from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from dataclasses import asdict

from repository import TaskNotFoundError
from postgres_repository import PostgresTaskRepository, init_db

app = FastAPI()

repo = PostgresTaskRepository()


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


@app.post("/tasks", description="Create a new task")
def create_task(task: TaskIn):
    if not task.title:
        return JSONResponse(status_code=400, content={"error": "Title is missing"})

    return JSONResponse(
        status_code=201,
        content=asdict(repo.create(task.title, task.done)),
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

    return asdict(repo.update(task_id, task.title, task.done))


@app.delete("/tasks/{task_id}", description="Delete a task by ID")
def delete_task(task_id: int):
    repo.delete(task_id)
    return Response(status_code=204)