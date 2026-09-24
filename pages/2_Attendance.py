"""
Campus Companion - Attendance Tracker
Live calculation from attendance_log, daily attendance marker synced with timetable,
75% Indian college cutoff analysis, and the Bunk-o-Meter (Classes to attend/skip).
"""

import streamlit as st
import pandas as pd
import math
from datetime import datetime, date
from database import get_connection, render_sidebar, get_subject_color

# Page Configuration
st.set_page_config(
    page_title="Attendance Tracker - Campus Companion",
    page_icon="📊",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title("📊 Attendance Tracker & Cutoff Calculator")
st.caption("Live attendance monitoring compliant with university 75% mandatory attendance regulations.")

# Current Date Logic
current_date_str = "2026-09-24"
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")
day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
current_day_name = day_names[today_dt.weekday()]

# Fetch Subjects & Attendance Data
subjects_query = "SELECT id, code, name, credits FROM subjects ORDER BY code;"
subjects_df = pd.read_sql_query(subjects_query, conn)

att_query = """
SELECT 
    al.id, al.subject_id, al.date, al.status, al.period_slot, al.remarks,
    s.code AS subject_code, s.name AS subject_name
FROM attendance_log al
JOIN subjects s ON al.subject_id = s.id
ORDER BY al.date DESC, al.id DESC;
"""
att_df = pd.read_sql_query(att_query, conn)

# Overall Statistics Calculation
total_sessions = len(att_df)
attended_sessions = len(att_df[att_df["status"] == "Present"])
overall_pct = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0.0

# Subject level calculation
sub_stats = []
safe_count = 0
shortage_count = 0

for _, s in subjects_df.iterrows():
    s_logs = att_df[att_df["subject_id"] == s["id"]]
    t = len(s_logs)
    a = len(s_logs[s_logs["status"] == "Present"])
    pct = (a / t * 100) if t > 0 else 100.0

    # Bunk / Attend calculations for 75% cutoff
    # Formula: (A + x) / (T + x) >= 0.75 -> x >= 3T - 4A
    # Skip: A / (T + y) >= 0.75 -> y <= (4A - 3T) / 3
    classes_to_attend = max(0, math.ceil(3 * t - 4 * a))
    classes_can_skip = max(0, math.floor((4 * a - 3 * t) / 3)) if t > 0 else 0

    if t > 0:
        if pct >= 75.0:
            safe_count += 1
        else:
            shortage_count += 1

    sub_stats.append({
        "id": s["id"],
        "code": s["code"],
        "name": s["name"],
        "credits": s["credits"],
        "total": t,
        "attended": a,
        "percentage": pct,
        "to_attend": classes_to_attend,
        "can_skip": classes_can_skip
    })

# --- KPI METRICS TOP BAR ---
k1, k2, k3, k4 = st.columns(4)
with k1:
    delta_str = f"{overall_pct - 75.0:+.1f}% vs 75% cutoff"
    st.metric("Overall Attendance", f"{overall_pct:.1f}%", delta=delta_str, delta_color="normal" if overall_pct >= 75 else "inverse")
with k2:
    st.metric("Total Classes Conducted", f"{total_sessions} Sessions")
with k3:
    st.metric("Subjects Safe (≥75%)", f"{safe_count} Courses", delta="Safe from exam debar")
with k4:
    st.metric("Subjects in Defaulter Zone", f"{shortage_count} Courses", delta="Immediate action needed" if shortage_count > 0 else "All clean", delta_color="inverse" if shortage_count > 0 else "normal")

st.divider()

# Navigation tabs
tab_overview, tab_mark, tab_simulator, tab_history = st.tabs([
    "📈 Subject Attendance Cards",
    "✍️ Mark Today's Attendance",
    "🧮 What-If Bunk Simulator",
    "📜 Attendance Logs & History"
])

# --- TAB 1: SUBJECT ATTENDANCE CARDS ---
with tab_overview:
    st.subheader("Course-by-Course Attendance Health")
    st.caption("Visual progress bars indicate compliance with the mandatory 75% attendance rule.")

    # Two-column grid of subject cards
    col_left, col_right = st.columns(2, gap="medium")
    for idx, stat in enumerate(sub_stats):
        target_col = col_left if idx % 2 == 0 else col_right
        with target_col:
            with st.container(border=True):
                # Header row
                c_h1, c_h2 = st.columns([3, 1])
                with c_h1:
                    st.markdown(f"### {stat['code']}")
                    st.caption(stat['name'])
                with c_h2:
                    st.markdown(f"## {stat['percentage']:.1f}%")

                # Progress bar
                progress_val = min(1.0, max(0.0, stat['percentage'] / 100.0))
                st.progress(progress_val)

                # Stats info
                st.write(f"Attended: **{stat['attended']}** / **{stat['total']}** classes")

                # Cutoff evaluation & actionable recommendation
                if stat['total'] == 0:
                    st.info("ℹ️ No classes recorded yet for this subject.")
                elif stat['percentage'] < 75.0:
                    st.error(
                        f"🚨 **Attendance Shortage!** You must attend the next **{stat['to_attend']}** classes "
                        f"consecutively to cross the 75% cutoff."
                    )
                else:
                    if stat['can_skip'] > 0:
                        st.success(
                            f"✅ **Safe Zone!** You can safely skip up to **{stat['can_skip']}** upcoming classes "
                            f"and remain above 75%."
                        )
                    else:
                        st.warning("⚠️ **Borderline!** You are at the 75% margin. Missing even 1 class will trigger attendance shortage.")

# --- TAB 2: MARK TODAY'S ATTENDANCE ---
with tab_mark:
    st.subheader("✍️ Log Today's Classroom Attendance")
    st.write("Marking is tied to the schedule timetable to ensure accurate record keeping.")

    # Date and day selection
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        log_date = st.date_input("Attendance Date:", value=today_dt.date())
    with col_d2:
        log_day_name = day_names[log_date.weekday()]
        st.info(f"Detected Timetable Day: **{log_day_name}**")

    # Pull scheduled classes for that day
    sched_day_query = """
    SELECT 
        cs.id, cs.start_time, cs.end_time, cs.room, cs.session_type,
        s.id AS subject_id, s.code AS subject_code, s.name AS subject_name,
        f.name AS faculty_name
    FROM class_schedule cs
    JOIN subjects s ON cs.subject_id = s.id
    LEFT JOIN faculty f ON cs.faculty_id = f.id
    WHERE cs.day_of_week = ?
    ORDER BY cs.start_time ASC;
    """
    day_classes_df = pd.read_sql_query(sched_day_query, conn, params=(log_day_name,))

    if day_classes_df.empty:
        st.warning(f"No classes scheduled in master timetable for {log_day_name}.")
    else:
        with st.form("mark_attendance_form"):
            st.markdown(f"#### Scheduled Sessions for {log_day_name} ({log_date.strftime('%Y-%m-%d')})")
            
            attendance_inputs = {}
            for _, c_row in day_classes_df.iterrows():
                slot_key = f"{c_row['id']}_{c_row['subject_id']}"
                with st.container(border=True):
                    sc1, sc2, sc3 = st.columns([3, 2, 2])
                    with sc1:
                        st.markdown(f"**{c_row['subject_code']} - {c_row['subject_name']}**")
                        st.caption(f"🕒 {c_row['start_time']} - {c_row['end_time']} | 📍 {c_row['room']}")
                    with sc2:
                        status_val = st.radio(
                            "Status:",
                            options=["Present", "Absent"],
                            index=0,
                            key=f"status_{slot_key}",
                            horizontal=True
                        )
                    with sc3:
                        remarks_val = st.text_input(
                            "Notes (optional):",
                            placeholder="e.g. Lab experiment #4",
                            key=f"rem_{slot_key}"
                        )
                    attendance_inputs[slot_key] = {
                        "subject_id": c_row["subject_id"],
                        "slot": f"{c_row['start_time']} - {c_row['end_time']}",
                        "status": status_val,
                        "remarks": remarks_val
                    }

            submit_att = st.form_submit_button("Submit Attendance Log")
            if submit_att:
                cursor = conn.cursor()
                date_str = log_date.strftime("%Y-%m-%d")
                for key, data in attendance_inputs.items():
                    # Check for existing log to prevent duplicates
                    cursor.execute("""
                    SELECT id FROM attendance_log 
                    WHERE subject_id = ? AND date = ? AND period_slot = ?;
                    """, (data["subject_id"], date_str, data["slot"]))
                    existing_entry = cursor.fetchone()
                    if existing_entry:
                        cursor.execute("""
                        UPDATE attendance_log 
                        SET status = ?, remarks = ?
                        WHERE id = ?;
                        """, (data["status"], data["remarks"], existing_entry[0]))
                    else:
                        cursor.execute("""
                        INSERT INTO attendance_log (subject_id, date, status, period_slot, remarks)
                        VALUES (?, ?, ?, ?, ?);
                        """, (data["subject_id"], date_str, data["status"], data["slot"], data["remarks"]))
                conn.commit()
                st.success(f"🎉 Attendance successfully recorded/updated for {len(attendance_inputs)} classes on {date_str}!")
                st.rerun()

# --- TAB 3: WHAT-IF BUNK SIMULATOR ---
with tab_simulator:
    st.subheader("🧮 Bunk-o-Meter & Term Attendance Calculator")
    st.write("Plan your leaves based on remaining semester classes and simulate future attendance trajectories.")

    sim_sub_options = {f"{s['code']} - {s['name']}": s for s in sub_stats if s['total'] > 0}
    if sim_sub_options:
        selected_sim_label = st.selectbox("Select Subject to Analyze:", list(sim_sub_options.keys()))
        selected_sub = sim_sub_options[selected_sim_label]

        current_tot = selected_sub["total"]
        current_att = selected_sub["attended"]
        current_perc = selected_sub["percentage"]

        st.info(f"Current Stats for **{selected_sub['code']}**: Attended **{current_att}** / **{current_tot}** ({current_perc:.1f}%)")

        st.markdown("#### 🎯 Term-Wide Attendance Target (Based on Remaining Classes)")
        c_term1, c_term2 = st.columns(2)
        with c_term1:
            total_planned_term = st.number_input(
                f"Total Planned Lectures in Semester Term for {selected_sub['code']}:",
                min_value=current_tot + 1,
                max_value=100,
                value=max(current_tot + 15, 45)
            )
        with c_term2:
            remaining_in_term = total_planned_term - current_tot
            st.metric("Remaining Classes in Term", f"{remaining_in_term} Lectures")

        # Term calculations
        # Required total attended to achieve 75%: ceil(0.75 * total_planned_term)
        req_total_att = math.ceil(0.75 * total_planned_term)
        must_attend_rem = max(0, req_total_att - current_att)
        can_skip_rem = remaining_in_term - must_attend_rem

        with st.container(border=True):
            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                st.metric("Required Total Attended", f"{req_total_att} / {total_planned_term}", delta="75% Cutoff")
            with tc2:
                st.metric("Must Attend from Remaining", f"{must_attend_rem} of {remaining_in_term}", delta="Required for exam hall ticket")
            with tc3:
                st.metric("Can Skip from Remaining", f"{max(0, can_skip_rem)} Lectures", delta="Allowed leaves")

            if must_attend_rem > remaining_in_term:
                max_achievable = ((current_att + remaining_in_term) / total_planned_term) * 100
                st.error(f"🚨 **Mathematical Shortage!** Even attending 100% of remaining {remaining_in_term} classes will reach only {max_achievable:.1f}%. Immediate faculty appeal needed.")
            elif must_attend_rem == 0:
                st.success(f"🎉 **Deficit Impossible!** You have already attended enough classes to satisfy the 75% rule for the whole term.")
            else:
                st.info(f"📌 **Term Recommendation:** Attend at least **{must_attend_rem}** out of the next **{remaining_in_term}** lectures to guarantee exam eligibility (maximum **{can_skip_rem}** skips allowed).")

        st.markdown("#### 🔮 Interactive Streak Simulator")
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            future_attend = st.slider("Classes you will attend consecutively:", min_value=0, max_value=25, value=3)
        with col_sim2:
            future_miss = st.slider("Classes you will miss/bunk:", min_value=0, max_value=25, value=1)

        sim_new_tot = current_tot + future_attend + future_miss
        sim_new_att = current_att + future_attend
        sim_new_pct = (sim_new_att / sim_new_tot * 100) if sim_new_tot > 0 else 0.0

        with st.container(border=True):
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Projected Total Classes", sim_new_tot, delta=f"+{future_attend + future_miss}")
            with r2:
                st.metric("Projected Attended", sim_new_att, delta=f"+{future_attend}")
            with r3:
                pct_diff = sim_new_pct - current_perc
                st.metric("Projected Attendance %", f"{sim_new_pct:.1f}%", delta=f"{pct_diff:+.1f}%")

            if sim_new_pct >= 75.0:
                st.success(f"🎉 Result: **Eligible!** You will be in the safe zone ({sim_new_pct:.1f}% ≥ 75%).")
            else:
                st.error(f"🚨 Result: **Debarred Risk!** You will drop to {sim_new_pct:.1f}%, which is below the 75% threshold.")
    else:
        st.info("Log attendance records first to enable the simulator.")

# --- TAB 4: ATTENDANCE HISTORY LOGS ---
with tab_history:
    st.subheader("📜 Detailed Attendance Records")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        hist_sub_filter = st.selectbox(
            "Filter History by Subject:",
            ["All Subjects"] + subjects_df["code"].tolist()
        )
    with col_f2:
        hist_status_filter = st.selectbox(
            "Filter History by Status:",
            ["All Status", "Present", "Absent"]
        )

    hist_df = att_df.copy()
    if hist_sub_filter != "All Subjects":
        hist_df = hist_df[hist_df["subject_code"] == hist_sub_filter]
    if hist_status_filter != "All Status":
        hist_df = hist_df[hist_df["status"] == hist_status_filter]

    display_hist = hist_df[[
        "id", "date", "subject_code", "subject_name", "status", "period_slot", "remarks"
    ]].rename(columns={
        "id": "Log ID",
        "date": "Date",
        "subject_code": "Code",
        "subject_name": "Subject",
        "status": "Attendance",
        "period_slot": "Period Slot",
        "remarks": "Notes"
    })

    st.dataframe(display_hist, use_container_width=True, hide_index=True)

    # Allow deleting incorrect log entry
    if not hist_df.empty:
        with st.expander("🛠️ Delete or Correct an Attendance Entry"):
            log_ids = hist_df["id"].tolist()
            del_id = st.selectbox("Select Log ID to remove:", log_ids)
            if st.button("Delete Selected Log Entry"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM attendance_log WHERE id = ?;", (del_id,))
                conn.commit()
                st.warning(f"Log entry #{del_id} deleted successfully!")
                st.rerun()

conn.close()
