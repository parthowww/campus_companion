"""
Campus Companion - Clubs & Societies Portal
Discover active campus clubs, register for club workshops & hackathons,
track membership, and manage club events (Admin unlocked).
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="Clubs & Societies - Campus Companion",
    page_icon="🚀",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title("🚀 Student Clubs & Societies")
st.caption("Explore student-led communities, register for technical workshops, cultural jams, and leadership activities.")

current_date_str = "2026-09-24"
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")

# Fetch Clubs and Club Events
clubs_query = "SELECT id, name, category, description, lead_name, lead_email, member_count, meeting_room, motto FROM clubs ORDER BY name ASC;"
clubs_df = pd.read_sql_query(clubs_query, conn)

club_events_query = """
SELECT 
    ce.id, ce.club_id, ce.title, ce.date, ce.time, ce.venue, ce.description, ce.rsvp_count, ce.status,
    c.name AS club_name, c.category AS club_category
FROM club_events ce
JOIN clubs c ON ce.club_id = c.id
ORDER BY ce.date ASC;
"""
club_events_df = pd.read_sql_query(club_events_query, conn)
club_events_df["date_obj"] = pd.to_datetime(club_events_df["date"])

# Top Metric Banner
cl1, cl2, cl3, cl4 = st.columns(4)
with cl1:
    st.metric("Chartered Clubs", f"{len(clubs_df)} Societies")
with cl2:
    total_members = clubs_df["member_count"].sum()
    st.metric("Total Active Members", f"{total_members:,} Students")
with cl3:
    st.metric("Upcoming Club Sessions", f"{len(club_events_df)} Workshops")
with cl4:
    club_rsvps = club_events_df["rsvp_count"].sum()
    st.metric("Event RSVPs", f"{club_rsvps} Registrations")

st.divider()

tab_events, tab_directory, tab_manage = st.tabs([
    "📅 Club Events & Workshops",
    "🏛️ Societies Directory",
    "⚙️ Admin Club Manager"
])

# --- TAB 1: CLUB EVENTS & WORKSHOPS ---
with tab_events:
    st.subheader("Upcoming Club Activities & Workshops")

    col_cf1, col_cf2 = st.columns([1, 1])
    with col_cf1:
        club_filter = st.selectbox(
            "Filter by Organizing Club:",
            ["All Clubs"] + sorted(clubs_df["name"].tolist())
        )
    with col_cf2:
        search_cev = st.text_input("Search Club Event:", placeholder="e.g. Flutter, Stargazing, Acoustic")

    filtered_cev = club_events_df.copy()
    if club_filter != "All Clubs":
        filtered_cev = filtered_cev[filtered_cev["club_name"] == club_filter]
    if search_cev:
        kw = search_cev.lower()
        filtered_cev = filtered_cev[
            filtered_cev["title"].str.lower().str.contains(kw) |
            filtered_cev["description"].str.lower().str.contains(kw) |
            filtered_cev["venue"].str.lower().str.contains(kw)
        ]

    st.write(f"Showing **{len(filtered_cev)}** scheduled club activities:")

    if filtered_cev.empty:
        st.info("No club events match the selected criteria.")
    else:
        for _, cev in filtered_cev.iterrows():
            with st.container(border=True):
                c_main, c_act = st.columns([3, 1], gap="medium")
                with c_main:
                    st.markdown(f"### {cev['title']}")
                    st.caption(f"🎪 Organized by **{cev['club_name']}** (`{cev['club_category']}`)")
                    st.caption(f"🗓️ **{cev['date_obj'].strftime('%A, %d %B %Y')}** at **{cev['time']}** | 📍 Venue: **{cev['venue']}**")
                    st.write(cev["description"])
                with c_act:
                    st.metric("Interested / RSVP", f"{cev['rsvp_count']} Students")
                    btn_key = f"rsvp_cev_{cev['id']}"
                    if st.button("🙋 RSVP for Workshop", key=btn_key, use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE club_events SET rsvp_count = rsvp_count + 1 WHERE id = ?;", (cev["id"],))
                        conn.commit()
                        st.toast(f"RSVP recorded for {cev['title']}!")
                        st.rerun()

# --- TAB 2: SOCIETIES DIRECTORY ---
with tab_directory:
    st.subheader("Official Campus Clubs & Student Societies")
    
    cat_choices = ["All Categories"] + sorted(clubs_df["category"].unique().tolist())
    sel_club_cat = st.selectbox("Filter by Domain:", cat_choices)

    filtered_clubs = clubs_df.copy()
    if sel_club_cat != "All Categories":
        filtered_clubs = filtered_clubs[filtered_clubs["category"] == sel_club_cat]

    cols = st.columns(2, gap="large")
    for idx, cl in filtered_clubs.iterrows():
        target_col = cols[idx % 2]
        with target_col:
            with st.container(border=True):
                st.markdown(f"### {cl['name']}")
                if cl['motto']:
                    st.caption(f"*“{cl['motto']}”*")
                st.markdown(f"Category: `{cl['category']}` | 👥 Members: **{cl['member_count']}**")
                st.write(cl['description'])
                st.write(f"👤 **Student Lead:** {cl['lead_name']} ([{cl['lead_email']}](mailto:{cl['lead_email']}))")
                st.caption(f"📍 Regular Meets: **{cl['meeting_room']}**")
                
                # Interactive Join Interest
                join_key = f"join_club_{cl['id']}"
                if st.button("🤝 Join Society", key=join_key):
                    st.toast(f"Application sent to {cl['lead_name']} ({cl['name']})!")

# --- TAB 3: ADMIN CLUB MANAGER ---
with tab_manage:
    if role == "Admin":
        st.subheader("⚡ Master Club & Event Controls")
        st.write("Publish new club workshops, schedule meetups, or charter new campus societies.")

        col_ev_admin, col_cl_admin = st.columns([1, 1], gap="large")

        with col_ev_admin:
            st.markdown("#### ➕ Add New Club Event")
            with st.form("add_club_event_form", clear_on_submit=True):
                club_map = {c["name"]: c["id"] for _, c in clubs_df.iterrows()}
                chosen_club = st.selectbox("Organizing Club:", list(club_map.keys()))
                ev_title = st.text_input("Activity / Workshop Title:", placeholder="e.g. Next.js Fullstack Workshop")
                ev_date = st.date_input("Event Date:", value=today_dt.date())
                ev_time = st.text_input("Time:", value="05:00 PM")
                ev_venue = st.text_input("Venue / Room:", value="Block-C 102")
                ev_desc = st.text_area("Event Description:", placeholder="Agenda, prerequisites, laptops needed.")

                submit_club_ev = st.form_submit_button("Publish Club Event")
                if submit_club_ev:
                    if not ev_title:
                        st.error("Please provide a title.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO club_events (club_id, title, date, time, venue, description, rsvp_count, status)
                        VALUES (?, ?, ?, ?, ?, ?, 0, 'Upcoming');
                        """, (club_map[chosen_club], ev_title, ev_date.strftime("%Y-%m-%d"), ev_time, ev_venue, ev_desc))
                        conn.commit()
                        st.success("Club event published successfully!")
                        st.rerun()

        with col_cl_admin:
            st.markdown("#### 🏛️ Charter New Student Club")
            with st.form("charter_club_form", clear_on_submit=True):
                new_c_name = st.text_input("Society / Club Name:", placeholder="e.g. Blockchain & Web3 Guild")
                new_c_cat = st.selectbox("Category:", ["Technical", "Cultural", "Sports", "Social", "Management", "Arts"])
                new_c_motto = st.text_input("Motto / Tagline:", placeholder="e.g. Decentralizing the Future")
                new_c_desc = st.text_area("Club Mission & Objectives:")
                new_c_lead = st.text_input("Student Lead Name:", placeholder="e.g. Rohan Verma")
                new_c_email = st.text_input("Lead Email:", placeholder="rohan.lead@campus.edu")
                new_c_room = st.text_input("Allocated Room:", value="Block-F 101")
                new_c_members = st.number_input("Founding Members Count:", min_value=5, value=25)

                charter_btn = st.form_submit_button("Charter Club")
                if charter_btn:
                    if not new_c_name:
                        st.error("Club name is required.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO clubs (name, category, description, lead_name, lead_email, member_count, meeting_room, motto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """, (new_c_name, new_c_cat, new_c_desc, new_c_lead, new_c_email, new_c_members, new_c_room, new_c_motto))
                        conn.commit()
                        st.success(f"Club '{new_c_name}' successfully chartered!")
                        st.rerun()

            st.write("")
            st.markdown("#### 🗑️ Delete Existing Club Event")
            if not club_events_df.empty:
                del_opts = {f"#{r['id']} {r['title']} ({r['club_name']})": r['id'] for _, r in club_events_df.iterrows()}
                sel_del_ev = st.selectbox("Select Activity to Remove:", list(del_opts.keys()))
                del_target_id = del_opts[sel_del_ev]

                if st.button("Delete Club Event", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM club_events WHERE id = ?;", (del_target_id,))
                    conn.commit()
                    st.warning("Club activity deleted!")
                    st.rerun()
    else:
        st.info("🔒 **Admin Access Required**")
        st.write("Switch user role to **Admin** in the sidebar to publish club workshops or charter societies.")

conn.close()
