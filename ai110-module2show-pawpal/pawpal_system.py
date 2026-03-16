from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

PRIORITY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
STATE_FILE = Path("pawpal_state.json")


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
        due_date: date | None = None,
    ) -> None:
        self.description = description
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.frequency = frequency      # "daily", "weekly", "as_needed"
        self.category = category
        self.notes = notes
        self.completed = completed
        self.last_completed_date: date | None = None
        self.due_date: date | None = due_date  # when this occurrence is next due

    # --- Fix 1: frequency-aware scheduling ---

    def should_schedule_today(self) -> bool:
        """Return True if this task is due to appear in today's schedule."""
        if self.due_date is not None:
            return self.due_date <= date.today()
        # Fallback for legacy tasks that predate due_date
        if self.frequency in ("daily", "as_needed"):
            return True
        if self.frequency == "weekly":
            if self.last_completed_date is None:
                return True
            return (date.today() - self.last_completed_date).days >= 7
        return True

    def next_occurrence(self) -> Task | None:
        """Return a fresh, incomplete copy of this task due on its next occurrence.

        Returns None for 'as_needed' tasks (no predictable cadence).
        timedelta(days=1) advances by exactly one day; timedelta(days=7) by one week.
        """
        if self.frequency == "daily":
            next_due = date.today() + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = date.today() + timedelta(days=7)
        else:  # "as_needed"
            return None
        return Task(
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            category=self.category,
            notes=self.notes,
            completed=False,
            due_date=next_due,
        )

    def is_high_priority(self) -> bool:
        return _normalize_priority(self.priority) == "high"

    def mark_complete(self) -> None:
        self.completed = True
        self.last_completed_date = date.today()  # Fix 1: record completion date

    def mark_incomplete(self) -> None:
        self.completed = False

    # --- Fix 2: serialization ---

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "frequency": self.frequency,
            "category": self.category,
            "notes": self.notes,
            "completed": self.completed,
            "last_completed_date": (
                self.last_completed_date.isoformat() if self.last_completed_date else None
            ),
            "due_date": (
                self.due_date.isoformat() if self.due_date else None
            ),
        }

    @classmethod
    def from_dict(cls, d: dict) -> Task:
        t = cls(
            d["description"], d["duration_minutes"], d["priority"],
            d["frequency"], d["category"], d["notes"], d.get("completed", False),
        )
        if d.get("last_completed_date"):
            t.last_completed_date = date.fromisoformat(d["last_completed_date"])
        if d.get("due_date"):
            t.due_date = date.fromisoformat(d["due_date"])
        return t


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

    def complete_task(self, task: Task) -> None:
        """Mark task complete and append the next occurrence if it recurs."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.add_task(next_task)

    # --- Fix 2: serialization ---

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "needs": self.needs,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Pet:
        pet = cls(d["name"], d["species"], d["age"], d.get("needs", []))
        for task_data in d.get("tasks", []):
            pet.tasks.append(Task.from_dict(task_data))
        return pet


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

    # --- Fix 2: serialization ---

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "preferences": self.preferences,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Owner:
        owner = cls(d["name"], d["available_minutes"], d.get("preferences", []))
        for pet_data in d.get("pets", []):
            owner.pets.append(Pet.from_dict(pet_data))
        return owner


# --- Fix 2: save / load helpers ---

def save_state(owner: Owner) -> None:
    """Persist the full owner → pets → tasks tree to disk."""
    STATE_FILE.write_text(json.dumps(owner.to_dict(), indent=2))


def load_state() -> Owner:
    """Load persisted state from disk, or return a blank Owner if none exists."""
    if STATE_FILE.exists():
        try:
            return Owner.from_dict(json.loads(STATE_FILE.read_text()))
        except Exception:
            pass
    return Owner(name="", available_minutes=60, preferences=[])


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

    def sort_by_time(self, reverse: bool = False) -> list[Task]:
        """Return all tasks sorted by duration_minutes. Shortest first by default."""
        return sorted(self._get_all_tasks(), key=lambda t: t.duration_minutes, reverse=reverse)

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self._get_all_tasks() if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to the named pet (case-insensitive)."""
        return [
            task
            for pet in self.owner.pets
            if pet.name.lower() == pet_name.lower()
            for task in pet.tasks
        ]

    def get_incomplete_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been marked complete."""
        return self.filter_by_status(completed=False)

    def generate_schedule(self) -> list[Task]:
        budget = self.owner.available_minutes
        if budget <= 0:
            return []

        # Fix 1: only consider tasks that are due today
        sort_key = lambda t: (
            PRIORITY_RANK.get(_normalize_priority(t.priority), 2),
            t.duration_minutes,
        )
        all_candidates = sorted(
            [t for t in self._get_all_tasks()
             if not t.completed and t.should_schedule_today()],
            key=sort_key,
        )

        scheduled: list[Task] = []
        scheduled_ids: set[int] = set()
        time_used = 0

        # Fix 3, Phase 1: guarantee at least one task per pet
        for pet in self.owner.pets:
            pet_candidates = [
                t for t in pet.tasks
                if not t.completed and t.should_schedule_today()
            ]
            if not pet_candidates:
                continue
            best = min(pet_candidates, key=sort_key)
            if time_used + best.duration_minutes <= budget:
                scheduled.append(best)
                scheduled_ids.add(id(best))
                time_used += best.duration_minutes

        # Fix 3, Phase 2: greedy fill remaining time with leftover tasks
        for task in all_candidates:
            if id(task) in scheduled_ids:
                continue
            if time_used + task.duration_minutes <= budget:
                scheduled.append(task)
                scheduled_ids.add(id(task))
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
