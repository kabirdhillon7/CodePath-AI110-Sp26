import streamlit as st
from pawpal_system import Pet, Task, Scheduler, save_state, load_state

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session State (Fix 2: load from disk on first run) ---
if "owner" not in st.session_state or not hasattr(st.session_state.owner, "to_dict"):
    st.session_state.owner = load_state()

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

# Fix 4: warn when budget is 0
if owner.available_minutes == 0:
    st.warning("Available time is 0 — no tasks can be scheduled.")

st.divider()

# ── 2. Your Pets ──────────────────────────────────────────────────────────────
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
    if not pet_name.strip():
        st.warning("Please enter a pet name.")
    # Fix 7: duplicate pet check
    elif any(p.name.lower() == pet_name.strip().lower() for p in owner.pets):
        st.warning(f"A pet named '{pet_name.strip()}' already exists.")
    else:
        new_pet = Pet(name=pet_name.strip(), species=species, age=int(age), needs=[])
        owner.add_pet(new_pet)
        save_state(owner)  # Fix 2
        st.success(f"Added {new_pet.name} the {new_pet.species}!")

# Fix 6: per-pet rows with Remove button instead of st.table
if owner.pets:
    for pet in list(owner.pets):  # copy so removal mid-loop is safe
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        col1.markdown(f"**{pet.name}**")
        col2.caption(f"{pet.species}, age {pet.age}")
        col3.caption(f"{len(pet.tasks)} task(s)")
        if col4.button("Remove", key=f"remove_pet_{id(pet)}"):
            owner.remove_pet(pet)
            save_state(owner)  # Fix 2
            st.rerun()
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
            save_state(owner)  # Fix 2
            st.success(f"Added '{new_task.description}' to {selected_pet.name}.")
        else:
            st.warning("Please enter a task description.")

    # Fix 5 & 6: per-task rows with checkbox (mark complete) and remove button
    for pet in owner.pets:
        with st.expander(f"{pet.name}'s tasks ({len(pet.tasks)})"):
            if not pet.tasks:
                st.caption("No tasks yet.")
            for task in list(pet.tasks):
                col1, col2, col3 = st.columns([5, 1, 1])
                with col1:
                    label = f"~~{task.description}~~" if task.completed else task.description
                    st.markdown(
                        f"**{label}** · {task.duration_minutes} min · "
                        f"`{task.priority}` · {task.frequency}"
                    )
                    if task.notes:
                        st.caption(task.notes)
                with col2:
                    # Fix 5: completion checkbox
                    done = st.checkbox(
                        "Done", value=task.completed,
                        key=f"done_{id(task)}", label_visibility="collapsed"
                    )
                    if done != task.completed:
                        task.mark_complete() if done else task.mark_incomplete()
                        save_state(owner)  # Fix 2
                        st.rerun()
                with col3:
                    # Fix 6: remove task button
                    if st.button("🗑", key=f"remove_task_{id(task)}"):
                        pet.remove_task(task)
                        save_state(owner)  # Fix 2
                        st.rerun()

st.divider()

# ── 4. Generate Schedule ──────────────────────────────────────────────────────
st.subheader("Today's Schedule")

if not owner.pets or not owner.get_all_tasks():
    st.info("Add at least one pet and one task to generate a schedule.")
else:
    # Fix 8: button only triggers the computation; rendering is driven by session state
    if st.button("Generate Schedule"):
        scheduler = Scheduler(owner)
        scheduled = scheduler.generate_schedule()
        st.session_state.last_schedule_ids = [id(t) for t in scheduled]
        st.session_state.last_schedule_budget = owner.available_minutes

    # Fix 8: render from session state so it survives reruns
    if "last_schedule_ids" in st.session_state:
        id_set = set(st.session_state.last_schedule_ids)
        scheduled = [t for t in owner.get_all_tasks() if id(t) in id_set]
        all_incomplete = [t for t in owner.get_all_tasks() if not t.completed]
        excluded = [t for t in all_incomplete if id(t) not in id_set]
        time_used = sum(t.duration_minutes for t in scheduled)
        time_remaining = st.session_state.last_schedule_budget - time_used

        col1, col2, col3 = st.columns(3)
        col1.metric("Tasks Scheduled", len(scheduled))
        col2.metric("Time Used", f"{time_used} min")
        col3.metric("Time Remaining", f"{time_remaining} min")

        st.divider()

        priority_style = {
            "high":   ("🔴", st.error),
            "medium": ("🟡", st.warning),
            "low":    ("🟢", st.info),
        }

        if not scheduled:
            st.warning("No tasks fit within the available time budget.")
        else:
            for task in scheduled:
                emoji, container = priority_style.get(task.priority, ("🟢", st.info))
                with container(
                    f"**{emoji} {task.description}**  ·  {task.duration_minutes} min  ·  {task.frequency}",
                    icon=None,
                ):
                    if task.notes:
                        st.caption(task.notes)

        if excluded:
            with st.expander(f"Excluded tasks ({len(excluded)}) — didn't fit in time budget"):
                for task in excluded:
                    st.markdown(
                        f"- **{task.description}** ({task.duration_minutes} min, {task.priority} priority)"
                    )
