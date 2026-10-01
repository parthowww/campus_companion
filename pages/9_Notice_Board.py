"""
Campus Companion - Campus Notice Board & Circulars
Official college announcements, examination circulars, placement updates,
pinned alerts, with Admin posting and deletion permissions.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="Notice Board - Campus Companion",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title(" Campus Notice Board & Circulars")
st.caption("Official university circulars, examination notifications, placement drives, and administrative alerts.")

current_date_str = datetime.now().strftime("%Y-%m-%d")
today_dt = datetime.strptime(current_date_str, "%Y-%m-%d")

# Fetch Notices
notices_query = """
SELECT id, title, category, content, published_date, is_pinned, target_audience
FROM notices
ORDER BY is_pinned DESC, published_date DESC;
"""
notices_df = pd.read_sql_query(notices_query, conn)

# Top Metric Banner
n1, n2 = st.columns(2)
st.write('')
n3, n4 = st.columns(2)
with n1:
    st.metric("Total Circulars", f"{len(notices_df)} Notices")
with n2:
    pinned_count = len(notices_df[notices_df["is_pinned"] == 1])
    st.metric("Pinned Alerts", f"{pinned_count} Pinned")
with n3:
    urgent_count = len(notices_df[notices_df["category"] == "Urgent"])
    st.metric("Urgent Notices", f"{urgent_count} Active", delta="High priority", delta_color="inverse")
with n4:
    exam_count = len(notices_df[notices_df["category"].isin(["Exam", "Academic"])])
    st.metric("Exam & Academics", f"{exam_count} Circulars")

st.divider()

tab_bulletin, tab_admin = st.tabs([" Notice Bulletin", "⚙️ Admin Notice Publisher"])

# --- TAB 1: NOTICE BULLETIN ---
with tab_bulletin:
    c_f1, c_f2 = st.columns([1, 2])
    with c_f1:
        cat_choices = ["All Categories", "Urgent", "Academic", "Exam", "Placement", "Hostel", "General"]
        sel_cat = st.selectbox("Filter Category:", cat_choices)
    with c_f2:
        search_term = st.text_input("Search Notices by Keyword:", placeholder="e.g. Exam, Scholarship, Placement, Library")

    filtered_notices = notices_df.copy()
    if sel_cat != "All Categories":
        filtered_notices = filtered_notices[filtered_notices["category"] == sel_cat]
    if search_term:
        kw = search_term.lower()
        filtered_notices = filtered_notices[
            filtered_notices["title"].str.lower().str.contains(kw) |
            filtered_notices["content"].str.lower().str.contains(kw) |
            filtered_notices["target_audience"].str.lower().str.contains(kw)
        ]

    # Pinned Section (if any match)
    pinned_matches = filtered_notices[filtered_notices["is_pinned"] == 1]
    regular_matches = filtered_notices[filtered_notices["is_pinned"] == 0]

    if not pinned_matches.empty:
        st.markdown("###  Pinned High-Priority Announcements")
        for _, p_not in pinned_matches.iterrows():
            with st.container(border=True):
                p_c1, p_c2 = st.columns([3, 1])
                with p_c1:
                    st.markdown(f"####  [{p_not['category']}] {p_not['title']}")
                    st.caption(f"️ Published: **{p_not['published_date']}** |  Target: `{p_not['target_audience']}`")
                    st.write(p_not['content'])
                with p_c2:
                    st.warning(" **PINNED NOTICE**")
                    if p_not['category'] == "Urgent":
                        st.error("⚠️ Immediate Attention")

    st.markdown(f"###  General Circulars ({len(regular_matches)})")
    if regular_matches.empty and pinned_matches.empty:
        st.info("No notices match the selected criteria.")
    else:
        for _, noti in regular_matches.iterrows():
            with st.container(border=True):
                n_c1, n_c2 = st.columns([3, 1])
                with n_c1:
                    st.markdown(f"#### [{noti['category']}] {noti['title']}")
                    st.caption(f"️ Published: **{noti['published_date']}** |  Target: `{noti['target_audience']}`")
                    st.write(noti['content'])
                with n_c2:
                    if noti['category'] == 'Exam':
                        st.info(" Examination Cell")
                    elif noti['category'] == 'Placement':
                        st.success(" Placement Cell")
                    elif noti['category'] == 'Hostel':
                        st.caption(" Hostel Wardens")
                    else:
                        st.caption("️ General Admin")

# --- TAB 2: ADMIN NOTICE PUBLISHER ---
with tab_admin:
    if role == "Admin":
        st.subheader(" Master Notice Board Operations")
        st.write("Publish official notifications or retract outdated circulars.")

        col_post, col_remove = st.columns([1, 1], gap="large")

        with col_post:
            st.markdown("#### ➕ Publish New Circular")
            with st.form("publish_notice_form", clear_on_submit=True):
                new_n_title = st.text_input("Notice Title / Heading:", placeholder="e.g. Schedule for Odd Semester Practical Viva")
                new_n_cat = st.selectbox("Category:", ["Urgent", "Academic", "Exam", "Placement", "Hostel", "General"])
                new_n_target = st.text_input("Target Audience:", value="All Students")
                new_n_content = st.text_area("Official Circular Content:", height=150)
                new_n_pin = st.checkbox(" Pin to Top of Notice Board", value=False)

                publish_btn = st.form_submit_button("Broadcast Notice")
                if publish_btn:
                    if not new_n_title or not new_n_content:
                        st.error("Title and content are required.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO notices (title, category, content, published_date, is_pinned, target_audience)
                        VALUES (?, ?, ?, ?, ?, ?);
                        """, (new_n_title, new_n_cat, new_n_content, current_date_str, 1 if new_n_pin else 0, new_n_target))
                        conn.commit()
                        st.success(f"Circular '{new_n_title}' posted successfully!")
                        st.rerun()

        with col_remove:
            st.markdown("#### ️ Delete or Retract Circular")
            if not notices_df.empty:
                del_notice_map = {f"#{r['id']} - {r['title']} ({r['published_date']})": r['id'] for _, r in notices_df.iterrows()}
                sel_del_notice = st.selectbox("Select Circular to Delete:", list(del_notice_map.keys()))
                del_target_nid = del_notice_map[sel_del_notice]

                if st.button("Delete Notice", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM notices WHERE id = ?;", (del_target_nid,))
                    conn.commit()
                    st.warning("Notice retracted from board!")
                    st.rerun()
            else:
                st.info("No notices to delete.")
    else:
        st.info(" **Admin Access Required**")
        st.write("Switch user role to **Admin** in the sidebar to publish or remove official notices.")

conn.close()
