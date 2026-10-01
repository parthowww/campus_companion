"""
Campus Companion - Holiday Tracker
Upcoming holidays sorted chronologically with live countdown metrics,
month & category filtering, visual calendar timeline, and admin management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="Holiday Tracker - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title("️ Holiday Tracker & Countdown")
st.caption("Official university calendar distinguishing National Holidays and College-Specific Off Days.")

# Current Date Logic
current_date_str = date.today().strftime("%Y-%m-%d")
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")

# Fetch Holidays
holidays_query = "SELECT id, name, date, category, description FROM holidays ORDER BY date ASC;"
holidays_df = pd.read_sql_query(holidays_query, conn)
holidays_df["date_obj"] = pd.to_datetime(holidays_df["date"])
holidays_df["days_away"] = (holidays_df["date_obj"] - today_dt).dt.days
holidays_df["month_name"] = holidays_df["date_obj"].dt.strftime("%B %Y")

upcoming_df = holidays_df[holidays_df["days_away"] >= 0]
past_df = holidays_df[holidays_df["days_away"] < 0]

# --- KPI COUNTDOWN & SUMMARY METRICS ---
if not upcoming_df.empty:
    next_hol = upcoming_df.iloc[0]
    next_hol_name = next_hol["name"]
    next_hol_days = next_hol["days_away"]
    next_hol_cat = next_hol["category"]
    next_hol_date = next_hol["date_obj"].strftime("%A, %d %B %Y")
else:
    next_hol_name = "None Upcoming"
    next_hol_days = 0
    next_hol_cat = "N/A"
    next_hol_date = "N/A"

h1, h2 = st.columns(2)
st.write('')
h3, h4 = st.columns(2)
with h1:
    st.metric(
        label=f"Next Holiday: {next_hol_name[:18]}",
        value=f"{next_hol_days} Days Left",
        delta=next_hol_date
    )
with h2:
    total_upcoming = len(upcoming_df)
    st.metric("Total Upcoming Holidays", f"{total_upcoming} Days Off")
with h3:
    nat_count = len(upcoming_df[upcoming_df["category"] == "National"])
    st.metric("National Holidays", f"{nat_count} Days", delta="Gazetted")
with h4:
    coll_count = len(upcoming_df[upcoming_df["category"] == "College-Specific"])
    st.metric("College-Specific Days Off", f"{coll_count} Days", delta="Institutional")

st.divider()

# --- FILTER CONTROLS ---
col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    available_months = ["All Months"] + sorted(holidays_df["month_name"].unique().tolist(), key=lambda x: datetime.strptime(x, "%B %Y"))
    selected_month = st.selectbox("Filter by Month:", available_months)

with col_filter2:
    selected_cat = st.selectbox("Filter by Holiday Category:", ["All Categories", "National", "College-Specific"])

filtered_holidays = holidays_df.copy()
if selected_month != "All Months":
    filtered_holidays = filtered_holidays[filtered_holidays["month_name"] == selected_month]
if selected_cat != "All Categories":
    filtered_holidays = filtered_holidays[filtered_holidays["category"] == selected_cat]

tab_list, tab_visual, tab_admin = st.tabs([" Holiday Calendar Cards", " Timeline & Distribution", "⚙️ Admin Holiday Manager"])

# --- TAB 1: HOLIDAY CARDS ---
with tab_list:
    st.subheader("Scheduled Holidays & Breaks")
    if filtered_holidays.empty:
        st.info("No holidays found matching the selected filters.")
    else:
        for _, hol in filtered_holidays.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.5, 3, 1.5])
                with c1:
                    st.markdown(f"### {hol['date_obj'].strftime('%d %b %Y')}")
                    st.caption(f"️ {hol['date_obj'].strftime('%A')}")
                with c2:
                    st.markdown(f"**{hol['name']}**")
                    st.write(hol['description'] or "Official academic holiday.")
                with c3:
                    if hol['category'] == "National":
                        st.success(" National Holiday")
                    else:
                        st.info(" College-Specific")

                    if hol['days_away'] > 0:
                        st.caption(f" **In {hol['days_away']} days**")
                    elif hol['days_away'] == 0:
                        st.warning(" **Today is Holiday!**")
                    else:
                        st.caption(f"Passed ({abs(hol['days_away'])} days ago)")

# --- TAB 2: TIMELINE DISTRIBUTION ---
with tab_visual:
    st.subheader("Academic Holiday Timeline & Categorization")
    if not holidays_df.empty:
        fig_hol = px.scatter(
            holidays_df,
            x="date_obj",
            y="category",
            color="category",
            size=[20] * len(holidays_df),
            hover_name="name",
            hover_data={"description": True, "date": True, "days_away": True},
            color_discrete_map={"National": "#16A34A", "College-Specific": "#0284C7"},
            title="Distribution of Holidays across Academic Year 2026-27"
        )
        fig_hol.update_layout(
            xaxis=dict(title="Holiday Date"),
            yaxis=dict(title="Category"),
            height=320,
            showlegend=True
        )
        st.plotly_chart(fig_hol, use_container_width=True)

# --- TAB 3: ADMIN HOLIDAY MANAGER ---
with tab_admin:
    if role == "Admin":
        st.subheader(" Manage Academic Holiday List")
        st.write("Add new institute off-days or remove cancelled holidays.")

        col_add, col_del = st.columns([1, 1], gap="large")

        with col_add:
            st.markdown("#### ➕ Add New Holiday")
            with st.form("add_holiday_form", clear_on_submit=True):
                h_name = st.text_input("Holiday Name:", placeholder="e.g. Sports Day Holiday")
                h_date = st.date_input("Holiday Date:", value=today_dt.date())
                h_cat = st.selectbox("Category:", ["College-Specific", "National"])
                h_desc = st.text_area("Description / Remarks:", placeholder="e.g. College closed on account of annual celebrations.")
                
                submitted = st.form_submit_button("Publish Holiday to Calendar")
                if submitted:
                    if not h_name:
                        st.error("Please provide a holiday name.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO holidays (name, date, category, description)
                        VALUES (?, ?, ?, ?);
                        """, (h_name, h_date.strftime("%Y-%m-%d"), h_cat, h_desc))
                        conn.commit()
                        st.success(f"Holiday '{h_name}' added successfully!")
                        st.rerun()

        with col_del:
            st.markdown("#### ️ Delete Existing Holiday")
            if not holidays_df.empty:
                hol_options = {f"{h['name']} ({h['date']})": h['id'] for _, h in holidays_df.iterrows()}
                selected_hol_label = st.selectbox("Select Holiday to Delete:", list(hol_options.keys()))
                del_target_id = hol_options[selected_hol_label]

                if st.button("Delete Selected Holiday", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM holidays WHERE id = ?;", (del_target_id,))
                    conn.commit()
                    st.warning("Holiday removed from academic calendar!")
                    st.rerun()
            else:
                st.info("No holidays available to delete.")
    else:
        st.info(" **Admin Access Required**")
        st.write("Switch role to **Admin** in the sidebar to publish or remove holidays.")

conn.close()
