from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---

owner = Owner(name="Kabir", available_minutes=90, preferences=["morning routines first"])

# Pet 1: Luna (dog)
luna = Pet(name="Luna", species="Dog", age=3, needs=["walk", "feeding", "grooming"])
luna.add_task(Task("Morning walk", 30, "high", "daily", "walk", "Around the neighborhood"))
luna.add_task(Task("Breakfast feeding", 10, "high", "daily", "feeding", "1 cup dry kibble"))
luna.add_task(Task("Brush coat", 20, "medium", "weekly", "grooming", "Focus on shedding areas"))

# Pet 2: Mochi (cat)
mochi = Pet(name="Mochi", species="Cat", age=2, needs=["feeding", "enrichment", "litter"])
mochi.add_task(Task("Wet food feeding", 5, "high", "daily", "feeding", "Half a can, morning"))
mochi.add_task(Task("Enrichment puzzle", 15, "low", "daily", "enrichment", "Hide treats in puzzle toy"))
mochi.add_task(Task("Clean litter box", 10, "medium", "daily", "litter", ""))

owner.add_pet(luna)
owner.add_pet(mochi)

# --- Run Scheduler ---

scheduler = Scheduler(owner)

print("=" * 45)
print("        PawPal+ — Today's Schedule")
print("=" * 45)
print(scheduler.explain_schedule())
