"""
Campus Companion - Class Schedule Tracker
Weekly timetable grid (Mon-Sat x period slots), color-coded by subject hash,
with full Add/Edit/Delete class management for Admin.
"""

import streamlit as st
import pandas as pd
from database import get_connection, render_sidebar, get_subject_color

# Page Configuration
st.set_page_config(
    page_title="Class Schedule - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title("️ Class Schedule Tracker")
st.caption("Weekly timetable grid across period slots with room allocations and faculty info.")

# Fetch schedule, subjects, faculty
schedule_query = """
SELECT 
    cs.id, cs.day_of_week, cs.start_time, cs.end_time, cs.room, cs.session_type,
    s.id AS subject_id, s.code AS subject_code, s.name AS subject_name, s.color_code,
    f.id AS faculty_id, f.name AS faculty_name
FROM class_schedule cs
JOIN subjects s ON cs.subject_id = s.id
LEFT JOIN faculty f ON cs.faculty_id = f.id
ORDER BY 
    CASE cs.day_of_week
        WHEN 'Monday' THEN 1
        WHEN 'Tuesday' THEN 2
        WHEN 'Wednesday' THEN 3
        WHEN 'Thursday' THEN 4
        WHEN 'Friday' THEN 5
        WHEN 'Saturday' THEN 6
        ELSE 7
    END,
    cs.start_time ASC;
"""
sched_df = pd.read_sql_query(schedule_query, conn)

# Subject palette legend
subjects_df = pd.read_sql_query("SELECT id, code, name FROM subjects ORDER BY code;", conn)
faculty_df = pd.read_sql_query("SELECT id, name, department FROM faculty ORDER BY name;", conn)
rooms_df = pd.read_sql_query("SELECT room_number, block_name FROM buildings_rooms ORDER BY room_number;", conn)

tab_grid, tab_table, tab_manage = st.tabs([" Weekly Schedule Grid", " Detailed Schedule List", "⚙️ Manage Classes"])

# --- TAB 1: WEEKLY SCHEDULE GRID ---
with tab_grid:
    st.subheader("Weekly Timetable Matrix (Mon - Sat)")
    
    # Subject Legend
    st.markdown("**Subject Color Key:**")
    legend_cols = st.columns(min(6, len(subjects_df)))
    for idx, s_row in subjects_df.head(12).iterrows():
        col_idx = idx % 6
        color = get_subject_color(s_row["name"])
        with legend_cols[col_idx]:
            st.markdown(f":balloon: `{s_row['code']}` — {s_row['name'][:18]}")

    st.write("")
    
    # View Selector
    view_mode = st.radio("Choose Schedule Presentation:", [" Styled Timetable Matrix (Grid)", "️ Day-by-Day Detailed Columns"], horizontal=True)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if view_mode == " Styled Timetable Matrix (Grid)":
        # Build period slots
        sched_df["slot"] = sched_df["start_time"] + " - " + sched_df["end_time"]
        unique_slots = sorted(sched_df["slot"].unique().tolist())
        
        # Initialize matrix DataFrame
        matrix_data = {d: ["—"] * len(unique_slots) for d in days}
        matrix_df = pd.DataFrame(matrix_data, index=unique_slots)

        for _, row in sched_df.iterrows():
            d = row["day_of_week"]
            s = row["slot"]
            if d in matrix_df.columns and s in matrix_df.index:
                cell_val = f"{row['subject_code']} [{row['room']}]"
                matrix_df.at[s, d] = cell_val

        def color_timetable_cell(val):
            if not val or val == "—":
                return "background-color: #F8FAFC; color: #94A3B8; text-align: center;"
            sub_prefix = val.split(" ")[0].split("[")[0].strip()
            bg_col = get_subject_color(sub_prefix)
            return f"background-color: {bg_col}; color: #FFFFFF; font-weight: bold; text-align: center; border-radius: 4px;"

        styled_timetable = matrix_df.style.map(color_timetable_cell)
        st.dataframe(styled_timetable, use_container_width=True, height=360)

    else:
        # Grid of Days (Monday to Saturday)
        day_cols = st.columns(len(days))

        for idx, day in enumerate(days):
            with day_cols[idx]:
                st.markdown(f"#### {day[:3].upper()}")
                day_classes = sched_df[sched_df["day_of_week"] == day]
                
                if day_classes.empty:
                    st.caption("No classes scheduled")
                else:
                    for _, cls in day_classes.iterrows():
                        color = get_subject_color(cls["subject_name"])
                        with st.container(border=True):
                            st.markdown(f"**{cls['subject_code']}**")
                            st.caption(f"{cls['subject_name'][:20]}")
                            st.markdown(f" `{cls['start_time']} - {cls['end_time']}`")
                            st.caption(f" {cls['room']}")
                            st.caption(f"‍ {cls['faculty_name'] or 'Staff'}")
                            badge_label = cls['session_type']
                            if badge_label == "Lab":
                                st.info(f" {badge_label}")
                            else:
                                st.success(f" {badge_label}")

# --- TAB 2: DETAILED SCHEDULE LIST ---
with tab_table:
    st.subheader("Search & Filter Class Schedule")
    
    f1, f2, f3 = st.columns(3)
    with f1:
        filter_day = st.multiselect("Filter by Day:", options=days, default=[])
    with f2:
        filter_sub = st.multiselect("Filter by Subject:", options=subjects_df["code"].tolist(), default=[])
    with f3:
        filter_type = st.multiselect("Filter by Session Type:", options=["Lecture", "Lab", "Tutorial"], default=[])

    filtered_df = sched_df.copy()
    if filter_day:
        filtered_df = filtered_df[filtered_df["day_of_week"].isin(filter_day)]
    if filter_sub:
        filtered_df = filtered_df[filtered_df["subject_code"].isin(filter_sub)]
    if filter_type:
        filtered_df = filtered_df[filtered_df["session_type"].isin(filter_type)]

    display_df = filtered_df[[
        "id", "day_of_week", "start_time", "end_time", "subject_code",
        "subject_name", "room", "faculty_name", "session_type"
    ]].rename(columns={
        "id": "Class ID",
        "day_of_week": "Day",
        "start_time": "Starts",
        "end_time": "Ends",
        "subject_code": "Code",
        "subject_name": "Subject Title",
        "room": "Room / Lab",
        "faculty_name": "Instructor",
        "session_type": "Format"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=" Download Schedule as CSV",
        data=csv_data,
        file_name="campus_schedule_sem5.csv",
        mime="text/csv"
    )

# --- TAB 3: MANAGE CLASSES (ADMIN ONLY) ---
with tab_manage:
    if role == "Admin":
        st.subheader(" Master Schedule Management")
        st.write("Add, update, or remove period allocations from the institutional schedule.")

        m_col1, m_col2 = st.columns([1, 1], gap="large")

        with m_col1:
            st.markdown("#### ➕ Add New Scheduled Class")
            with st.form("add_class_form", clear_on_submit=True):
                subject_options = {f"{r['code']} - {r['name']}": r['id'] for _, r in subjects_df.iterrows()}
                selected_sub_name = st.selectbox("Select Subject:", options=list(subject_options.keys()))
                
                day_choice = st.selectbox("Day of Week:", days)
                
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    start_val = st.text_input("Start Time (e.g. 09:00 AM):", value="09:00 AM")
                with c_t2:
                    end_val = st.text_input("End Time (e.g. 10:00 AM):", value="10:00 AM")

                room_list = [r["room_number"] for _, r in rooms_df.iterrows()]
                room_choice = st.selectbox("Room / Hall:", room_list)

                faculty_options = {f"{f['name']} ({f['department']})": f['id'] for _, f in faculty_df.iterrows()}
                faculty_choice = st.selectbox("Faculty Instructor:", list(faculty_options.keys()))

                session_type_choice = st.selectbox("Session Type:", ["Lecture", "Lab", "Tutorial"])

                submitted = st.form_submit_button("Save Class to Timetable")
                if submitted:
                    sub_id = subject_options[selected_sub_name]
                    fac_id = faculty_options[faculty_choice]
                    
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO class_schedule (subject_id, day_of_week, start_time, end_time, room, faculty_id, session_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (sub_id, day_choice, start_val, end_val, room_choice, fac_id, session_type_choice))
                    conn.commit()
                    st.success(" Class added to timetable successfully! Reloading view...")
                    st.rerun()

        with m_col2:
            st.markdown("#### ️ Edit or Delete Existing Class")
            if not sched_df.empty:
                class_dict = {
                    f"#{row['id']} [{row['day_of_week'][:3]}] {row['subject_code']} ({row['start_time']} - {row['room']})": row['id']
                    for _, row in sched_df.iterrows()
                }
                selected_class_label = st.selectbox("Select Class to Manage:", list(class_dict.keys()))
                target_id = class_dict[selected_class_label]

                class_to_edit = sched_df[sched_df["id"] == target_id].iloc[0]

                with st.form("edit_class_form"):
                    st.caption(f"Editing Class Record #{target_id}")
                    e_room = st.text_input("Update Room / Venue:", value=class_to_edit["room"])
                    e_start = st.text_input("Update Start Time:", value=class_to_edit["start_time"])
                    e_end = st.text_input("Update End Time:", value=class_to_edit["end_time"])
                    e_type = st.selectbox("Update Session Type:", ["Lecture", "Lab", "Tutorial"], index=["Lecture", "Lab", "Tutorial"].index(class_to_edit["session_type"]))

                    col_save, col_del = st.columns(2)
                    with col_save:
                        update_pressed = st.form_submit_button("Update Class Details")
                    with col_del:
                        delete_pressed = st.form_submit_button("Delete Class Entry")

                    if update_pressed:
                        cursor = conn.cursor()
                        cursor.execute("""
                        UPDATE class_schedule
                        SET room = ?, start_time = ?, end_time = ?, session_type = ?
                        WHERE id = ?;
                        """, (e_room, e_start, e_end, e_type, target_id))
                        conn.commit()
                        st.success("Class updated successfully!")
                        st.rerun()

                    if delete_pressed:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM class_schedule WHERE id = ?;", (target_id,))
                        conn.commit()
                        st.warning("Class deleted from timetable!")
                        st.rerun()
            else:
                st.info("No classes found to edit.")
    else:
        st.info(" **Admin Access Required**")
        st.write("You are currently viewing in **Student Role**. Switching to Admin in the sidebar unlocks the class scheduling and deletion forms.")

conn.close()
