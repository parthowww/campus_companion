# 🐛 Bugs Fixed & Updates

This document tracks the recent bug fixes, security patches, and architectural improvements made to **Campus Companion**.

## 🚀 Recent Updates

### 1. Implemented Strict Login Wall & Authentication Routing
- **Issue:** Users could previously access the dashboard and inner pages without explicitly logging in, and role switching was done via a simple unauthenticated dropdown in the sidebar.
- **Fix:** Introduced a strict "Login Wall" in the `render_sidebar()` function. If a user is not authenticated (`is_auth_user == False`), the sidebar navigation is hidden via CSS, and all page execution is halted (`st.stop()`) until the user authenticates through the central landing page portals.

### 2. Fixed Privilege Escalation in Student Portal
- **Issue:** The Student portal previously exposed Admin-level CRUD operations. Students could see tabs to "Add New Assignment", "Manage Classes", "Admin Holiday Manager", and more.
- **Fix:** Refactored the tab rendering logic across all 10 pages in the `pages/` directory. Admin tabs are now conditionally injected only if `role == 'Admin'`. For students, the tabs simply do not exist.

### 3. Patched Self-Grading & Deletion Exploit in Assignments
- **Issue:** In the "Update Status & Submit" tab of `pages/7_Assignments.py`, students had access to the "Marks Obtained" input and the "Delete Selected Assignment" button, allowing them to grade their own assignments or delete them entirely.
- **Fix:** 
  - Restrained the `Marks Obtained` number input inside an `if role == 'Admin':` check. Students now see a read-only metric of their grade.
  - Wrapped the assignment deletion expander in an `if role == 'Admin':` check to prevent unauthorized data destruction.
  - Restricted the assignment status dropdown so students can only mark tasks as "Pending", "In Progress", or "Submitted". Only Admins can set the status to "Graded".

### 4. Busted Session State Caching
- **Issue:** Streamlit was aggressively caching the `logged_in` variable, causing users to bypass the new login wall upon page refresh.
- **Fix:** Renamed the session authentication variable to `is_auth_user` to forcefully invalidate all old cached sessions and require a fresh login for all users.
