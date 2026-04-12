from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---

owner = Owner(name="Kabir", available_minutes=90, preferences=["morning routines first"])

# Pet 1: Luna — tasks added out of order (long → short → medium)
luna = Pet(name="Luna", species="Dog", age=3, needs=["walk", "feeding", "grooming"])
luna.add_task(Task("Morning walk",     30, "high",   "daily",  "walk",     "Around the neighborhood"))
luna.add_task(Task("Brush coat",       20, "medium", "weekly", "grooming", "Focus on shedding areas"))
luna.add_task(Task("Breakfast feeding", 10, "high",  "daily",  "feeding",  "1 cup dry kibble"))

# Pet 2: Mochi — tasks added out of order (medium → long → short)
mochi = Pet(name="Mochi", species="Cat", age=2, needs=["feeding", "enrichment", "litter"])
mochi.add_task(Task("Clean litter box",   10, "medium", "daily", "litter",     ""))
mochi.add_task(Task("Enrichment puzzle",  15, "low",    "daily", "enrichment", "Hide treats in puzzle toy"))
mochi.add_task(Task("Wet food feeding",    5, "high",   "daily", "feeding",    "Half a can, morning"))

owner.add_pet(luna)
owner.add_pet(mochi)

# Mark one task complete so filters have something to show on each side
luna.tasks[0].mark_complete()   # Morning walk → done

scheduler = Scheduler(owner)

def section(title):
    print(f"\n{'─' * 45}")
    print(f"  {title}")
    print('─' * 45)

def task_row(t):
    status = "✓" if t.completed else "○"
    print(f"  {status}  {t.description:<25} {t.duration_minutes:>3} min  [{t.priority}]")

# ── 1. Sort by time (shortest → longest) ─────────────────────────────────────
section("sort_by_time()  —  shortest first")
for t in scheduler.sort_by_time():
    task_row(t)

# ── 2. Sort by time (longest → shortest) ─────────────────────────────────────
section("sort_by_time(reverse=True)  —  longest first")
for t in scheduler.sort_by_time(reverse=True):
    task_row(t)

# ── 3. Filter by status: incomplete ──────────────────────────────────────────
section("filter_by_status(completed=False)  —  pending tasks")
for t in scheduler.filter_by_status(completed=False):
    task_row(t)

# ── 4. Filter by status: complete ────────────────────────────────────────────
section("filter_by_status(completed=True)  —  done tasks")
for t in scheduler.filter_by_status(completed=True):
    task_row(t)

# ── 5. Filter by pet: Luna ────────────────────────────────────────────────────
section("filter_by_pet('Luna')  —  Luna's tasks only")
for t in scheduler.filter_by_pet("Luna"):
    task_row(t)

# ── 6. Filter by pet: Mochi ───────────────────────────────────────────────────
section("filter_by_pet('Mochi')  —  Mochi's tasks only")
for t in scheduler.filter_by_pet("Mochi"):
    task_row(t)

# ── 7. Today's full schedule ──────────────────────────────────────────────────
section("generate_schedule()  —  today's plan")
print(scheduler.explain_schedule())
