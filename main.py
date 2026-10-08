from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from fastapi import Response
from dataclasses import asdict

from repository import TaskNotFoundError
from sqlite_repository import SqliteTaskRepository, init_db, get_db_connection

app = FastAPI()

repo = SqliteTaskRepository()


@app.on_event("startup")
def startup_event():
    init_db()


class TaskIn(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.exception_handler(TaskNotFoundError)
def task_not_found_handler(request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {exc.task_id} not found"},
    )


@app.get("/", description="Get API information")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", description="Check the health of the API")
def health():
    return {"status": "ok"}


@app.get("/tasks", description="Get all tasks")
def get_tasks():
    return [asdict(task) for task in repo.list_all()]


@app.get("/tasks/{task_id}", description="Get a task by ID")
def get_task(task_id: int):
    return asdict(repo.get_by_id(task_id))


# --- still on the old direct-sqlite path, to be migrated next ---

@app.post("/tasks", description="Create a new task")
def create_task(task: TaskIn):
    if not task.title:
        return JSONResponse(status_code=400, content={"error": "Title is missing"})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, int(task.done)),
    )
    new_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()
    return JSONResponse(
        status_code=201,
        content={"id": row["id"], "title": row["title"], "done": bool(row["done"])},
    )


@app.put("/tasks/{task_id}", description="Update a task by ID")
def update_task(task_id: int, task: TaskUpdate):
    if task.title is None and task.done is None:
        return JSONResponse(
            status_code=400, content={"error": "No valid fields provided to update"}
        )
    if task.title is not None and task.title == "":
        return JSONResponse(
            status_code=400, content={"error": "Title cannot be empty"}
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if cursor.fetchone() is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )

    fields, values = [], []
    if task.title is not None:
        fields.append("title = ?")
        values.append(task.title)
    if task.done is not None:
        fields.append("done = ?")
        values.append(int(task.done))
    cursor.execute(
        f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values + [task_id]
    )
    conn.commit()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.delete("/tasks/{task_id}", description="Delete a task by ID")
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )
    return Response(status_code=204)