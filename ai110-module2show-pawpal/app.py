import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session State ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=60, preferences=[])

owner = st.session_state.owner

# ── 1. Owner Info ────────────────────────────────────────────────────────────
st.subheader("Owner Info")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value=owner.name)
    owner.name = owner_name
with col2:
    avail = st.number_input(
        "Time available today (minutes)", min_value=0, max_value=1440, value=owner.available_minutes
    )
    owner.available_minutes = int(avail)

st.divider()

# ── 2. Add a Pet ─────────────────────────────────────────────────────────────
st.subheader("Your Pets")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
    submitted = st.form_submit_button("Add Pet")

if submitted:
    if pet_name.strip():
        new_pet = Pet(name=pet_name.strip(), species=species, age=int(age), needs=[])
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.name} the {new_pet.species}!")
    else:
        st.warning("Please enter a pet name.")

if owner.pets:
    pets_data = [
        {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
        for p in owner.pets
    ]
    st.table(pets_data)
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── 3. Add a Task ─────────────────────────────────────────────────────────────
st.subheader("Add a Task")

if not owner.pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Assign to pet", pet_names)

        col1, col2 = st.columns(2)
        with col1:
            description = st.text_input("Task description", value="Morning walk")
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            category = st.selectbox(
                "Category", ["walk", "feeding", "grooming", "enrichment", "meds", "other"]
            )
            notes = st.text_input("Notes (optional)", value="")

        task_submitted = st.form_submit_button("Add Task")

    if task_submitted:
        if description.strip():
            selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)
            new_task = Task(
                description=description.strip(),
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
                category=category,
                notes=notes.strip(),
            )
            selected_pet.add_task(new_task)
            st.success(f"Added '{new_task.description}' to {selected_pet.name}.")
        else:
            st.warning("Please enter a task description.")

    # Show each pet's current tasks
    for pet in owner.pets:
        with st.expander(f"{pet.name}'s tasks ({len(pet.tasks)})"):
            if pet.tasks:
                tasks_data = [
                    {
                        "Description": t.description,
                        "Minutes": t.duration_minutes,
                        "Priority": t.priority,
                        "Frequency": t.frequency,
                        "Done": t.completed,
                    }
                    for t in pet.tasks
                ]
                st.table(tasks_data)
            else:
                st.caption("No tasks yet.")

st.divider()

# ── 4. Generate Schedule ──────────────────────────────────────────────────────
st.subheader("Today's Schedule")

if not owner.pets or not owner.get_all_tasks():
    st.info("Add at least one pet and one task to generate a schedule.")
else:
    if st.button("Generate Schedule"):
        scheduler = Scheduler(owner)
        # result = scheduler.explain_schedule()
        # st.text(result)
        scheduled = scheduler.generate_schedule()
        all_incomplete = scheduler.get_incomplete_tasks()
        excluded = [t for t in all_incomplete if id(t) not in {id(s) for s in scheduled}]
        time_used = sum(t.duration_minutes for t in scheduled)
        time_remaining = owner.available_minutes - time_used

        # Time summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Tasks Scheduled", len(scheduled))
        col2.metric("Time Used", f"{time_used} min")
        col3.metric("Time Remaining", f"{time_remaining} min")

        st.divider()

        # Scheduled tasks
        if not scheduled:
            st.warning("No tasks fit within the available time budget.")
        else:
            priority_style = {
                "high":   ("🔴", st.error),
                "medium": ("🟡", st.warning),
                "low":    ("🟢", st.info),
            }
            for task in scheduled:
                emoji, container = priority_style.get(task.priority, ("🟢", st.info))
                with container(f"**{emoji} {task.description}**  ·  {task.duration_minutes} min  ·  {task.frequency}", icon=None):
                    if task.notes:
                        st.caption(task.notes)

        # Excluded tasks
        if excluded:
            with st.expander(f"Excluded tasks ({len(excluded)}) — didn't fit in time budget"):
                for task in excluded:
                    st.markdown(f"- **{task.description}** ({task.duration_minutes} min, {task.priority} priority)")
