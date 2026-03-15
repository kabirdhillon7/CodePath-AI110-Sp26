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
