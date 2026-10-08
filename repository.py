from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    done: bool


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


class TaskRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Task]:
        """Return all tasks as a list."""

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task:
        """Return a task or raise TaskNotFoundError."""

    @abstractmethod
    def create(self, title: str, done: bool = False) -> Task:
        """Insert and return a task."""

    @abstractmethod
    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        done: Optional[bool] = None,
    ) -> Task:
        """Update provided fields and return the task."""

    @abstractmethod
    def delete(self, task_id: int) -> None:
        """Delete a task or raise TaskNotFoundError."""
