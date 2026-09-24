# 🎓 Campus Companion

A comprehensive **Student Command Center** built with [Streamlit](https://streamlit.io/), designed to help college students manage their academic life — all in one place.

---

## ✨ Features

| Page | Description |
|------|-------------|
| 🏠 **Home Dashboard** | KPI overview — CGPA, attendance %, pending assignments, upcoming events & notices |
| 🗓️ **Class Schedule** | Weekly timetable grid (Mon–Sat), color-coded by subject, with Admin add/edit/delete |
| 📊 **Attendance Tracker** | Live attendance % per subject, 75% cutoff analysis, and the **Bunk-o-Meter** (classes to bunk safely) |
| 🏖️ **Holidays** | Upcoming holiday countdown, month & category filtering, visual calendar timeline |
| 🗺️ **Campus Map** | Schematic 2D campus block visualizer, "Find My Class" step-by-step navigation for freshers |
| 🎪 **College Events** | Fests, symposiums, hackathons & sports tournaments with RSVP/registration |
| 🚀 **Clubs & Societies** | Discover campus clubs, register for workshops, track membership |
| 📝 **Assignments** | Deadline tracker with urgency countdown, submission notes, and grade recorder |
| 🎯 **CGPA Calculator** | SGPA progression charts, course grade manager, and target CGPA predictor |
| 📌 **Notice Board** | Official announcements, exam circulars, placement updates with pinned alerts |
| 👨‍🏫 **Faculty Directory** | Professor office locations, consultation hours, and appointment requests |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/parthowww/campus_companion.git
cd campus_companion
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [Streamlit](https://streamlit.io/) | UI framework & multi-page app |
| [SQLite](https://sqlite.org/) | Local database (`campus.db`) |
| [Pandas](https://pandas.pydata.org/) | Data querying & manipulation |
| [Plotly](https://plotly.com/) | Interactive charts & campus map |

---

## 📁 Project Structure

```
campus_companion/
├── app.py                    # Home dashboard (entry point)
├── database.py               # DB connection, helpers, sidebar renderer
├── requirements.txt          # Python dependencies
├── campus.db                 # SQLite database (pre-seeded)
└── pages/
    ├── 1_Class_Schedule.py
    ├── 2_Attendance.py
    ├── 3_Holidays.py
    ├── 4_Campus_Map.py
    ├── 5_Events.py
    ├── 6_Club_Events.py
    ├── 7_Assignments.py
    ├── 8_CGPA_Calculator.py
    ├── 9_Notice_Board.py
    └── 10_Faculty_Directory.py
```

---

## 🔐 Role System

The app supports two roles switchable via the sidebar:

- **Student** — Read-only view of all data
- **Admin** — Full CRUD access to manage schedules, events, notices, faculty records, and more

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
