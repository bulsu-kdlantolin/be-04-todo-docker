from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from fastapi import Response
import sqlite3

app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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
            ]
        )

    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

tasks = [
    {
        "id": 1, 
        "title": "Task 1", 
        "done": False
    },
    {
        "id": 2, 
        "title": "Task 2",
        "done": True
    },
    {
        "id": 3, 
        "title": "Task 3",
        "done": False
    }
]

class Task(BaseModel):
    title: str 
    done: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/", description="Get API information")
def home():
    return { 
        "name": "Task API", 
        "version": "1.0", 
        "endpoints": ["/tasks"] 
    }

@app.get("/health", description="Check the health of the API")
def health():
    return {
        "status": "ok"
    }

@app.get("/tasks", description="Get all tasks")
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
        for row in rows
    ]

@app.get("/tasks/{task_id}", description="Get a task by ID")
def get_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }

@app.post("/tasks", description="Create a new task")
def create_task(task: Task):
    if not task.title:
        return JSONResponse(
            status_code=400,
            content={"error": "Title is missing"}
        )

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
        content={
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
        },
    )

@app.put("/tasks/{task_id}", description="Update a task by ID")
def update_task(task_id: int, task: TaskUpdate):
    # Same validation order as BE-01
    if task.title is None and task.done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "No valid fields provided to update"}
        )
    if task.title is not None and task.title == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if cursor.fetchone() is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    fields = []
    values = []
    if task.title is not None:
        fields.append("title = ?")
        values.append(task.title)
    if task.done is not None:
        fields.append("done = ?")
        values.append(int(task.done))

    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    values.append(task_id)
    cursor.execute(sql, values)
    conn.commit()

    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


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
            content={"error": f"Task {task_id} not found"}
        )

    return Response(status_code=204)