from datetime import date, timedelta

from pawpal_system import Pet, Task, Owner, Scheduler


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


# --- Task: is_high_priority / mark_incomplete ---

def test_is_high_priority_true_and_false():
    assert make_task(priority="high").is_high_priority() is True
    assert make_task(priority="medium").is_high_priority() is False


def test_mark_incomplete_resets_status():
    task = make_task()
    task.mark_complete()
    task.mark_incomplete()
    assert task.completed is False


# --- Pet: remove_task ---

def test_remove_task_decreases_count():
    pet = Pet(name="Luna", species="Dog", age=3, needs=[])
    task = make_task()
    pet.add_task(task)
    pet.remove_task(task)
    assert len(pet.get_tasks()) == 0


# --- Scheduler helpers ---

def make_scheduled_owner(*tasks, budget=60):
    owner = Owner(name="Test", available_minutes=budget, preferences=[])
    pet = Pet(name="Luna", species="Dog", age=3, needs=[])
    for t in tasks:
        pet.add_task(t)
    owner.add_pet(pet)
    return owner


# --- Scheduler: generate_schedule ---

def test_scheduler_excludes_completed_tasks():
    task = make_task()
    task.mark_complete()
    owner = make_scheduled_owner(task)
    assert Scheduler(owner).generate_schedule() == []


def test_scheduler_zero_budget_returns_empty():
    owner = make_scheduled_owner(make_task(), budget=0)
    assert Scheduler(owner).generate_schedule() == []


# --- Scheduler: sort_by_time ---

def test_scheduler_sort_by_time_ascending():
    long_task = make_task(duration_minutes=30)
    short_task = make_task(duration_minutes=5)
    owner = make_scheduled_owner(long_task, short_task)  # added out of order
    result = Scheduler(owner).sort_by_time()
    assert result[0].duration_minutes == 5
    assert result[-1].duration_minutes == 30
