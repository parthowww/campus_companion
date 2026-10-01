"""
Campus Companion - Assignment Deadlines & Submission Tracker
Track project deliverables, laboratory reports, deadlines with countdown urgency,
submit assignments with notes, and record grades.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="Assignments Tracker - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title(" Assignment Deadlines & Submissions")
st.caption("Centralized assignment manager with submission tracking, deadline urgency, and grading history.")

current_date_str = datetime.now().strftime("%Y-%m-%d")
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")

# Fetch Assignments & Subjects
assign_query = """
SELECT 
    a.id, a.subject_id, a.title, a.description, a.due_date, a.max_marks,
    a.status, a.marks_obtained, a.submission_notes,
    s.code AS subject_code, s.name AS subject_name, s.color_code
FROM assignments a
JOIN subjects s ON a.subject_id = s.id
ORDER BY 
    CASE a.status 
        WHEN 'Pending' THEN 1
        WHEN 'In Progress' THEN 2
        WHEN 'Submitted' THEN 3
        ELSE 4
    END,
    a.due_date ASC;
"""
assign_df = pd.read_sql_query(assign_query, conn)
assign_df["due_obj"] = pd.to_datetime(assign_df["due_date"])
assign_df["days_left"] = (assign_df["due_obj"] - today_dt).dt.days

# KPI Metrics Bar
total_tasks = len(assign_df)
pending_tasks = len(assign_df[assign_df["status"] == "Pending"])
in_progress_tasks = len(assign_df[assign_df["status"] == "In Progress"])
submitted_tasks = len(assign_df[assign_df["status"] == "Submitted"])
graded_tasks = len(assign_df[assign_df["status"] == "Graded"])

a1, a2, a3 = st.columns(3)
st.write('')
a4, a5, _ = st.columns(3)
with a1:
    st.metric("Total Courseworks", total_tasks)
with a2:
    st.metric("Pending", pending_tasks, delta="Not started", delta_color="inverse" if pending_tasks > 0 else "normal")
with a3:
    st.metric("In Progress", in_progress_tasks, delta="Active work", delta_color="off")
with a4:
    st.metric("Submitted", submitted_tasks, delta="Awaiting marks")
with a5:
    st.metric("Graded", graded_tasks, delta="Finalized")

st.divider()

tab_tasks, tab_submit, tab_analytics, tab_new = st.tabs([
    " Assignment Board",
    " Update Status & Submit",
    " Performance Analytics",
    "➕ Add New Assignment"
])

# --- TAB 1: ASSIGNMENT BOARD ---
with tab_tasks:
    st.subheader("Actionable Assignments")
    
    col_stat, col_sub = st.columns([1, 1])
    with col_stat:
        status_filter = st.selectbox(
            "Filter by Status:",
            ["All Assignments", "Action Required (Pending & In Progress)", "Pending", "In Progress", "Submitted", "Graded"]
        )
    with col_sub:
        subjects_list = ["All Subjects"] + sorted(assign_df["subject_code"].unique().tolist())
        sub_filter = st.selectbox("Filter by Course:", subjects_list)

    filtered_tasks = assign_df.copy()
    if status_filter == "Action Required (Pending & In Progress)":
        filtered_tasks = filtered_tasks[filtered_tasks["status"].isin(["Pending", "In Progress"])]
    elif status_filter != "All Assignments":
        filtered_tasks = filtered_tasks[filtered_tasks["status"] == status_filter]

    if sub_filter != "All Subjects":
        filtered_tasks = filtered_tasks[filtered_tasks["subject_code"] == sub_filter]

    if filtered_tasks.empty:
        st.info(" No assignments found matching this filter.")
    else:
        for _, task in filtered_tasks.iterrows():
            with st.container(border=True):
                c_details, c_urgency = st.columns([3, 1], gap="medium")
                with c_details:
                    st.markdown(f"### {task['title']}")
                    st.caption(f" Course: **{task['subject_code']} - {task['subject_name']}** | Max Marks: **{task['max_marks']}**")
                    st.write(task['description'] or "No additional description.")
                    if task['submission_notes']:
                        st.caption(f" **Submission Notes:** {task['submission_notes']}")

                with c_urgency:
                    st.markdown(f"️ **Due: {task['due_date']}**")
                    
                    # Urgency indicator
                    if task['status'] in ['Pending', 'In Progress']:
                        if task['days_left'] < 0:
                            st.error(f" Overdue by {abs(task['days_left'])} days!")
                        elif task['days_left'] <= 2:
                            st.warning(f"⚠️ Urgent: Due in {task['days_left']} days!")
                        else:
                            st.info(f" {task['days_left']} days left")
                    
                    # Status Badge
                    if task['status'] == "Pending":
                        st.caption("Status:  **Pending**")
                    elif task['status'] == "In Progress":
                        st.caption("Status:  **In Progress**")
                    elif task['status'] == "Submitted":
                        st.caption("Status:  **Submitted**")
                    else:
                        st.caption("Status:  **Graded**")
                        if task['marks_obtained'] is not None:
                            st.success(f"Score: **{task['marks_obtained']}** / {task['max_marks']}")

# --- TAB 2: UPDATE STATUS & SUBMIT ---
with tab_submit:
    st.subheader(" Turn in Deliverable or Update Status")
    st.write("Record your progress or submit assignment deliverables.")

    task_options = {
        f"#{r['id']} [{r['subject_code']}] {r['title']} (Current: {r['status']})": r['id']
        for _, r in assign_df.iterrows()
    }
    
    if task_options:
        sel_task_label = st.selectbox("Select Assignment to Update:", list(task_options.keys()))
        selected_task_id = task_options[sel_task_label]
        target_task = assign_df[assign_df["id"] == selected_task_id].iloc[0]

        with st.form("submit_assignment_form"):
            st.markdown(f"#### Updating: {target_task['title']}")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                new_stat = st.selectbox(
                    "Update Status to:",
                    ["Pending", "In Progress", "Submitted", "Graded"],
                    index=["Pending", "In Progress", "Submitted", "Graded"].index(target_task["status"])
                )
            with c_s2:
                marks_input = st.number_input(
                    f"Marks Obtained (Max {target_task['max_marks']}):",
                    min_value=0.0,
                    max_value=float(target_task['max_marks']),
                    value=float(target_task['marks_obtained']) if target_task['marks_obtained'] is not None else 0.0
                )

            notes_input = st.text_area(
                "Submission Notes / Link / Repository URL:",
                value=target_task["submission_notes"] or "",
                placeholder="e.g. Uploaded to LMS, GitHub: https://github.com/student/tsp-solver"
            )

            submit_update = st.form_submit_button("Save Assignment Progress")
            if submit_update:
                cursor = conn.cursor()
                final_marks = marks_input if new_stat == "Graded" else target_task["marks_obtained"]
                cursor.execute("""
                UPDATE assignments 
                SET status = ?, marks_obtained = ?, submission_notes = ?
                WHERE id = ?;
                """, (new_stat, final_marks, notes_input, selected_task_id))
                conn.commit()
                st.success("Assignment updated successfully!")
                st.rerun()

        st.write("")
        with st.expander("️ Delete Selected Assignment"):
            st.warning(f"Permanently remove '{target_task['title']}'?")
            if st.button("Confirm Delete Assignment", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM assignments WHERE id = ?;", (selected_task_id,))
                conn.commit()
                st.warning("Assignment deleted successfully!")
                st.rerun()
    else:
        st.info("No assignments available to update.")

# --- TAB 3: PERFORMANCE ANALYTICS ---
with tab_analytics:
    st.subheader("Performance & Grading Distribution")
    graded_df = assign_df[assign_df["status"] == "Graded"]
    
    if not graded_df.empty:
        graded_df["percentage_score"] = (graded_df["marks_obtained"] / graded_df["max_marks"]) * 100
        
        c_an1, c_an2 = st.columns([1, 1])
        with c_an1:
            avg_score = graded_df["percentage_score"].mean()
            st.metric("Average Score Across Graded Tasks", f"{avg_score:.1f}%")
            
            fig_scores = px.bar(
                graded_df,
                x="subject_code",
                y="percentage_score",
                color="subject_code",
                hover_name="title",
                title="Assignment Scores (%) by Subject"
            )
            fig_scores.update_layout(yaxis=dict(range=[0, 105], title="Score (%)"), height=300)
            st.plotly_chart(fig_scores, use_container_width=True)

        with c_an2:
            fig_pie = px.pie(
                assign_df,
                names="status",
                title="Status Breakdown of All Assignments",
                color="status",
                color_discrete_map={
                    "Pending": "#DC2626",
                    "In Progress": "#D97706",
                    "Submitted": "#0284C7",
                    "Graded": "#16A34A"
                }
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No graded assignments recorded yet.")

# --- TAB 4: ADD NEW ASSIGNMENT ---
with tab_new:
    st.subheader("➕ Create New Coursework or Laboratory Assignment")
    
    subjects_df = pd.read_sql_query("SELECT id, code, name FROM subjects ORDER BY code;", conn)
    sub_choices = {f"{s['code']} - {s['name']}": s['id'] for _, s in subjects_df.iterrows()}

    with st.form("create_assign_form", clear_on_submit=True):
        sel_sub_name = st.selectbox("Subject:", list(sub_choices.keys()))
        new_title = st.text_input("Assignment Title:", placeholder="e.g. Implement B-Tree Indexing in C++")
        new_desc = st.text_area("Task Description & Submission Guidelines:")
        
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            new_due = st.date_input("Due Date:", value=today_dt.date())
        with c_d2:
            new_max_marks = st.number_input("Maximum Marks:", min_value=10, max_value=200, value=100)

        create_btn = st.form_submit_button("Add Assignment")
        if create_btn:
            if not new_title:
                st.error("Title is required.")
            else:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO assignments (subject_id, title, description, due_date, max_marks, status)
                VALUES (?, ?, ?, ?, ?, 'Pending');
                """, (sub_choices[sel_sub_name], new_title, new_desc, new_due.strftime("%Y-%m-%d"), new_max_marks))
                conn.commit()
                st.success("New assignment added to schedule!")
                st.rerun()

conn.close()
