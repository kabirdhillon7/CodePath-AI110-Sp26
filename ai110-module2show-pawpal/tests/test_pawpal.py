from datetime import date, timedelta

from pawpal_system import Pet, Task


def make_task(**kwargs):
    defaults = dict(
        description="Test task",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        category="general",
        notes="",
    )
    defaults.update(kwargs)
    return Task(**defaults)


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Luna", species="Dog", age=3, needs=[])
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task())
    assert len(pet.get_tasks()) == 1


# --- next_occurrence() ---

def test_next_occurrence_daily():
    task = make_task(frequency="daily")
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == date.today() + timedelta(days=1)
    assert nxt.completed is False


def test_next_occurrence_weekly():
    task = make_task(frequency="weekly")
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == date.today() + timedelta(days=7)
    assert nxt.completed is False


def test_next_occurrence_as_needed_returns_none():
    task = make_task(frequency="as_needed")
    assert task.next_occurrence() is None


def test_next_occurrence_does_not_copy_last_completed_date():
    task = make_task(frequency="daily")
    task.mark_complete()
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.last_completed_date is None


# --- Pet.complete_task() ---

def test_pet_complete_task_adds_next_occurrence():
    pet = Pet(name="Luna", species="Dog", age=3, needs=[])
    task = make_task(frequency="daily")
    pet.add_task(task)
    pet.complete_task(task)
    assert len(pet.get_tasks()) == 2
    assert pet.get_tasks()[0].completed is True
    assert pet.get_tasks()[1].completed is False


def test_pet_complete_task_as_needed_no_new_task():
    pet = Pet(name="Luna", species="Dog", age=3, needs=[])
    task = make_task(frequency="as_needed")
    pet.add_task(task)
    pet.complete_task(task)
    assert len(pet.get_tasks()) == 1


# --- Serialization ---

def test_due_date_roundtrips_serialization():
    tomorrow = date.today() + timedelta(days=1)
    task = make_task(due_date=tomorrow)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == tomorrow


def test_from_dict_without_due_date_key_is_none():
    task = make_task()
    d = task.to_dict()
    del d["due_date"]  # simulate old JSON without the key
    restored = Task.from_dict(d)
    assert restored.due_date is None


# --- should_schedule_today() ---

def test_should_schedule_today_with_future_due_date():
    task = make_task(due_date=date.today() + timedelta(days=1))
    assert task.should_schedule_today() is False


def test_should_schedule_today_with_todays_due_date():
    task = make_task(due_date=date.today())
    assert task.should_schedule_today() is True


def test_should_schedule_today_with_past_due_date():
    task = make_task(due_date=date.today() - timedelta(days=1))
    assert task.should_schedule_today() is True
