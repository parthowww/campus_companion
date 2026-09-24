

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from database import get_connection, render_sidebar, get_subject_color

# Page Configuration
st.set_page_config(
    page_title="Campus Companion - Home Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()

# Fetch DB connection
conn = get_connection()

# Current date and time logic
current_date_str = "2026-09-24"
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")
day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
current_day_name = day_names[today_dt.weekday()]

# Header
st.title("🎓 Campus Companion — Student Command Center")
st.caption(f"📅 Today: **{current_day_name}, September 24, 2026** | Term: **Odd Semester 2026 (Semester 3)** | Role: **{role}**")

# --- KPI METRICS SECTION ---
# 1. CGPA Calculation
grades_df = pd.read_sql_query("SELECT semester, credits, grade_points FROM student_grades;", conn)
if not grades_df.empty:
    total_credits = grades_df["credits"].sum()
    total_points = (grades_df["credits"] * grades_df["grade_points"]).sum()
    cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
else:
    cgpa = 0.0

# 2. Overall Attendance %
att_df = pd.read_sql_query("SELECT status FROM attendance_log;", conn)
if not att_df.empty:
    total_classes = len(att_df)
    present_classes = len(att_df[att_df["status"] == "Present"])
    overall_att_pct = round((present_classes / total_classes) * 100, 1)
else:
    overall_att_pct = 0.0

# 3. Next Holiday
holidays_df = pd.read_sql_query("SELECT name, date, category FROM holidays ORDER BY date ASC;", conn)
holidays_df["date_obj"] = pd.to_datetime(holidays_df["date"])
upcoming_holidays = holidays_df[holidays_df["date"] >= current_date_str]
if not upcoming_holidays.empty:
    next_holiday = upcoming_holidays.iloc[0]
    days_to_holiday = (next_holiday["date_obj"] - today_dt).days
    holiday_metric_label = next_holiday["name"]
    holiday_metric_val = f"In {days_to_holiday} days"
    holiday_delta_val = next_holiday["category"]
else:
    holiday_metric_label = "None upcoming"
    holiday_metric_val = "N/A"
    holiday_delta_val = None

# 4. Pending Assignments
assignments_df = pd.read_sql_query("SELECT id, status, due_date FROM assignments;", conn)
pending_assignments_count = len(assignments_df[assignments_df["status"].isin(["Pending", "In Progress"])])

# 5. Upcoming Events
events_df = pd.read_sql_query("SELECT id, title, date FROM events WHERE date >= ?;", conn, params=(current_date_str,))
upcoming_events_count = len(events_df)

# Render Metric Cards
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric(
        label="Cumulative CGPA",
        value=f"{cgpa:.2f} / 10.0",
        delta="+0.15 (Sem 4)"
    )
with m2:
    att_delta = f"{overall_att_pct - 75.0:+.1f}% vs 75% cutoff"
    st.metric(
        label="Overall Attendance",
        value=f"{overall_att_pct}%",
        delta=att_delta,
        delta_color="normal" if overall_att_pct >= 75.0 else "inverse"
    )
with m3:
    holiday_disp_title = f"Next: {holiday_metric_label[:14]}..." if len(holiday_metric_label) > 14 else f"Next: {holiday_metric_label}"
    st.metric(
        label=holiday_disp_title,
        value=holiday_metric_val,
        delta=holiday_delta_val
    )
with m4:
    st.metric(
        label="Pending Assignments",
        value=f"{pending_assignments_count} Tasks",
        delta="Action required",
        delta_color="off"
    )
with m5:
    st.metric(
        label="Campus Events",
        value=f"{upcoming_events_count} Active",
        delta="This semester"
    )

st.divider()

# --- MAIN DASHBOARD LAYOUT (2 COLUMNS) ---
left_col, right_col = st.columns([3, 2], gap="large")

with left_col:
    st.subheader("📅 Today's Class Schedule")
    
    # Day selector allowing fresh view or previewing another day
    selected_day = st.selectbox(
        "Select Day to Inspect:",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].index(current_day_name) if current_day_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] else 3
    )

    day_schedule_query = """
    SELECT 
        cs.id, cs.day_of_week, cs.start_time, cs.end_time, cs.room, cs.session_type,
        s.code AS subject_code, s.name AS subject_name, s.color_code,
        f.name AS faculty_name, f.email AS faculty_email
    FROM class_schedule cs
    JOIN subjects s ON cs.subject_id = s.id
    LEFT JOIN faculty f ON cs.faculty_id = f.id
    WHERE cs.day_of_week = ?
    ORDER BY cs.start_time ASC;
    """
    today_schedule_df = pd.read_sql_query(day_schedule_query, conn, params=(selected_day,))

    if today_schedule_df.empty:
        st.info(f"🎉 No lectures scheduled for {selected_day}! Enjoy your self-study time or club activities.")
    else:
        for idx, row in today_schedule_df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.5, 3, 2])
                with c1:
                    st.markdown(f"**⏰ {row['start_time']} - {row['end_time']}**")
                    st.caption(f"Type: `{row['session_type']}`")
                with c2:
                    st.markdown(f"**{row['subject_code']} - {row['subject_name']}**")
                    st.caption(f"👨‍🏫 Faculty: **{row['faculty_name'] or 'Department Staff'}**")
                with c3:
                    st.markdown(f"📍 Room: **{row['room']}**")
                    st.caption("Floor directions available in Campus Map")

    st.subheader("📊 Subject-Wise Attendance Status")
    sub_att_query = """
    SELECT 
        s.name AS subject_name, s.code AS subject_code,
        COUNT(al.id) AS total_sessions,
        SUM(CASE WHEN al.status = 'Present' THEN 1 ELSE 0 END) AS attended_sessions
    FROM subjects s
    LEFT JOIN attendance_log al ON s.id = al.subject_id
    GROUP BY s.id
    HAVING total_sessions > 0
    ORDER BY s.code;
    """
    sub_att_df = pd.read_sql_query(sub_att_query, conn)
    
    if not sub_att_df.empty:
        sub_att_df["percentage"] = (sub_att_df["attended_sessions"] / sub_att_df["total_sessions"]) * 100
        sub_att_df["label"] = sub_att_df["subject_code"] + " (" + sub_att_df["percentage"].round(1).astype(str) + "%)"
        sub_att_df["status_color"] = sub_att_df["percentage"].apply(
            lambda x: "#16A34A" if x >= 80 else ("#D97706" if x >= 75 else "#DC2626")
        )

        fig_att = go.Figure()
        fig_att.add_trace(go.Bar(
            y=sub_att_df["subject_code"],
            x=sub_att_df["percentage"],
            orientation="h",
            marker=dict(color=sub_att_df["status_color"]),
            text=sub_att_df["percentage"].round(1).astype(str) + "%",
            textposition="auto",
            hovertext=sub_att_df["subject_name"],
            name="Attendance %"
        ))
        # Add cutoff line at 75%
        fig_att.add_vline(
            x=75, line_width=2, line_dash="dash", line_color="#DC2626",
            annotation_text="75% Cutoff", annotation_position="top right"
        )
        fig_att.update_layout(
            xaxis=dict(title="Attendance Percentage (%)", range=[0, 105]),
            yaxis=dict(title="Subject Code", autorange="reversed"),
            margin=dict(l=10, r=10, t=20, b=20),
            height=300
        )
        st.plotly_chart(fig_att, use_container_width=True)
    else:
        st.info("No attendance records logged yet.")

with right_col:
    st.subheader("📢 Urgent Notices & Circulars")
    notices_query = """
    SELECT title, category, published_date, content, target_audience
    FROM notices
    WHERE is_pinned = 1 OR category = 'Urgent'
    ORDER BY published_date DESC
    LIMIT 4;
    """
    notices_df = pd.read_sql_query(notices_query, conn)
    
    for _, notice in notices_df.iterrows():
        with st.expander(f"🔴 [{notice['category']}] {notice['title']}", expanded=True):
            st.caption(f"🗓️ Posted: {notice['published_date']} | Audience: `{notice['target_audience']}`")
            st.write(notice["content"])

    st.subheader("📈 Academic SGPA Trend")
    sem_query = """
    SELECT semester, SUM(credits * grade_points) / SUM(credits) as sgpa
    FROM student_grades
    GROUP BY semester
    ORDER BY semester ASC;
    """
    sem_df = pd.read_sql_query(sem_query, conn)
    if not sem_df.empty:
        sem_df["Semester_Label"] = "Sem " + sem_df["semester"].astype(str)
        fig_sgpa = px.line(
            sem_df,
            x="Semester_Label",
            y="sgpa",
            markers=True,
            text=sem_df["sgpa"].round(2),
            title="SGPA Progression (Semesters 1-4)"
        )
        fig_sgpa.update_traces(textposition="top center", line_color="#4F46E5", marker=dict(size=8))
        fig_sgpa.update_layout(
            yaxis=dict(title="SGPA (out of 10)", range=[7.5, 10.0]),
            xaxis=dict(title=""),
            margin=dict(l=10, r=10, t=40, b=20),
            height=250
        )
        st.plotly_chart(fig_sgpa, use_container_width=True)

    st.subheader("⚡ Quick Navigation Portal")
    q1, q2 = st.columns(2)
    with q1:
        st.page_link("pages/1_Class_Schedule.py", label="Weekly Timetable", icon="🗓️")
        st.page_link("pages/2_Attendance.py", label="Attendance Tracker", icon="📊")
        st.page_link("pages/4_Campus_Map.py", label="Campus Map & Rooms", icon="🗺️")
        st.page_link("pages/7_Assignments.py", label="Assignments", icon="📝")
        st.page_link("pages/8_CGPA_Calculator.py", label="CGPA Predictor", icon="🎯")
    with q2:
        st.page_link("pages/3_Holidays.py", label="Holiday Countdown", icon="🏖️")
        st.page_link("pages/5_Events.py", label="College Events", icon="🎪")
        st.page_link("pages/6_Club_Events.py", label="Clubs & Societies", icon="🚀")
        st.page_link("pages/9_Notice_Board.py", label="Notice Board", icon="📌")
        st.page_link("pages/10_Faculty_Directory.py", label="Faculty Directory", icon="👨‍🏫")

conn.close()
