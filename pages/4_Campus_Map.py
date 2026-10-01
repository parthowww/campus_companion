"""
Campus Companion - Campus Map & Class Location Finder
Schematic 2D campus block visualization using Plotly, 'Find My Class' step-by-step
navigation guide for freshers, floor-by-floor directories, and facilities search.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="Campus Map & Finder - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title("️ Campus Map & Room Navigator")
st.caption("Fresher-friendly location directory, step-by-step walking routes, and 2D schematic campus guide.")

# Fetch Rooms & Buildings
rooms_query = """
SELECT id, block_name, room_number, room_type, floor, capacity, landmark, directions, coord_x, coord_y
FROM buildings_rooms
ORDER BY block_name, room_number;
"""
rooms_df = pd.read_sql_query(rooms_query, conn)

# Fetch Subjects and their assigned rooms from schedule for "Find My Class"
sched_rooms_query = """
SELECT DISTINCT s.code AS subject_code, s.name AS subject_name, cs.room, cs.session_type, cs.day_of_week, cs.start_time
FROM class_schedule cs
JOIN subjects s ON cs.subject_id = s.id
ORDER BY s.code, cs.day_of_week;
"""
sched_rooms_df = pd.read_sql_query(sched_rooms_query, conn)

tab_finder, tab_map, tab_directory, tab_manage = st.tabs([
    " Find My Class / Room",
    "️ Interactive 2D Campus Map",
    " Floor-by-Floor Directory",
    "⚙️ Manage Room Directory"
])

# --- TAB 1: FIND MY CLASS / ROOM ---
with tab_finder:
    st.subheader(" Freshers' Class & Venue Locator")
    st.write("Never get lost again! Search by your course or room number to get precise floor directions.")

    find_mode = st.radio(
        "Search Mode:",
        ["Search by Subject / Course", "Search by Room Number", "Search Campus Amenity / Facility"],
        horizontal=True
    )

    selected_room_target = None

    if find_mode == "Search by Subject / Course":
        if not sched_rooms_df.empty:
            subject_list = sched_rooms_df["subject_code"] + " — " + sched_rooms_df["subject_name"]
            subj_choice = st.selectbox("Select Your Enrolled Subject:", subject_list.unique())
            s_code = subj_choice.split(" — ")[0]
            matched_sched = sched_rooms_df[sched_rooms_df["subject_code"] == s_code]
            
            st.markdown(f"#### Timetable Allocations for `{s_code}`:")
            for _, m_row in matched_sched.iterrows():
                st.info(f" **{m_row['day_of_week']}** at **{m_row['start_time']}** ➔ Allocated Venue: **{m_row['room']}** (`{m_row['session_type']}`)")
            
            if not matched_sched.empty:
                selected_room_target = matched_sched.iloc[0]["room"]
        else:
            st.info("No courses scheduled with venues yet.")

    elif find_mode == "Search by Room Number":
        if not rooms_df.empty:
            room_list = rooms_df["room_number"].tolist()
            selected_room_target = st.selectbox("Select Destination Room / Lab:", room_list)
        else:
            st.info("No rooms registered.")

    else:
        facility_types = ["Library", "Cafeteria", "Health Center", "Auditorium", "Laboratory", "Admin", "Seminar Hall"]
        sel_fac = st.selectbox("Select Amenity Category:", facility_types)
        fac_rooms = rooms_df[rooms_df["room_type"] == sel_fac]
        if not fac_rooms.empty:
            selected_room_target = st.selectbox("Select Specific Facility:", fac_rooms["room_number"].tolist())
        else:
            st.warning("No rooms registered under this category yet.")

    # Show Navigation Card if room selected
    if selected_room_target:
        room_info = rooms_df[rooms_df["room_number"] == selected_room_target]
        if not room_info.empty:
            r = room_info.iloc[0]
            st.write("")
            with st.container(border=True):
                st.markdown(f"##  {r['room_number']}")
                st.caption(f"**{r['block_name']}** • Level: **{r['floor']}** • Type: **{r['room_type']}**")
                
                c_dir1, c_dir2 = st.columns([1, 1], gap="medium")
                with c_dir1:
                    st.markdown("####  Nearest Landmark")
                    st.write(r['landmark'])
                    st.metric("Seating / Lab Capacity", f"{r['capacity']} Persons")
                with c_dir2:
                    st.markdown("####  Step-by-Step Directions from Main Gate")
                    st.info(r['directions'])
                    st.caption("Tip: Look out for green directional wayfinding signage posted at all staircases and elevators.")

# --- TAB 2: INTERACTIVE 2D CAMPUS SCHEMATIC MAP ---
with tab_map:
    st.subheader("️ 2D Campus Block Schematic Map")
    st.caption("Interactive schematic layout of academic blocks, central facilities, and walking plazas.")

    # Distinct blocks coordinate representation
    blocks_summary = rooms_df.groupby("block_name").agg({
        "coord_x": "mean",
        "coord_y": "mean",
        "room_number": "count"
    }).reset_index().rename(columns={"room_number": "room_count"})

    fig_map = go.Figure()

    # Draw walking pathway links between blocks
    pathways = [
        ([25, 45, 65, 80], [30, 30, 30, 20]), # South Academic Street
        ([45, 50, 65, 75], [30, 65, 30, 55]), # Central Cross Spine
        ([25, 20, 50], [35, 75, 65]),         # West to Sports & Library
    ]
    for px_coords, py_coords in pathways:
        fig_map.add_trace(go.Scatter(
            x=px_coords, y=py_coords,
            mode="lines",
            line=dict(color="#CBD5E1", width=5, dash="dot"),
            hoverinfo="none",
            showlegend=False
        ))

    # Add Campus Central Landmark
    fig_map.add_trace(go.Scatter(
        x=[50], y=[45],
        mode="markers+text",
        marker=dict(size=28, color="#0EA5E9", symbol="diamond"),
        text=["⛲ Central Fountain Plaza"],
        textposition="bottom center",
        name="Plaza Landmark",
        hovertext="Central Fountain & University Clock Tower"
    ))

    # Add Main Gates
    fig_map.add_trace(go.Scatter(
        x=[10, 50, 95], y=[30, 90, 20],
        mode="markers+text",
        marker=dict(size=18, color="#64748B", symbol="square"),
        text=[" West Gate", " North Gate", " East Gate"],
        textposition="top center",
        name="Campus Gates",
        hovertext="Security Checkpoints and Parking"
    ))

    # Add Academic Blocks
    color_palette = ["#4F46E5", "#0284C7", "#16A34A", "#D97706", "#9333EA", "#DC2626", "#059669"]
    for i, b_row in blocks_summary.iterrows():
        b_color = color_palette[i % len(color_palette)]
        fig_map.add_trace(go.Scatter(
            x=[b_row["coord_x"]],
            y=[b_row["coord_y"]],
            mode="markers+text",
            marker=dict(size=35, color=b_color, line=dict(width=2, color="#FFFFFF")),
            text=[b_row["block_name"].split(" ")[0]],
            textposition="middle center",
            textfont=dict(color="white", size=11),
            name=b_row["block_name"],
            hovertext=f"<b>{b_row['block_name']}</b><br>Registered Rooms: {b_row['room_count']}<br>Coords: ({b_row['coord_x']}, {b_row['coord_y']})"
        ))

    fig_map.update_layout(
        title="Campus Infrastructure & Block Map",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 105]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[10, 95]),
        plot_bgcolor="#F8FAFC",
        height=520,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig_map, use_container_width=True)

# --- TAB 3: FLOOR-BY-FLOOR DIRECTORY ---
with tab_directory:
    st.subheader(" Comprehensive Block Directory")
    
    unique_blocks = rooms_df["block_name"].unique().tolist()
    sel_block = st.selectbox("Select Block to Explore:", unique_blocks)

    block_rooms = rooms_df[rooms_df["block_name"] == sel_block]
    
    floors = ["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "4th Floor"]
    for fl in floors:
        fl_rooms = block_rooms[block_rooms["floor"] == fl]
        if not fl_rooms.empty:
            st.markdown(f"####  {fl}")
            for _, r in fl_rooms.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 3, 2])
                    with c1:
                        st.markdown(f"**{r['room_number']}**")
                        st.caption(f"Category: `{r['room_type']}`")
                    with c2:
                        st.write(f" **Landmark:** {r['landmark']}")
                        st.caption(f"Capacity: {r['capacity']} seats")
                    with c3:
                        st.caption(f"Directions: {r['directions']}")

# --- TAB 4: MANAGE ROOM DIRECTORY (ADMIN ONLY) ---
with tab_manage:
    if role == "Admin":
        st.subheader(" Master Building & Room Management")
        st.write("Add new classrooms, update wayfinding directions, or configure landmarks.")

        col_a1, col_a2 = st.columns([1, 1], gap="large")

        with col_a1:
            st.markdown("#### ➕ Add New Venue Entry")
            with st.form("add_room_form", clear_on_submit=True):
                new_block = st.selectbox("Block Name:", unique_blocks + ["Block-H (New Annexe)"])
                new_room_no = st.text_input("Room Number / Label:", placeholder="e.g. Block-C 401")
                new_type = st.selectbox("Room Type:", ["Classroom", "Laboratory", "Faculty Cabin", "Seminar Hall", "Library", "Cafeteria", "Sports", "Admin"])
                new_floor = st.selectbox("Floor Level:", ["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "4th Floor"])
                new_cap = st.number_input("Seating Capacity:", min_value=5, max_value=1000, value=60)
                new_landmark = st.text_input("Nearest Landmark:", placeholder="e.g. Next to Machine Learning Lab")
                new_directions = st.text_area("Walking Directions:", placeholder="e.g. Enter Block C north entrance, take stairs to 4th floor.")
                
                c_x1, c_x2 = st.columns(2)
                with c_x1:
                    new_cx = st.number_input("Map Coordinate X (0-100):", value=65.0)
                with c_x2:
                    new_cy = st.number_input("Map Coordinate Y (0-100):", value=40.0)

                submitted_room = st.form_submit_button("Register Venue")
                if submitted_room:
                    if not new_room_no:
                        st.error("Room number is required.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO buildings_rooms (block_name, room_number, room_type, floor, capacity, landmark, directions, coord_x, coord_y)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (new_block, new_room_no, new_type, new_floor, new_cap, new_landmark, new_directions, new_cx, new_cy))
                        conn.commit()
                        st.success(f"Room '{new_room_no}' added to campus directory!")
                        st.rerun()

        with col_a2:
            st.markdown("#### ️ Remove / Delete Room Entry")
            if not rooms_df.empty:
                room_opts = {f"{r['room_number']} ({r['block_name']})": r['id'] for _, r in rooms_df.iterrows()}
                selected_del_room = st.selectbox("Select Venue to Delete:", list(room_opts.keys()))
                target_del_id = room_opts[selected_del_room]

                if st.button("Delete Room Entry", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM buildings_rooms WHERE id = ?;", (target_del_id,))
                    conn.commit()
                    st.warning("Venue entry deleted from database!")
                    st.rerun()
            else:
                st.info("No venues to delete.")
    else:
        st.info(" **Admin Access Required**")
        st.write("Switch role to **Admin** in the sidebar to register new campus venues.")

conn.close()
