import sqlite3
from abc import ABC, abstractmethod
from typing import Optional

from repository import Task, TaskNotFoundError


DB_PATH = "tasks.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy groceries", 0),
                ("Walk the dog", 0),
                ("Write code", 1),
            ],
        )

    conn.commit()
    conn.close()


def _row_to_task(row: sqlite3.Row) -> Task:
    """The only place SQLite's 0/1 for `done` becomes a Python bool."""
    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
    )


class SqliteTaskRepository:
    """SQLite-backed TaskRepository.

    Only list_all and get_by_id are implemented for now; the remaining
    three methods will be added in the next step, at which point this
    class will inherit from ABC and satisfy the full contract.
    """

    def list_all(self) -> list[Task]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks")
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int) -> Task:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            raise TaskNotFoundError(task_id)

        return _row_to_task(row)