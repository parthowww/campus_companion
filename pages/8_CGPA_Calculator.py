"""
Campus Companion - CGPA & SGPA Calculator & Target Predictor
Semester-wise grade point tracker, SGPA progression charts,
course grade manager with SQLite persistence, and target CGPA forecaster.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="CGPA Calculator - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title(" CGPA & SGPA Calculator")
st.caption("10-point Indian UGC/AICTE grading system calculator, semester progression tracker, and target CGPA planner.")

# Standard 10-Point Grade Map
GRADE_POINTS = {
    "O (Outstanding)": 10.0,
    "A+ (Excellent)": 9.0,
    "A (Very Good)": 8.0,
    "B+ (Good)": 7.0,
    "B (Above Average)": 6.0,
    "C (Average)": 5.0,
    "P (Pass)": 4.0,
    "F (Fail)": 0.0
}

# Fetch Grades Data
grades_query = """
SELECT id, semester, course_code, course_name, credits, grade_letter, grade_points
FROM student_grades
ORDER BY semester ASC, course_code ASC;
"""
grades_df = pd.read_sql_query(grades_query, conn)

# --- OVERALL CGPA & CREDITS CALCULATION ---
if not grades_df.empty:
    total_credits = grades_df["credits"].sum()
    total_grade_points = (grades_df["credits"] * grades_df["grade_points"]).sum()
    cgpa = (total_grade_points / total_credits) if total_credits > 0 else 0.0
else:
    total_credits = 0
    total_grade_points = 0.0
    cgpa = 0.0

# Semester breakdown calculation
sem_groups = []
if not grades_df.empty:
    for sem_num, group in grades_df.groupby("semester"):
        sem_cred = group["credits"].sum()
        sem_pts = (group["credits"] * group["grade_points"]).sum()
        sgpa = (sem_pts / sem_cred) if sem_cred > 0 else 0.0
        sem_groups.append({
            "semester": sem_num,
            "label": f"Semester {sem_num}",
            "credits": sem_cred,
            "sgpa": round(sgpa, 2)
        })

sem_summary_df = pd.DataFrame(sem_groups)

# Top Metric Banner
c1, c2 = st.columns(2)
st.write('')
c3, c4 = st.columns(2)
with c1:
    st.metric("Cumulative CGPA", f"{cgpa:.2f} / 10.0", delta=f"{cgpa - 8.0:+.2f} vs 8.0 distinction")
with c2:
    st.metric("Total Credits Earned", f"{total_credits} Credits")
with c3:
    completed_sems = len(sem_summary_df)
    st.metric("Semesters Completed", f"{completed_sems} Semesters")
with c4:
    best_sem = sem_summary_df.loc[sem_summary_df["sgpa"].idxmax()]["label"] if not sem_summary_df.empty else "N/A"
    best_sgpa = sem_summary_df["sgpa"].max() if not sem_summary_df.empty else 0.0
    st.metric("Highest SGPA", f"{best_sgpa:.2f}", delta=best_sem)

st.divider()

tab_overview, tab_planner, tab_manager = st.tabs([
    " Academic Progression & Breakdown",
    " Target CGPA Forecaster",
    "⚙️ Manage Course Grades"
])

# --- TAB 1: ACADEMIC PROGRESSION & BREAKDOWN ---
with tab_overview:
    st.subheader("Semester-Wise Academic Trajectory")

    if not sem_summary_df.empty:
        col_chart, col_sems = st.columns([3, 2], gap="large")
        
        with col_chart:
            fig_prog = go.Figure()
            fig_prog.add_trace(go.Scatter(
                x=sem_summary_df["label"],
                y=sem_summary_df["sgpa"],
                mode="lines+markers+text",
                text=sem_summary_df["sgpa"].apply(lambda x: f"{x:.2f}"),
                textposition="top center",
                line=dict(color="#4F46E5", width=3),
                marker=dict(size=10, color="#4338CA"),
                name="SGPA"
            ))
            # CGPA baseline
            fig_prog.add_hline(
                y=cgpa, line_dash="dash", line_color="#10B981",
                annotation_text=f"Current CGPA: {cgpa:.2f}",
                annotation_position="bottom right"
            )
            fig_prog.update_layout(
                title="SGPA Progression Trendline",
                yaxis=dict(range=[7.0, 10.2], title="SGPA Points"),
                xaxis=dict(title=""),
                height=350,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_prog, use_container_width=True)

        with col_sems:
            st.markdown("#### Semester Summary Table")
            st.dataframe(
                sem_summary_df.rename(columns={"label": "Semester", "credits": "Credits", "sgpa": "SGPA"}),
                use_container_width=True,
                hide_index=True
            )

        st.subheader(" Detailed Course Breakdown")
        if not sem_summary_df.empty:
            selected_sem = st.selectbox("Inspect Courses for Semester:", sem_summary_df["semester"].tolist())
            sem_courses = grades_df[grades_df["semester"] == selected_sem]

            st.dataframe(
                sem_courses[["course_code", "course_name", "credits", "grade_letter", "grade_points"]].rename(columns={
                    "course_code": "Course Code",
                    "course_name": "Course Title",
                    "credits": "Credits",
                    "grade_letter": "Grade",
                    "grade_points": "Points"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No courses registered yet.")
    else:
        st.info("No academic grades recorded yet. Add grades in the 'Manage Course Grades' tab.")

# --- TAB 2: TARGET CGPA FORECASTER ---
with tab_planner:
    st.subheader(" Target CGPA Planner & Feasibility Forecaster")
    st.write("Determine exactly what average SGPA you must score in remaining semesters to achieve your goal.")

    col_p1, col_p2 = st.columns([1, 1], gap="large")
    with col_p1:
        with st.container(border=True):
            st.markdown("#### Goal Configuration")
            target_cgpa = st.slider("Desired Graduation CGPA:", min_value=7.5, max_value=10.0, value=9.0, step=0.05)
            
            total_program_sems = 8
            current_completed_sems = len(sem_summary_df)
            remaining_sems = max(1, total_program_sems - current_completed_sems)
            
            rem_sems_input = st.number_input("Remaining Semesters to Complete:", min_value=1, max_value=8, value=remaining_sems)
            avg_credits_per_sem = st.number_input("Average Credits per Future Semester:", min_value=12, max_value=30, value=20)

            future_credits = rem_sems_input * avg_credits_per_sem
            total_graduation_credits = total_credits + future_credits

            # Calculation
            # (total_grade_points + required_future_points) / total_graduation_credits = target_cgpa
            required_future_points = (target_cgpa * total_graduation_credits) - total_grade_points
            required_future_sgpa = required_future_points / future_credits if future_credits > 0 else 0.0

    with col_p2:
        with st.container(border=True):
            st.markdown("####  Feasibility Outcome")
            st.metric("Required Average SGPA", f"{required_future_sgpa:.2f} / 10.0")
            
            if required_future_sgpa <= 0:
                st.success(" You have already exceeded this CGPA goal! Maintaining passing grades is sufficient.")
            elif required_future_sgpa <= 8.5:
                st.success(f" **Easily Achievable!** You need an average SGPA of **{required_future_sgpa:.2f}** over the next **{rem_sems_input}** semesters (A / B+ grade profile).")
            elif required_future_sgpa <= 9.5:
                st.warning(f"⚠️ **Challenging but Achievable!** You need an average SGPA of **{required_future_sgpa:.2f}** (mostly A+ and O grades required).")
            elif required_future_sgpa <= 10.0:
                st.error(f" **Extreme Difficulty!** You need nearly perfect 10.0 SGPA (**{required_future_sgpa:.2f}**) across every upcoming semester.")
            else:
                st.error(f" **Mathematically Impossible!** Scoring {required_future_sgpa:.2f} exceeds the maximum possible 10.0 limit. Consider adjusting your target CGPA to a realistic figure like {min(10.0, (total_grade_points + 10.0 * future_credits) / total_graduation_credits):.2f}.")

# --- TAB 3: MANAGE COURSE GRADES ---
with tab_manager:
    st.subheader("⚙️ Add or Update Course Grade Entries")
    st.caption("Data is persisted in campus.db SQLite database across app restarts.")

    col_m1, col_m2 = st.columns([1, 1], gap="large")

    with col_m1:
        st.markdown("#### ➕ Add Completed Course Grade")
        with st.form("add_grade_form", clear_on_submit=True):
            in_sem = st.number_input("Semester:", min_value=1, max_value=8, value=5)
            in_code = st.text_input("Course Code:", placeholder="e.g. CS309")
            in_name = st.text_input("Course Title:", placeholder="e.g. Compiler Design")
            in_credits = st.number_input("Course Credits:", min_value=1, max_value=10, value=4)
            
            grade_choice = st.selectbox("Grade Secured:", list(GRADE_POINTS.keys()))
            
            submit_grade = st.form_submit_button("Record Grade to Transcript")
            if submit_grade:
                if not in_code or not in_name:
                    st.error("Course code and title are required.")
                else:
                    g_letter = grade_choice.split(" ")[0]
                    g_pts = GRADE_POINTS[grade_choice]
                    
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO student_grades (semester, course_code, course_name, credits, grade_letter, grade_points)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """, (in_sem, in_code, in_name, in_credits, g_letter, g_pts))
                    conn.commit()
                    st.success(f"Course {in_code} added with grade {g_letter} ({g_pts} pts)!")
                    st.rerun()

    with col_m2:
        st.markdown("#### ️ Delete Course Grade Entry")
        if not grades_df.empty:
            grade_dict = {
                f"#{r['id']} [Sem {r['semester']}] {r['course_code']} - {r['course_name']} ({r['grade_letter']})": r['id']
                for _, r in grades_df.iterrows()
            }
            del_grade_choice = st.selectbox("Select Course Record to Remove:", list(grade_dict.keys()))
            target_del_id = grade_dict[del_grade_choice]

            if st.button("Delete Course Record", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM student_grades WHERE id = ?;", (target_del_id,))
                conn.commit()
                st.warning("Course grade record removed from database!")
                st.rerun()
        else:
            st.info("No courses to delete.")

conn.close()
