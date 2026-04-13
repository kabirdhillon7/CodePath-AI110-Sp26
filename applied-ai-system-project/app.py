import streamlit as st
from pawpal_system import Pet, Task, Scheduler, save_state, load_state

try:
    from ai_advisor import suggest_tasks_for_pet, analyze_schedule, chat_with_advisor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session State ---
if "owner" not in st.session_state or not hasattr(st.session_state.owner, "to_dict"):
    st.session_state.owner = load_state()

owner = st.session_state.owner

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_main, tab_chat = st.tabs(["Schedule & Tasks", "AI Care Chat"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Schedule & Tasks
# ══════════════════════════════════════════════════════════════════════════════
with tab_main:

    # ── 1. Owner Info ──────────────────────────────────────────────────────────
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

    if owner.available_minutes == 0:
        st.warning("Available time is 0 — no tasks can be scheduled.")

    st.divider()

    # ── 2. Your Pets ───────────────────────────────────────────────────────────
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
        elif any(p.name.lower() == pet_name.strip().lower() for p in owner.pets):
            st.warning(f"A pet named '{pet_name.strip()}' already exists.")
        else:
            new_pet = Pet(name=pet_name.strip(), species=species, age=int(age), needs=[])
            owner.add_pet(new_pet)
            save_state(owner)
            st.success(f"Added {new_pet.name} the {new_pet.species}!")

    if owner.pets:
        for pet in list(owner.pets):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            col1.markdown(f"**{pet.name}**")
            col2.caption(f"{pet.species}, age {pet.age}")
            col3.caption(f"{len(pet.tasks)} task(s)")
            if col4.button("Remove", key=f"remove_pet_{id(pet)}"):
                owner.remove_pet(pet)
                save_state(owner)
                st.rerun()

        # ── AI Task Suggester ──────────────────────────────────────────────────
        if AI_AVAILABLE:
            st.markdown("---")
            st.markdown("**AI Task Suggestions**")
            ai_pet_name = st.selectbox(
                "Select a pet for AI suggestions",
                [p.name for p in owner.pets],
                key="ai_suggest_pet",
            )
            if st.button("Get AI Suggestions", key="ai_suggest_btn"):
                pet_obj = next(p for p in owner.pets if p.name == ai_pet_name)
                with st.spinner("Asking the AI care advisor..."):
                    suggestions = suggest_tasks_for_pet(pet_obj.name, pet_obj.species, pet_obj.age)
                st.session_state.ai_suggestions = suggestions
                st.session_state.ai_suggestions_pet = ai_pet_name

            if "ai_suggestions" in st.session_state:
                suggestions = st.session_state.ai_suggestions
                if suggestions == "QUOTA_EXHAUSTED":
                    st.warning(
                        "Gemini free-tier quota exhausted for today. "
                        "Quota resets at midnight Pacific Time. "
                        "Check usage at https://ai.dev/rate-limit"
                    )
                elif suggestions:
                    st.markdown(f"**Suggested tasks for {st.session_state.ai_suggestions_pet}:**")
                    selected_indices = []
                    for i, td in enumerate(suggestions):
                        checked = st.checkbox(
                            f"{td['description']} — {td['duration_minutes']} min "
                            f"[{td['priority']}, {td['frequency']}]",
                            key=f"ai_task_{i}",
                        )
                        if checked:
                            selected_indices.append(i)
                    if st.button("Add Selected Tasks", key="ai_add_tasks"):
                        pet_obj = next(
                            p for p in owner.pets
                            if p.name == st.session_state.ai_suggestions_pet
                        )
                        for i in selected_indices:
                            td = suggestions[i]
                            pet_obj.add_task(Task(**td))
                        save_state(owner)
                        del st.session_state.ai_suggestions
                        st.success(f"Added {len(selected_indices)} task(s)!")
                        st.rerun()
                else:
                    st.warning("AI could not generate suggestions. Check pawpal_ai.log for details.")

    else:
        st.info("No pets yet. Add one above.")

    st.divider()

    # ── 3. Add a Task ──────────────────────────────────────────────────────────
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
                save_state(owner)
                st.success(f"Added '{new_task.description}' to {selected_pet.name}.")
            else:
                st.warning("Please enter a task description.")

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
                        done = st.checkbox(
                            "Done", value=task.completed,
                            key=f"done_{id(task)}", label_visibility="collapsed"
                        )
                        if done != task.completed:
                            if done:
                                pet.complete_task(task)
                            else:
                                task.mark_incomplete()
                            save_state(owner)
                            st.rerun()
                    with col3:
                        if st.button("🗑", key=f"remove_task_{id(task)}"):
                            pet.remove_task(task)
                            save_state(owner)
                            st.rerun()

    st.divider()

    # ── 4. Today's Schedule ────────────────────────────────────────────────────
    st.subheader("Today's Schedule")

    if not owner.pets or not owner.get_all_tasks():
        st.info("Add at least one pet and one task to generate a schedule.")
    else:
        if st.button("Generate Schedule"):
            scheduler = Scheduler(owner)
            scheduled = scheduler.generate_schedule()
            st.session_state.last_schedule_ids = [id(t) for t in scheduled]
            st.session_state.last_schedule_budget = owner.available_minutes
            # Clear stale analysis when schedule is regenerated
            st.session_state.pop("ai_schedule_analysis", None)

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

            # ── AI Schedule Analyzer ───────────────────────────────────────────
            if AI_AVAILABLE and scheduled:
                st.divider()
                if st.button("Analyze Schedule with AI", key="ai_analyze_btn"):
                    with st.spinner("Analyzing your schedule..."):
                        analysis = analyze_schedule(owner, scheduled, excluded)
                    st.session_state.ai_schedule_analysis = analysis

                if "ai_schedule_analysis" in st.session_state:
                    analysis = st.session_state.ai_schedule_analysis
                    if analysis == "QUOTA_EXHAUSTED":
                        st.warning(
                            "Gemini free-tier quota exhausted for today. "
                            "Quota resets at midnight Pacific Time."
                        )
                    else:
                        st.markdown("**AI Care Advisor:**")
                        st.markdown(analysis)

            if excluded:
                with st.expander(f"Excluded tasks ({len(excluded)}) — didn't fit in time budget"):
                    for task in excluded:
                        st.markdown(
                            f"- **{task.description}** ({task.duration_minutes} min, {task.priority} priority)"
                        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AI Care Chat
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.subheader("Ask your AI Care Advisor")

    if not AI_AVAILABLE:
        st.error(
            "AI features are unavailable. Run `pip install google-generativeai python-dotenv` "
            "and set your GEMINI_API_KEY in a `.env` file."
        )
    elif not owner.pets:
        st.info("Add at least one pet first so the AI knows your situation.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Render existing conversation
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask about your pets' care...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = chat_with_advisor(owner, st.session_state.chat_history, user_input)
                if reply == "QUOTA_EXHAUSTED":
                    reply = (
                        "Gemini free-tier quota exhausted for today. "
                        "Quota resets at midnight Pacific Time. "
                        "Check usage at https://ai.dev/rate-limit"
                    )
                st.markdown(reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})
