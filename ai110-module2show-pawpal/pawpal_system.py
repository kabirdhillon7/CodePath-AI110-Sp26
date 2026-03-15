from __future__ import annotations


class Pet:
    """Represents a pet with its characteristics and care needs."""

    def __init__(self, name: str, species: str, age: int, needs: list[str]) -> None:
        self.name = name
        self.species = species
        self.age = age
        self.needs = needs

    def get_needs(self) -> list[str]:
        pass


class Task:
    """Represents a single pet care task with duration and priority."""

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        category: str,
        notes: str,
    ) -> None:
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category
        self.notes = notes

    def is_high_priority(self) -> bool:
        pass


class Owner:
    """Represents the pet owner, including their time constraints and preferences."""

    def __init__(
        self, name: str, available_minutes: int, preferences: list[str]
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets: list[Pet] = []
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


class Scheduler:
    """Generates and explains a daily care plan based on the owner, pets, and tasks."""

    def __init__(self, owner: Owner, pets: list[Pet], tasks: list[Task]) -> None:
        self.owner = owner
        self.pets = pets
        self.tasks = tasks

    def generate_schedule(self) -> list[Task]:
        pass

    def explain_schedule(self) -> str:
        pass

    def filter_by_priority(self, level: str) -> list[Task]:
        pass

    def fits_in_time(self, tasks: list[Task]) -> bool:
        pass
