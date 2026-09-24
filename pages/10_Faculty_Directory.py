"""
Campus Companion - Faculty Directory & Consultation Hours
Find professor office cabins, consultation hours, department directories,
and request academic doubt-clearing appointments.
"""

import streamlit as st
import pandas as pd
from database import get_connection, render_sidebar

# Page Configuration
st.set_page_config(
    page_title="Faculty Directory - Campus Companion",
    page_icon="👨‍🏫",
    layout="wide"
)

# Common Sidebar with Role Toggle
role = render_sidebar()
conn = get_connection()

st.title("👨‍🏫 Faculty Directory & Office Hours")
st.caption("Contact information, cabin locations, consultation hours, and academic consultation appointments.")

# Fetch Faculty Members
faculty_query = """
SELECT id, name, department, designation, email, phone, room, cabin_hours, subjects_taught
FROM faculty
ORDER BY name ASC;
"""
faculty_df = pd.read_sql_query(faculty_query, conn)

# Top Metric Banner
f1, f2, f3, f4 = st.columns(4)
with f1:
    st.metric("Total Faculty", f"{len(faculty_df)} Professors")
with f2:
    cse_prof = len(faculty_df[faculty_df["department"] == "Computer Science"])
    st.metric("Computer Science", f"{cse_prof} Professors")
with f3:
    math_ece = len(faculty_df[faculty_df["department"].isin(["Mathematics", "Electronics"])])
    st.metric("Math & Electronics", f"{math_ece} Professors")
with f4:
    st.metric("Office Consultations", "Available Weekly", delta="Check cabin hours")

st.divider()

tab_directory, tab_consult, tab_admin = st.tabs([
    "📚 Faculty Profiles",
    "📅 Request Office Consultation",
    "⚙️ Manage Faculty (Admin)"
])

# --- TAB 1: FACULTY PROFILES ---
with tab_directory:
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        dept_options = ["All Departments"] + sorted(faculty_df["department"].unique().tolist())
        sel_dept = st.selectbox("Filter Department:", dept_options)
    with col_d2:
        search_f = st.text_input("Search Faculty by Name, Cabin, or Subject:", placeholder="e.g. Sharma, Algorithms, Block-C")

    filtered_fac = faculty_df.copy()
    if sel_dept != "All Departments":
        filtered_fac = filtered_fac[filtered_fac["department"] == sel_dept]
    if search_f:
        kw = search_f.lower()
        filtered_fac = filtered_fac[
            filtered_fac["name"].str.lower().str.contains(kw) |
            filtered_fac["room"].str.lower().str.contains(kw) |
            filtered_fac["subjects_taught"].str.lower().str.contains(kw) |
            filtered_fac["designation"].str.lower().str.contains(kw)
        ]

    st.subheader(f"Showing {len(filtered_fac)} Faculty Members")

    if filtered_fac.empty:
        st.info("No faculty profiles matched your search criteria.")
    else:
        f_cols = st.columns(2, gap="large")
        for idx, prof in filtered_fac.iterrows():
            target_c = f_cols[idx % 2]
            with target_c:
                with st.container(border=True):
                    st.markdown(f"### {prof['name']}")
                    st.caption(f"**{prof['designation']}** • Dept of **{prof['department']}**")
                    st.markdown(f"📍 Cabin: **{prof['room']}**")
                    st.markdown(f"🕒 Consultation Hours: **{prof['cabin_hours']}**")
                    st.markdown(f"📖 Specializations: *{prof['subjects_taught']}*")
                    st.caption(f"✉️ [{prof['email']}](mailto:{prof['email']}) | 📞 {prof['phone']}")

# --- TAB 2: REQUEST OFFICE CONSULTATION ---
with tab_consult:
    st.subheader("📅 Schedule an Academic Consultation / Doubt Session")
    st.write("Book a 15-minute consultation slot during the faculty member's official office hours.")

    fac_map = {f"{r['name']} ({r['department']} - Cabin: {r['room']})": r['id'] for _, r in faculty_df.iterrows()}
    
    if fac_map:
        with st.form("consultation_request_form", clear_on_submit=True):
            sel_prof = st.selectbox("Select Faculty Member:", list(fac_map.keys()))
            student_roll = st.text_input("Your Roll Number:", value="2024-CS-042")
            req_topic = st.text_input("Subject / Topic for Discussion:", placeholder="e.g. Clarification regarding B-Tree rebalancing in DBMS")
            req_slot = st.selectbox("Preferred Time Slot:", ["During Next Office Hours", "After Class (Lunch Hour)", "Virtual Meeting via Google Meet"])
            req_notes = st.text_area("Detailed Query / Background Context:")

            submit_req = st.form_submit_button("Submit Consultation Request")
            if submit_req:
                if not req_topic:
                    st.error("Please provide a discussion topic.")
                else:
                    st.success(f"🎉 Consultation request forwarded to {sel_prof.split(' (')[0]}! They will confirm via institutional email.")
    else:
        st.info("No faculty profiles registered yet.")

# --- TAB 3: MANAGE FACULTY (ADMIN) ---
with tab_admin:
    if role == "Admin":
        st.subheader("⚡ Master Faculty Records Management")
        st.write("Register new faculty appointments or update cabin allocations.")

        col_add_f, col_del_f = st.columns([1, 1], gap="large")

        with col_add_f:
            st.markdown("#### ➕ Add Faculty Profile")
            with st.form("add_faculty_form", clear_on_submit=True):
                f_name = st.text_input("Full Name (with Prefix):", placeholder="e.g. Dr. Raghavendra Rao")
                f_dept = st.selectbox("Department:", ["Computer Science", "Mathematics", "Electronics", "Humanities", "Management", "Mechanical", "Civil"])
                f_desig = st.selectbox("Designation:", ["Professor", "Associate Professor", "Assistant Professor", "Professor & HOD", "Adjunct Professor"])
                f_email = st.text_input("Email:", placeholder="raghavendra.rao@campus.edu")
                f_phone = st.text_input("Phone:", value="+91 98765 43230")
                f_room = st.text_input("Cabin Location:", value="Block-C 315")
                f_hours = st.text_input("Consultation Hours:", value="Tue & Thu 2:00 PM - 4:00 PM")
                f_subjs = st.text_area("Subjects / Areas Taught:", placeholder="e.g. Distributed Computing, Cloud Systems")

                add_f_btn = st.form_submit_button("Register Faculty")
                if add_f_btn:
                    if not f_name or not f_email:
                        st.error("Name and email are required.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                        INSERT INTO faculty (name, department, designation, email, phone, room, cabin_hours, subjects_taught)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """, (f_name, f_dept, f_desig, f_email, f_phone, f_room, f_hours, f_subjs))
                        conn.commit()
                        st.success(f"Faculty member {f_name} registered successfully!")
                        st.rerun()

        with col_del_f:
            st.markdown("#### 🗑️ Delete Faculty Record")
            if not faculty_df.empty:
                del_f_map = {f"#{r['id']} {r['name']} ({r['department']})": r['id'] for _, r in faculty_df.iterrows()}
                sel_del_f = st.selectbox("Select Faculty to Remove:", list(del_f_map.keys()))
                del_target_fid = del_f_map[sel_del_f]

                if st.button("Delete Faculty Record", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM faculty WHERE id = ?;", (del_target_fid,))
                    conn.commit()
                    st.warning("Faculty member removed from directory!")
                    st.rerun()
            else:
                st.info("No faculty to delete.")
    else:
        st.info("🔒 **Admin Access Required**")
        st.write("Switch user role to **Admin** in the sidebar to add or remove faculty records.")

conn.close()
