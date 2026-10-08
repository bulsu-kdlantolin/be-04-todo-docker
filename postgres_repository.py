import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

from repository import Task, TaskNotFoundError, TaskRepository


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_db_connection() -> psycopg.Connection[dict[str, Any]]:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    with get_db_connection() as connection:
        connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


def _row_to_task(row: dict[str, Any]) -> Task:
    return Task(id=row["id"], title=row["title"], done=row["done"])


class PostgresTaskRepository(TaskRepository):
    def list_all(self) -> list[Task]:
        with get_db_connection() as connection:
            rows = connection.execute(
                "SELECT id, title, done FROM tasks ORDER BY id"
            ).fetchall()
        return [_row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int) -> Task:
        with get_db_connection() as connection:
            row = connection.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
            ).fetchone()
        if row is None:
            raise TaskNotFoundError(task_id)
        return _row_to_task(row)

    def create(self, title: str, done: bool = False) -> Task:
        with get_db_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done
                """,
                (title, done),
            ).fetchone()
        return _row_to_task(row)

    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        done: Optional[bool] = None,
    ) -> Task:
        fields: list[str] = []
        values: list[Any] = []
        if title is not None:
            fields.append("title = %s")
            values.append(title)
        if done is not None:
            fields.append("done = %s")
            values.append(done)

        with get_db_connection() as connection:
            if not fields:
                row = connection.execute(
                    "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
                ).fetchone()
            else:
                values.append(task_id)
                row = connection.execute(
                    f"""
                    UPDATE tasks
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING id, title, done
                    """,
                    values,
                ).fetchone()
        if row is None:
            raise TaskNotFoundError(task_id)
        return _row_to_task(row)

    def delete(self, task_id: int) -> None:
        with get_db_connection() as connection:
            result = connection.execute(
                "DELETE FROM tasks WHERE id = %s", (task_id,)
            )
        if result.rowcount == 0:
            raise TaskNotFoundError(task_id)
