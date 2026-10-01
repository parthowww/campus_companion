"""
Campus Companion - College Events Tracker
Upcoming campus fests, symposiums, hackathons, and sports tournaments
with live RSVP/registration, category filtering, and Admin management forms.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="College Events - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title(" Campus Events & Festivals")
st.caption("Central hub for university symposiums, hackathons, cultural festivals, and athletic tournaments.")

current_date_str = datetime.now().strftime("%Y-%m-%d")
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")

# Fetch Events
events_query = """
SELECT id, title, category, date, time, venue, organizer, description, registration_url, status, rsvp_count
FROM events
ORDER BY date ASC;
"""
events_df = pd.read_sql_query(events_query, conn)
events_df["date_obj"] = pd.to_datetime(events_df["date"])

# Top Metric Banner
e1, e2 = st.columns(2)
st.write('')
e3, e4 = st.columns(2)
with e1:
    st.metric("Total Events", f"{len(events_df)} Active")
with e2:
    tech_count = len(events_df[events_df["category"] == "Technical"])
    st.metric("Tech & Hackathons", f"{tech_count} Events")
with e3:
    cult_count = len(events_df[events_df["category"] == "Cultural"])
    st.metric("Cultural Fests", f"{cult_count} Events")
with e4:
    total_rsvps = events_df["rsvp_count"].sum()
    st.metric("Student Registrations", f"{total_rsvps} RSVPs", delta="+48 this week")

st.divider()

# Tab Navigation
tab_browse, tab_timeline, tab_admin = st.tabs([" Explore Events", " Event Calendar Visual", "⚙️ Admin Event Management"])

# --- TAB 1: EXPLORE EVENTS ---
with tab_browse:
    c_f1, c_f2 = st.columns([1, 2])
    with c_f1:
        cat_filter = st.selectbox(
            "Filter Category:",
            ["All Categories", "Technical", "Cultural", "Academic", "Sports", "Workshop"]
        )
    with c_f2:
        search_kw = st.text_input("Search Events (Keyword, Venue, Organizer):", placeholder="e.g. Hackathon, Turing Hall, Google")

    filtered_events = events_df.copy()
    if cat_filter != "All Categories":
        filtered_events = filtered_events[filtered_events["category"] == cat_filter]
    if search_kw:
        kw = search_kw.lower()
        filtered_events = filtered_events[
            filtered_events["title"].str.lower().str.contains(kw) |
            filtered_events["venue"].str.lower().str.contains(kw) |
            filtered_events["organizer"].str.lower().str.contains(kw) |
            filtered_events["description"].str.lower().str.contains(kw)
        ]

    st.subheader(f"Showing {len(filtered_events)} Events")

    if filtered_events.empty:
        st.info("No events match your search criteria.")
    else:
        for _, ev in filtered_events.iterrows():
            with st.container(border=True):
                col_info, col_action = st.columns([3, 1], gap="medium")
                with col_info:
                    st.markdown(f"### {ev['title']}")
                    st.caption(f"️ **{ev['date_obj'].strftime('%A, %d %B %Y')}** at **{ev['time']}** |  Venue: **{ev['venue']}**")
                    st.caption(f"Organized by: **{ev['organizer']}** | Category: `{ev['category']}`")
                    st.write(ev['description'])

                with col_action:
                    st.markdown(f" **{ev['rsvp_count']}** registered")
                    
                    # RSVP Button for Students & Admins
                    rsvp_key = f"rsvp_{ev['id']}"
                    if st.button("️ RSVP / Register", key=rsvp_key, use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE events SET rsvp_count = rsvp_count + 1 WHERE id = ?;", (ev["id"],))
                        conn.commit()
                        st.toast(f" Registered for {ev['title']}!")
                        st.rerun()

                    if ev["registration_url"]:
                        st.link_button(" External Portal", ev["registration_url"], use_container_width=True)

# --- TAB 2: EVENT CALENDAR VISUAL ---
with tab_timeline:
    st.subheader("Event Timeline & Distribution")
    if not events_df.empty:
        events_df["plot_size"] = events_df["rsvp_count"].apply(lambda x: max(14, int(x)))
        fig_events = px.scatter(
            events_df,
            x="date_obj",
            y="category",
            color="category",
            size="plot_size",
            hover_name="title",
            hover_data={"venue": True, "time": True, "organizer": True, "rsvp_count": True},
            title="Events by Date and Student Interest (Bubble size indicates RSVP count)"
        )
        fig_events.update_layout(
            xaxis=dict(title="Event Date"),
            yaxis=dict(title="Category"),
            height=350,
            showlegend=True
        )
        st.plotly_chart(fig_events, use_container_width=True)

# --- TAB 3: ADMIN EVENT MANAGEMENT ---
with tab_admin:
    if role == "Admin":
        st.subheader(" Master Event Operations")
        st.write("Publish new university events, modify event venues, or remove cancelled entries.")

        col_new, col_mod = st.columns([1, 1], gap="large")

        with col_new:
            st.markdown("#### ➕ Add New Event")
            with st.form("create_event_form", clear_on_submit=True):
                e_title = st.text_input("Event Title:", placeholder="e.g. AI Research Conclave")
                e_cat = st.selectbox("Category:", ["Technical", "Cultural", "Academic", "Sports", "Workshop"])
                e_date = st.date_input("Event Date:", value=today_dt.date())
                e_time = st.text_input("Time:", value="10:00 AM")
                e_venue = st.text_input("Venue:", value="Block-E Auditorium")
                e_org = st.text_input("Organizer:", value="Department of Computer Science")
                e_desc = st.text_area("Detailed Description:", placeholder="Key highlights, speakers, guidelines.")
                e_link = st.text_input("Registration URL (optional):", placeholder="https://example.com/register")

                publish_pressed = st.form_submit_button("Publish Event")
                if publish_pressed:
                    if not e_title:
                        st.error("Please enter an event title.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO events (title, category, date, time, venue, organizer, description, registration_url, status, rsvp_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Upcoming', 0);
                        """, (e_title, e_cat, e_date.strftime("%Y-%m-%d"), e_time, e_venue, e_org, e_desc, e_link))
                        conn.commit()
                        st.success(f"Event '{e_title}' published successfully!")
                        st.rerun()

        with col_mod:
            st.markdown("#### ️ Edit or Delete Event")
            if not events_df.empty:
                event_dict = {f"#{r['id']} - {r['title']} ({r['date']})": r['id'] for _, r in events_df.iterrows()}
                selected_event_label = st.selectbox("Select Event to Manage:", list(event_dict.keys()))
                del_ev_id = event_dict[selected_event_label]
                ev_to_edit = events_df[events_df["id"] == del_ev_id].iloc[0]

                with st.form("edit_event_form"):
                    st.caption(f"Editing Event #{del_ev_id}")
                    new_venue = st.text_input("Update Venue:", value=ev_to_edit["venue"])
                    new_time = st.text_input("Update Time:", value=ev_to_edit["time"])
                    new_desc = st.text_area("Update Description:", value=ev_to_edit["description"])

                    b_save, b_del = st.columns(2)
                    with b_save:
                        update_ev = st.form_submit_button("Update Event Details")
                    with b_del:
                        delete_ev = st.form_submit_button("Delete Event")

                    if update_ev:
                        cursor = conn.cursor()
                        cursor.execute("""
                        UPDATE events SET venue = ?, time = ?, description = ? WHERE id = ?;
                        """, (new_venue, new_time, new_desc, del_ev_id))
                        conn.commit()
                        st.success("Event details updated!")
                        st.rerun()

                    if delete_ev:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM events WHERE id = ?;", (del_ev_id,))
                        conn.commit()
                        st.warning("Event deleted from calendar!")
                        st.rerun()
            else:
                st.info("No events to edit.")
    else:
        st.info(" **Admin Access Required**")
        st.write("Switch user role to **Admin** in the sidebar to publish or modify campus events.")

conn.close()
