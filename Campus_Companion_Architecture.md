# Campus Companion - Architecture Overview

This document explains the core technical structure of the **Campus Companion** application. You can use this guide to explain the tech stack and system design to your teacher.

The application is built using a modern, lightweight, and unified tech stack primarily driven by **Python**. It is divided into three main components: Frontend, Backend, and Database.

---

## 1. 🖥️ Frontend (User Interface)

The frontend is completely built using **Streamlit**, a Python-based framework that allows for rapid web application development without needing to write raw HTML/CSS or JavaScript.

*   **Entry Point (`app.py`)**: This is the main dashboard of the application. It provides a high-level overview (KPIs, SGPA trends, urgent notices, and today's schedule).
*   **Multi-Page Routing (`pages/` Directory)**: Streamlit automatically creates a sidebar navigation menu based on the files inside the `pages/` folder. This keeps the application modular and organized.
    *   *Examples:* `1_Class_Schedule.py`, `2_Attendance.py`, etc.
*   **Data Visualization**: The app uses **Plotly Express** and **Plotly Graph Objects** to render interactive charts, such as the SGPA trend line and the Subject-Wise Attendance bar charts.
*   **Role-Based UI**: The `render_sidebar()` function handles session state (`st.session_state["user_role"]`). The UI dynamically changes depending on whether the user is logged in as a "Student" (read-only view) or "Admin" (can add notices, update assignments, etc.).

---

## 2. ⚙️ Backend (Application Logic)

Because Streamlit is a full-stack framework, the "Backend" logic is interwoven into the Python scripts.

*   **Database Connection Manager**: The `database.py` file acts as the backend core. It contains a `get_connection()` function that opens a thread-safe connection to the SQLite database.
*   **Data Processing**: The app heavily utilizes **Pandas**. Instead of writing raw loops to process database results, SQL queries are executed directly into Pandas DataFrames using `pd.read_sql_query(query, conn)`. This allows for fast data manipulation, filtering, and passing data directly to Plotly for charting.
*   **Dynamic Time Handling**: The backend uses Python's native `datetime` library (e.g., `date.today()`) to dynamically calculate countdowns for upcoming assignments, events, and holidays based on the actual current real-world date.

---

## 3. 🗄️ Database (Data Layer)

The application uses **SQLite** (`campus.db`), a lightweight, file-based relational database. It requires no separate server to run, making the app highly portable.

### Initialization & Schema
The `init_db()` function inside `database.py` automatically creates the database and populates it with realistic mock data if it doesn't already exist. 

### Core Tables
The schema is designed to represent a complete college ecosystem:
1.  **`subjects`**: Stores course codes, names, and total credits.
2.  **`faculty`**: Stores teacher details (name, email, department).
3.  **`class_schedule`**: A relational table linking subjects and faculty to specific days of the week, times, and room numbers.
4.  **`attendance_log`**: Tracks attendance ('Present' or 'Absent') tied to a specific subject ID.
5.  **`holidays`**: Stores academic and national holidays with dates and categories.
6.  **`events` & `club_events`**: Stores campus-wide events and extracurricular club activities.
7.  **`assignments`**: Tracks coursework, status ('Pending', 'In Progress', 'Submitted', 'Graded'), due dates, and marks.
8.  **`notices`**: Stores circulars with pinning capability for urgent announcements.
9.  **`student_grades`**: Stores historical grade points and credits per semester to dynamically calculate the SGPA and CGPA.

### How it connects:
Whenever a user opens a page (e.g., Attendance), the Python script opens a connection to `campus.db`, runs a `SELECT` query to fetch the logs, closes the connection, processes the stats using Pandas, and renders the result on the Streamlit frontend.
