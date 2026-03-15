from __future__ import annotations

PRIORITY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


def _normalize_priority(priority: str) -> str:
    """Return priority if valid ('high'/'medium'/'low'), otherwise 'low'."""
    return priority if priority in PRIORITY_RANK else "low"


class Task:
    """Represents a single activity with a description, time, frequency, and completion status."""

    def __init__(
        self,
        description: str,
        duration_minutes: int,
        priority: str,
        frequency: str,
        category: str,
        notes: str,
        completed: bool = False,
    ) -> None:
        self.description = description
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.frequency = frequency      # e.g. "daily", "weekly", "as_needed"
        self.category = category
        self.notes = notes
        self.completed = completed

    def is_high_priority(self) -> bool:
        return _normalize_priority(self.priority) == "high"

    def mark_complete(self) -> None:
        self.completed = True

    def mark_incomplete(self) -> None:
        self.completed = False


class Pet:
    """Stores pet details and a list of tasks assigned to that pet."""

    def __init__(self, name: str, species: str, age: int, needs: list[str]) -> None:
        self.name = name
        self.species = species
        self.age = age
        self.needs = needs
        self.tasks: list[Task] = []

    def get_needs(self) -> list[str]:
        return list(self.needs)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        return list(self.tasks)


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(
        self, name: str, available_minutes: int, preferences: list[str]
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        if pet in self.pets:
            self.pets.remove(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of all tasks across every pet."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of the owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def _get_all_tasks(self) -> list[Task]:
        """Flatten tasks from all pets, deduplicated by object identity."""
        seen_ids: set[int] = set()
        unique: list[Task] = []
        for task in self.owner.get_all_tasks():
            if id(task) not in seen_ids:
                seen_ids.add(id(task))
                unique.append(task)
        return unique

    def fits_in_time(self, tasks: list[Task]) -> bool:
        if self.owner.available_minutes <= 0:
            return len(tasks) == 0
        return sum(t.duration_minutes for t in tasks) <= self.owner.available_minutes

    def filter_by_priority(self, level: str) -> list[Task]:
        normalized_level = _normalize_priority(level)
        return [
            t for t in self._get_all_tasks()
            if _normalize_priority(t.priority) == normalized_level
        ]

    def get_incomplete_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been marked complete."""
        return [t for t in self._get_all_tasks() if not t.completed]

    def generate_schedule(self) -> list[Task]:
        if self.owner.available_minutes <= 0:
            return []

        # Only schedule incomplete tasks; sort by priority then duration (greedy fit)
        candidates = sorted(
            self.get_incomplete_tasks(),
            key=lambda t: (
                PRIORITY_RANK.get(_normalize_priority(t.priority), 2),
                t.duration_minutes,
            ),
        )

        scheduled: list[Task] = []
        time_used = 0
        for task in candidates:
            if time_used + task.duration_minutes <= self.owner.available_minutes:
                scheduled.append(task)
                time_used += task.duration_minutes

        return scheduled

    def explain_schedule(self) -> str:
        budget = self.owner.available_minutes

        if budget <= 0:
            return (
                f"No schedule generated for {self.owner.name}: "
                f"available time is {budget} minutes (must be > 0)."
            )

        scheduled = self.generate_schedule()
        time_used = sum(t.duration_minutes for t in scheduled)
        time_remaining = budget - time_used

        scheduled_ids = {id(t) for t in scheduled}
        all_incomplete = self.get_incomplete_tasks()
        excluded = [t for t in all_incomplete if id(t) not in scheduled_ids]

        lines: list[str] = []
        lines.append(f"Schedule for {self.owner.name} ({budget} min available)")
        lines.append("=" * 45)

        if not scheduled:
            lines.append("No tasks could be scheduled.")
            lines.append(
                f"  Reason: all {len(all_incomplete)} incomplete task(s) exceed the available time budget."
            )
        else:
            lines.append(
                f"Scheduled ({len(scheduled)} task(s), "
                f"{time_used} min used, {time_remaining} min remaining):"
            )
            for task in scheduled:
                label = _normalize_priority(task.priority).upper()
                lines.append(
                    f"  - [{label}] {task.description} ({task.duration_minutes} min, {task.frequency})"
                )
                if task.notes:
                    lines.append(f"      Note: {task.notes}")

        if excluded:
            lines.append("")
            lines.append(f"Excluded ({len(excluded)} task(s)):")
            for task in excluded:
                label = _normalize_priority(task.priority).upper()
                lines.append(
                    f"  - [{label}] {task.description} ({task.duration_minutes} min)"
                    f"  -- not enough time remaining"
                )
        else:
            lines.append("")
            lines.append("All incomplete tasks fit within the available time.")

        return "\n".join(lines)
