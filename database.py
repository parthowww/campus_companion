"""
Campus Companion - Database Manager & Seed Data
SQLite persistence module with full relational schema and realistic seed data.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campus.db")
_DB_INITIALIZED = False

def get_connection():
    """Returns a SQLite connection with row factory configured and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    """Initializes tables and populates seed data if empty."""
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Subjects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        credits INTEGER NOT NULL DEFAULT 4,
        semester INTEGER NOT NULL DEFAULT 5,
        color_code TEXT NOT NULL
    );
    """)

    # 2. Faculty
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        designation TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        room TEXT NOT NULL,
        cabin_hours TEXT NOT NULL,
        subjects_taught TEXT NOT NULL
    );
    """)

    # 3. Buildings & Rooms
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buildings_rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_name TEXT NOT NULL,
        room_number TEXT NOT NULL UNIQUE,
        room_type TEXT NOT NULL,
        floor TEXT NOT NULL,
        capacity INTEGER DEFAULT 60,
        landmark TEXT NOT NULL,
        directions TEXT NOT NULL,
        coord_x REAL NOT NULL,
        coord_y REAL NOT NULL
    );
    """)

    # 4. Class Schedule
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS class_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        day_of_week TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        room TEXT NOT NULL,
        faculty_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL,
        session_type TEXT DEFAULT 'Lecture'
    );
    """)

    # 5. Attendance Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        period_slot TEXT NOT NULL,
        remarks TEXT
    );
    """)

    # 6. Holidays
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT
    );
    """)

    # 7. Events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        venue TEXT NOT NULL,
        organizer TEXT NOT NULL,
        description TEXT NOT NULL,
        registration_url TEXT,
        status TEXT DEFAULT 'Upcoming',
        rsvp_count INTEGER DEFAULT 0
    );
    """)

    # 8. Clubs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clubs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        lead_name TEXT NOT NULL,
        lead_email TEXT NOT NULL,
        member_count INTEGER NOT NULL DEFAULT 50,
        meeting_room TEXT NOT NULL,
        motto TEXT
    );
    """)

    # 9. Club Events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS club_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        venue TEXT NOT NULL,
        description TEXT NOT NULL,
        rsvp_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Upcoming'
    );
    """)

    # 10. Assignments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT NOT NULL,
        max_marks INTEGER DEFAULT 100,
        status TEXT DEFAULT 'Pending',
        marks_obtained REAL,
        submission_notes TEXT
    );
    """)

    # 11. Notices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        published_date TEXT NOT NULL,
        is_pinned INTEGER DEFAULT 0,
        target_audience TEXT DEFAULT 'All Students'
    );
    """)

    # 12. Student Grades (CGPA)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        semester INTEGER NOT NULL,
        course_code TEXT NOT NULL,
        course_name TEXT NOT NULL,
        credits INTEGER NOT NULL,
        grade_letter TEXT NOT NULL,
        grade_points REAL NOT NULL
    );
    """)

    conn.commit()
    seed_data_if_needed(conn)
    _DB_INITIALIZED = True
    conn.close()

def seed_data_if_needed(conn):
    """Populates initial realistic sample dataset (15-20 rows per table) if tables are empty."""
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM subjects;")
    if cursor.fetchone()[0] > 0:
        return

    # 1. SUBJECTS (7 rows — real VIT Semester 3 curriculum)
    subjects_data = [
        ("21MAB201T", "Transforms and Boundary Value Problems", "Mathematics", 3, 3, "#2563EB"),
        ("21CSC201J", "Data Structures and Algorithms", "Computer Science", 3, 3, "#4F46E5"),
        ("21CSC202J", "Operating Systems", "Computer Science", 3, 3, "#16A34A"),
        ("21CSS201T", "Computer Organization and Architecture", "Computer Science", 3, 3, "#0D9488"),
        ("21CSC203P", "Advanced Programming Practice", "Computer Science", 3, 3, "#9333EA"),
        ("21DCS201P", "Design Thinking and Methodology", "Computer Science", 3, 3, "#D97706"),
        ("21LEM201T", "Professional Ethics", "Humanities", 3, 3, "#E11D48"),
    ]
    cursor.executemany(
        "INSERT INTO subjects (code, name, department, credits, semester, color_code) VALUES (?, ?, ?, ?, ?, ?);",
        subjects_data
    )

    # 2. FACULTY (7 rows — one per subject)
    faculty_data = [
        ("Dr. Ananya Roy", "Mathematics", "Associate Professor", "ananya.roy@campus.edu", "+91 98765 43216", "Block-A 204", "Mon & Wed 10:00 AM - 12:00 PM", "Transforms and Boundary Value Problems"),
        ("Dr. Sunita Kulkarni", "Computer Science", "Associate Professor", "sunita.kulkarni@campus.edu", "+91 98765 43213", "Block-C 310", "Wed & Fri 3:00 PM - 5:00 PM", "Data Structures and Algorithms"),
        ("Dr. Rajesh Sharma", "Computer Science", "Professor & HOD", "rajesh.sharma@campus.edu", "+91 98765 43210", "Block-C 301", "Mon & Wed 2:00 PM - 4:00 PM", "Operating Systems"),
        ("Prof. Amit Verma", "Computer Science", "Assistant Professor", "amit.verma@campus.edu", "+91 98765 43212", "Block-C 208", "Mon & Fri 11:00 AM - 1:00 PM", "Computer Organization and Architecture"),
        ("Prof. Arvind Iyer", "Computer Science", "Assistant Professor", "arvind.iyer@campus.edu", "+91 98765 43214", "Block-C 212", "Tue & Thu 3:00 PM - 5:00 PM", "Advanced Programming Practice"),
        ("Dr. Deepa Menon", "Management", "Associate Professor", "deepa.menon@campus.edu", "+91 98765 43222", "Block-D 312", "Tue & Fri 10:00 AM - 12:00 PM", "Design Thinking and Methodology"),
        ("Dr. Swati Joshi", "Humanities", "Associate Professor", "swati.joshi@campus.edu", "+91 98765 43220", "Block-D 205", "Tue & Thu 11:00 AM - 1:00 PM", "Professional Ethics"),
    ]
    cursor.executemany(
        "INSERT INTO faculty (name, department, designation, email, phone, room, cabin_hours, subjects_taught) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        faculty_data
    )

    # 3. BUILDINGS & ROOMS (18 rows)
    rooms_data = [
        ("Block-A (Sciences)", "Block-A 101", "Classroom", "Ground Floor", 80, "Opposite Central Fountain", "Enter via West Gate, Ground floor left wing", 25.0, 30.0),
        ("Block-A (Sciences)", "Block-A 204", "Faculty Cabin", "2nd Floor", 10, "Beside Seminar Hall 1", "Take staircase near West lobby to Floor 2", 25.0, 35.0),
        ("Block-A (Sciences)", "Block-A 206", "Faculty Cabin", "2nd Floor", 10, "Near Mathematics Dept Office", "Floor 2 right corridor, Room 206", 26.0, 36.0),
        ("Block-B (ECE & Labs)", "Block-B 105", "Seminar Hall", "Ground Floor", 150, "Near Robotics Workshop", "Enter Block B, straight past foyer", 45.0, 30.0),
        ("Block-B (ECE & Labs)", "Block-B 301", "Laboratory", "3rd Floor", 45, "DSP & Embedded Research Wing", "Take main elevator to 3rd floor, turn east", 45.0, 38.0),
        ("Block-B (ECE & Labs)", "Block-B 302", "Faculty Cabin", "3rd Floor", 12, "Dean ECE Cabin", "3rd floor north corridor", 46.0, 39.0),
        ("Block-C (CSE & IT)", "Block-C 102", "Laboratory", "Ground Floor", 60, "Systems Programming Lab", "Main entrance of Block C, left corridor", 65.0, 30.0),
        ("Block-C (CSE & IT)", "Block-C 204", "Classroom", "2nd Floor", 90, "Alan Turing Lecture Hall", "Take Block-C elevators to 2nd floor, turn right", 65.0, 35.0),
        ("Block-C (CSE & IT)", "Block-C 208", "Faculty Cabin", "2nd Floor", 8, "Beside Server Room", "Floor 2, middle corridor", 66.0, 36.0),
        ("Block-C (CSE & IT)", "Block-C 301", "Faculty Cabin", "3rd Floor", 15, "HOD CSE Office Suite", "Floor 3, opposite conference room", 65.0, 40.0),
        ("Block-C (CSE & IT)", "Block-C 305", "Laboratory", "3rd Floor", 70, "Advanced AI & Cloud Lab", "3rd floor west wing", 67.0, 41.0),
        ("Block-D (Admin & Humanities)", "Block-D 101", "Library", "Ground & 1st Floor", 300, "Central Campus Library", "North quadrangle main entrance", 50.0, 65.0),
        ("Block-D (Admin & Humanities)", "Block-D 202", "Admin", "2nd Floor", 40, "Registrar & Examination Cell", "Block D, 2nd floor central atrium", 50.0, 70.0),
        ("Block-D (Admin & Humanities)", "Block-D 312", "Classroom", "3rd Floor", 75, "Management Studies Room", "Take east elevator to 3rd floor", 52.0, 72.0),
        ("Block-E (Auditorium & Arts)", "Block-E 001", "Auditorium", "Ground Floor", 800, "Rabindranath Tagore Grand Audi", "South-East zone near East Gate", 80.0, 20.0),
        ("Block-E (Auditorium & Arts)", "Block-E 105", "Cafeteria", "1st Floor", 250, "Student Recreation Center & Food Court", "Above Grand Auditorium lobby", 82.0, 22.0),
        ("Block-F (Incubation & R&D)", "Block-F 101", "Laboratory", "Ground Floor", 50, "MakerSpace & 3D Printing Lab", "Behind Block C near Innovation Park", 75.0, 55.0),
        ("Block-G (Sports & Amenities)", "Block-G 104", "Health Center", "Ground Floor", 30, "Campus Clinic & First Aid", "Next to Gymnasium and Athletic Track", 20.0, 75.0),
    ]
    cursor.executemany(
        "INSERT INTO buildings_rooms (block_name, room_number, room_type, floor, capacity, landmark, directions, coord_x, coord_y) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        rooms_data
    )

    # 4. CLASS SCHEDULE — Mon–Sat timetable using subject_id 1–6
    # ID 1=Transforms(MAB), 2=DSA(CSC), 3=OS(CSC), 4=COA(CSS), 5=AdvProg(CSC), 6=DesignThinking(DCS)
    # Faculty: 1=Dr.Ananya(MAB), 2=Dr.Sunita(DSA), 3=Dr.Rajesh(OS), 4=Prof.Amit(COA), 5=Prof.Arvind(AdvProg), 6=Dr.Deepa(DesignThinking)
    # Professional Ethics (ID 7) has 0 contact hours — no schedule entries
    schedule_data = [
        # Monday — MAB + DSA + OS + AdvProg(Lab)
        (1, "Monday", "08:00 AM", "09:00 AM", "Block-A 101", 1, "Lecture"),
        (2, "Monday", "09:00 AM", "10:00 AM", "Block-C 204", 2, "Lecture"),
        (3, "Monday", "10:15 AM", "11:15 AM", "Block-C 204", 3, "Lecture"),
        (5, "Monday", "02:00 PM", "04:00 PM", "Block-C 102", 5, "Lab"),

        # Tuesday — COA + DSA(Lab) + DesignThinking
        (4, "Tuesday", "08:00 AM", "09:00 AM", "Block-C 204", 4, "Lecture"),
        (2, "Tuesday", "09:00 AM", "11:00 AM", "Block-C 305", 2, "Lab"),
        (6, "Tuesday", "11:15 AM", "12:15 PM", "Block-D 312", 6, "Lecture"),

        # Wednesday — MAB + OS + COA + DesignThinking
        (1, "Wednesday", "08:00 AM", "09:00 AM", "Block-A 101", 1, "Lecture"),
        (3, "Wednesday", "09:00 AM", "10:00 AM", "Block-C 204", 3, "Lecture"),
        (4, "Wednesday", "10:15 AM", "11:15 AM", "Block-C 204", 4, "Lecture"),
        (6, "Wednesday", "02:00 PM", "03:00 PM", "Block-D 312", 6, "Lecture"),

        # Thursday — DSA + AdvProg + OS(Lab)
        (2, "Thursday", "08:00 AM", "09:00 AM", "Block-C 204", 2, "Lecture"),
        (5, "Thursday", "09:00 AM", "10:00 AM", "Block-C 204", 5, "Lecture"),
        (3, "Thursday", "10:15 AM", "12:15 PM", "Block-C 102", 3, "Lab"),

        # Friday — MAB + COA + AdvProg
        (1, "Friday", "08:00 AM", "09:00 AM", "Block-A 101", 1, "Lecture"),
        (4, "Friday", "09:00 AM", "10:00 AM", "Block-C 204", 4, "Lecture"),
        (5, "Friday", "10:15 AM", "11:15 AM", "Block-C 204", 5, "Lecture"),

        # Saturday — DesignThinking Workshop
        (6, "Saturday", "09:30 AM", "11:30 AM", "Block-D 312", 6, "Lab"),
    ]
    cursor.executemany(
        "INSERT INTO class_schedule (subject_id, day_of_week, start_time, end_time, room, faculty_id, session_type) VALUES (?, ?, ?, ?, ?, ?, ?);",
        schedule_data
    )

    # 5. ATTENDANCE LOG — historical records using subject_id 1–6
    attendance_data = [
        # ID 1 — Transforms and Boundary Value Problems: 5 present, 1 absent → 83.3%
        (1, "2026-09-01", "Present", "08:00 AM - 09:00 AM", "Laplace transforms introduction"),
        (1, "2026-09-03", "Present", "08:00 AM - 09:00 AM", "Fourier series derivation"),
        (1, "2026-09-08", "Present", "08:00 AM - 09:00 AM", "Boundary value problems"),
        (1, "2026-09-10", "Absent",  "08:00 AM - 09:00 AM", "Medical leave"),
        (1, "2026-09-15", "Present", "08:00 AM - 09:00 AM", "Z-transforms tutorial"),
        (1, "2026-09-17", "Present", "08:00 AM - 09:00 AM", "Sturm-Liouville problems"),

        # ID 2 — Data Structures and Algorithms: 5 present, 2 absent → 71.4% (Below 75%!)
        (2, "2026-09-01", "Present", "09:00 AM - 10:00 AM", "Arrays and linked lists review"),
        (2, "2026-09-02", "Absent",  "09:00 AM - 11:00 AM", "Overslept (Lab)"),
        (2, "2026-09-08", "Present", "09:00 AM - 10:00 AM", "Binary search trees"),
        (2, "2026-09-09", "Present", "09:00 AM - 11:00 AM", "BST lab practice"),
        (2, "2026-09-15", "Absent",  "09:00 AM - 10:00 AM", "Club activity clash"),
        (2, "2026-09-16", "Present", "09:00 AM - 10:00 AM", "Graph traversals BFS/DFS"),
        (2, "2026-09-22", "Present", "09:00 AM - 11:00 AM", "Heap sort and priority queues lab"),

        # ID 3 — Operating Systems: 5 present, 0 absent → 100%
        (3, "2026-09-01", "Present", "10:15 AM - 11:15 AM", "Process concepts and PCB"),
        (3, "2026-09-03", "Present", "10:15 AM - 12:15 PM", "Fork and exec system calls lab"),
        (3, "2026-09-08", "Present", "10:15 AM - 11:15 AM", "CPU scheduling algorithms"),
        (3, "2026-09-10", "Present", "10:15 AM - 12:15 PM", "Semaphore implementation lab"),
        (3, "2026-09-15", "Present", "10:15 AM - 11:15 AM", "Virtual memory and paging"),

        # ID 4 — Computer Organization and Architecture: 4 present, 1 absent → 80%
        (4, "2026-09-01", "Present", "08:00 AM - 09:00 AM", "Number systems and Boolean algebra"),
        (4, "2026-09-03", "Present", "10:15 AM - 11:15 AM", "Combinational circuits"),
        (4, "2026-09-08", "Absent",  "08:00 AM - 09:00 AM", "Sick"),
        (4, "2026-09-10", "Present", "10:15 AM - 11:15 AM", "ALU design and data paths"),
        (4, "2026-09-15", "Present", "08:00 AM - 09:00 AM", "Pipelining and hazards"),

        # ID 5 — Advanced Programming Practice: 3 present, 1 absent → 75%
        (5, "2026-09-01", "Present", "02:00 PM - 04:00 PM", "Python OOP concepts lab"),
        (5, "2026-09-08", "Present", "09:00 AM - 10:00 AM", "File handling and exceptions"),
        (5, "2026-09-15", "Absent",  "02:00 PM - 04:00 PM", "Missed afternoon lab"),
        (5, "2026-09-22", "Present", "09:00 AM - 10:00 AM", "Recursion and backtracking"),

        # ID 6 — Design Thinking and Methodology: 4 present, 0 absent → 100%
        (6, "2026-09-02", "Present", "11:15 AM - 12:15 PM", "Empathy mapping workshop"),
        (6, "2026-09-09", "Present", "02:00 PM - 03:00 PM", "Define and ideate phases"),
        (6, "2026-09-16", "Present", "11:15 AM - 12:15 PM", "Prototyping and testing"),
        (6, "2026-09-23", "Present", "09:30 AM - 11:30 AM", "Design sprint Saturday session"),
    ]
    cursor.executemany(
        "INSERT INTO attendance_log (subject_id, date, status, period_slot, remarks) VALUES (?, ?, ?, ?, ?);",
        attendance_data
    )

    # 6. HOLIDAYS (16 rows)
    holidays_data = [
        ("Mahatma Gandhi Jayanti", "2026-10-02", "National", "Birth anniversary of Mahatma Gandhi"),
        ("Maha Navami / Dussehra", "2026-10-20", "National", "Dussehra festival celebration"),
        ("Vijaya Dashami", "2026-10-21", "National", "Victory of good over evil"),
        ("Founder's Day Off", "2026-10-28", "College-Specific", "Annual campus establishment commemoration day"),
        ("Diwali / Deepavali", "2026-11-08", "National", "Festival of lights (Deepavali holiday)"),
        ("Govardhan Puja & Bhai Dooj", "2026-11-09", "National", "Post-Diwali festive holiday"),
        ("Guru Nanak Jayanti", "2026-11-24", "National", "Birth of Guru Nanak Dev Ji"),
        ("Winter Mid-Semester Break", "2026-12-15", "College-Specific", "End of mid-term evaluation vacation"),
        ("Christmas Day", "2026-12-25", "National", "Christmas day worldwide celebration"),
        ("New Year's Day", "2027-01-01", "College-Specific", "First day of the new year"),
        ("Republic Day", "2027-01-26", "National", "Celebration of the Indian Constitution"),
        ("Campus Tech Fest Off", "2027-02-12", "College-Specific", "Post-Innovate 2027 recovery holiday"),
        ("Maha Shivratri", "2027-03-06", "National", "Holy night of Lord Shiva"),
        ("Holi Festival", "2027-03-22", "National", "Festival of vibrant colors"),
        ("Id-ul-Fitr", "2027-04-09", "National", "Islamic celebration at conclusion of Ramadan"),
        ("Dr. B.R. Ambedkar Jayanti", "2027-04-14", "National", "Commemoration of the architect of the Indian Constitution"),
    ]
    cursor.executemany(
        "INSERT INTO holidays (name, date, category, description) VALUES (?, ?, ?, ?);",
        holidays_data
    )

    # 7. EVENTS (16 rows)
    events_data = [
        ("HackCampus 2026: 36-Hr Hackathon", "Technical", "2026-10-03", "09:00 AM", "Block-C 102 & AI Lab", "Department of CSE", "National level hackathon tackling climate tech and healthcare problems.", "https://hackcampus2026.dev", "Upcoming", 142),
        ("Annual Tech Symposium 'Innovate'", "Technical", "2026-10-15", "10:00 AM", "Block-E 001 Auditorium", "Student Technical Council", "Keynotes from Google & DeepMind researchers, project exhibits, and robotics arena.", "https://campusinnovate.org", "Upcoming", 320),
        ("Alumni Mentorship Roundtables", "Academic", "2026-10-24", "02:00 PM", "Block-B 105 Seminar Hall", "Alumni Relations Cell", "Direct networking with alumni working at FAANG, Unicorn startups, and Ivy League labs.", "https://alumni.campus.edu/rsvp", "Upcoming", 85),
        ("Aura 2026: Inter-College Cultural Fest", "Cultural", "2026-11-12", "05:00 PM", "Open Air Amphitheatre", "Cultural Committee", "Battle of the Bands, Pro-Nite concert, street play competitions, and fashion showcase.", "https://aura2026.campus.edu", "Upcoming", 650),
        ("Hands-on Workshop: Deep Learning with PyTorch", "Workshop", "2026-10-10", "11:00 AM", "Block-C 305", "ACM Student Chapter", "Practical session covering CNNs, Transformers, and LLM fine-tuning techniques.", "https://acm.campus.edu/pytorch", "Upcoming", 60),
        ("Inter-Department Football Championship", "Sports", "2026-10-18", "04:30 PM", "Central Sports Ground", "Sports Council", "Knockout football tournament between CSE, ECE, Mech, and Management branches.", "", "Upcoming", 190),
        ("Guest Lecture: Quantum Algorithms", "Academic", "2026-10-08", "03:00 PM", "Block-A 101", "Dept of Mathematics & Physics", "Guest lecture by Dr. S. Ramanujan Institute on quantum supremacy and Shor's algorithm.", "", "Upcoming", 95),
        ("Campus Placement Drive: Google & Microsoft", "Academic", "2026-11-02", "08:30 AM", "Block-C Turing Hall", "Training & Placement Cell", "On-campus recruitment and pre-placement talks for final and pre-final year students.", "https://tpc.campus.edu/drive2026", "Upcoming", 410),
        ("Debate Open 2026: Parliamentary Style", "Cultural", "2026-10-29", "03:30 PM", "Block-D 202", "Literary & Debating Society", "Heated debates on AI governance, global economics, and digital surveillance.", "", "Upcoming", 70),
        ("Robotics Drone Racing League", "Technical", "2026-11-05", "01:30 PM", "Indoor Sports Arena", "Robotics Club", "FPV obstacle drone racing and obstacle navigation obstacle challenge.", "https://robotics.campus.edu/drone", "Upcoming", 130),
        ("Blood Donation & Health Checkup Camp", "Cultural", "2026-10-12", "09:30 AM", "Block-G 104 Clinic", "Rotaract Club & Red Cross", "Annual voluntary blood donation drive in collaboration with City Hospital.", "", "Upcoming", 210),
        ("VenturePitch: Campus Startup Pitch Day", "Workshop", "2026-11-18", "10:00 AM", "Block-F 101 MakerSpace", "Entrepreneurship Cell (E-Cell)", "Pitch your startup idea to angel investors with seed grants up to INR 5 Lakhs.", "https://ecell.campus.edu/pitch", "Upcoming", 115),
        ("Cybersecurity CTF: FlagHunt 2026", "Technical", "2026-10-31", "06:00 PM", "Online & Block-C 102", "GDSC & Infosec Club", "Capture-the-flag competition with cryptography, reverse engineering, and web exploits.", "https://ctf.campus.edu", "Upcoming", 175),
        ("Badminton Inter-College Open", "Sports", "2026-11-20", "09:00 AM", "Indoor Badminton Courts", "Sports Council", "Men's and Women's singles and doubles tournament.", "", "Upcoming", 80),
        ("Winter Music Symphony & Acoustica", "Cultural", "2026-12-05", "06:30 PM", "Block-E Grand Auditorium", "Music Club Symphony", "An evening of classical ragas, acoustic unplugged, and rock fusion.", "", "Upcoming", 350),
        ("Cloud DevOps Bootcamp: Kubernetes & Terraform", "Workshop", "2026-09-28", "02:00 PM", "Block-C 305", "Developer Student Club", "Industry-led masterclass on containerization, CI/CD pipelines, and cloud deployment.", "https://gdsc.campus.edu/devops", "Upcoming", 90),
    ]
    cursor.executemany(
        "INSERT INTO events (title, category, date, time, venue, organizer, description, registration_url, status, rsvp_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        events_data
    )

    # 8. CLUBS (15 rows)
    clubs_data = [
        ("Google Developer Student Club (GDSC)", "Technical", "Community for developers passionate about Google tech, web, mobile, and machine learning.", "Aarav Sharma", "aarav.gdsc@campus.edu", 280, "Block-C 102", "Learn, Build, Empower"),
        ("ACM Student Chapter", "Technical", "Premier computing society focused on algorithmic problem solving, research, and competitive coding.", "Rhea Sengupta", "rhea.acm@campus.edu", 210, "Block-C 204", "Advancing Computing as a Science"),
        ("Robotics & Automation Club", "Technical", "Building autonomous rovers, combat bots, drones, and industrial automation prototypes.", "Karthik Verma", "karthik.robo@campus.edu", 160, "Block-F 101", "Innovate Beyond Limits"),
        ("Entrepreneurship Cell (E-Cell)", "Management", "Fostering the spirit of startup innovation, venture capital, and entrepreneurial leadership.", "Siddharth Jain", "sid.ecell@campus.edu", 195, "Block-F MakerSpace", "Igniting Enterprise"),
        ("Infosec & Cyber Defense Club", "Technical", "Ethical hacking, binary exploitation, network defense, and CTF competitions.", "Tanvi Kulkarni", "tanvi.infosec@campus.edu", 130, "Block-C 305", "Securing Cyberspace"),
        ("Symphony: The Music Society", "Cultural", "Campus band, classical vocals, choir, instrumentalists, and acoustic ensembles.", "Aditya Nair", "aditya.music@campus.edu", 140, "Block-E 105", "Harmonizing Souls"),
        ("Dramatics Club (Natya)", "Cultural", "Street plays, stage theater, mono-acting, scripting, and production.", "Meera Joshi", "meera.drama@campus.edu", 115, "Block-E Auditorium", "All the World's a Stage"),
        ("Choreography Society (Footloose)", "Cultural", "Contemporary, hip-hop, western freestyle, and traditional Indian dance forms.", "Pooja Hegde", "pooja.dance@campus.edu", 125, "Block-E Dance Studio", "Express Through Motion"),
        ("Literary & Debating Society", "Cultural", "Parliamentary debating, elocution, creative writing, poetry slams, and book reviews.", "Kabir Ghosh", "kabir.lit@campus.edu", 150, "Block-D 101 Library", "Words That Ignite Minds"),
        ("Shutterbugs: Photography Club", "Arts", "Visual storytelling, photo-walks, digital darkroom editing, and campus media coverage.", "Devansh Patel", "devansh.photo@campus.edu", 95, "Block-D Media Lab", "Capturing Moments Forever"),
        ("Rotaract Youth Club", "Social", "Community upliftment, health drives, environmental cleanup, and literacy campaigns.", "Ananya Rao", "ananya.rotaract@campus.edu", 220, "Block-D 202", "Fellowship Through Service"),
        ("Green Earth & Eco Club", "Social", "Campus sustainability, tree planting, electronic waste recycling, and solar awareness.", "Tanya Biswas", "tanya.eco@campus.edu", 110, "Block-A Botanical Garden", "Think Green, Live Clean"),
        ("Astronomy & Space Society", "Technical", "Stargazing nights, telescope workshops, astrophotography, and cosmology seminars.", "Nikhil Saxena", "nikhil.astro@campus.edu", 85, "Block-A Observatory Roof", "Exploring the Cosmos"),
        ("Gaming & Esports Guild", "Technical", "Competitive esports tournaments in Valorant, CS2, Rocket League, and game dev workshops.", "Varun Mehta", "varun.esports@campus.edu", 175, "Block-C 301", "Play to Win"),
        ("Sports & Fitness Club", "Sports", "Organizing inter-college athletics, basketball, cricket, badminton, and wellness marathons.", "Rohan Choudhury", "rohan.sports@campus.edu", 260, "Block-G Sports Complex", "Strength, Speed, Spirit"),
    ]
    cursor.executemany(
        "INSERT INTO clubs (name, category, description, lead_name, lead_email, member_count, meeting_room, motto) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        clubs_data
    )

    # 9. CLUB EVENTS (16 rows)
    club_events_data = [
        (1, "Cloud Study Jam: Google Cloud Arcade", "2026-09-30", "04:30 PM", "Block-C 102", "Hands-on labs on Google Cloud Skills Boost with badges and swag.", 95, "Upcoming"),
        (2, "CodeWars: Competitive Programming Contest", "2026-10-06", "05:00 PM", "Online (Codeforces)", "2-hour sprint contest covering graphs, math, and dynamic programming.", 120, "Upcoming"),
        (3, "Combat Robotics 101: Chassis Design", "2026-10-09", "03:00 PM", "Block-F 101", "Learn CAD modeling and brushless motor electronics for 15kg combat bots.", 48, "Upcoming"),
        (4, "Founder Stories: From Dorm to Seed Round", "2026-10-14", "04:00 PM", "Block-B 105", "Interactive fireside chat with an alumnus who raised $1.5M in seed funding.", 80, "Upcoming"),
        (5, "Bug Bounty Hunting for Beginners", "2026-10-17", "05:30 PM", "Block-C 305", "Introduction to OWASP Top 10 vulnerabilities and ethical bug disclosures.", 65, "Upcoming"),
        (6, "Unplugged Acoustic Jam Session", "2026-10-04", "05:00 PM", "Open Air Theatre Steps", "Bring your acoustic guitars, cajons, or come sing along under the twilight.", 110, "Upcoming"),
        (7, "Street Play Street-Out: Cyberbullying Awareness", "2026-10-11", "01:15 PM", "Block-E Lawn", "High energy nukkad natak performed during lunch break.", 140, "Upcoming"),
        (8, "Urban Hip-Hop Dance Workshop", "2026-10-19", "04:30 PM", "Block-E Dance Hall", "Special masterclass by national breakdancing champions.", 55, "Upcoming"),
        (9, "Fresher's Parliamentary Debate Tournament", "2026-10-05", "03:00 PM", "Block-D 101", "Friendly debate tournament strictly for 1st and 2nd year students.", 42, "Upcoming"),
        (10, "Golden Hour Campus Photowalk", "2026-10-07", "04:45 PM", "Campus Clock Tower", "Learn composition, shutter speed tricks, and street portraiture.", 35, "Upcoming"),
        (11, "Old Clothes & Book Donation Drive", "2026-10-16", "10:00 AM", "Block-D Foyer", "Collecting textbooks, stationery, and winter clothes for orphanage drive.", 90, "Upcoming"),
        (12, "Campus Green Clean & Plantation Drive", "2026-10-23", "08:00 AM", "North Gate Grounds", "Planting 100 indigenous saplings along the campus athletic boundary.", 75, "Upcoming"),
        (13, "Supermoon Stargazing & Planet Watch", "2026-10-26", "07:30 PM", "Block-A Terrace", "Viewing Saturn's rings and lunar craters via 8-inch Dobsonian telescope.", 130, "Upcoming"),
        (14, "Valorant Campus LAN Showdown", "2026-10-27", "11:00 AM", "Block-C 102", "5v5 custom lobby tournament with hyper-low latency local server setup.", 88, "Upcoming"),
        (15, "Midnight Neon Marathon (5 KM)", "2026-11-06", "09:00 PM", "Sports Complex Track", "Glow-in-the-dark campus run promoting mental wellness and fitness.", 230, "Upcoming"),
        (1, "Flutter UI Sprint: Build a Mobile App in 3 Hours", "2026-10-22", "02:00 PM", "Block-C 305", "Step-by-step cross-platform mobile app development hands-on tutorial.", 70, "Upcoming"),
    ]
    cursor.executemany(
        "INSERT INTO club_events (club_id, title, date, time, venue, description, rsvp_count, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        club_events_data
    )

    # 10. ASSIGNMENTS — using subject_id 1–7 (Professional Ethics = ID 7, assignment-only)
    assignments_data = [
        # Pending / In Progress
        (2, "Implement AVL Tree with Rotations", "Code a self-balancing AVL tree with insert, delete, and search. Plot rotation counts.", "2026-09-28", 100, "Pending", None, "Submit C++/Python source with test cases."),
        (3, "CPU Scheduler Simulator (RR, SJF, Priority)", "Simulate scheduling algorithms and measure turnaround and waiting times.", "2026-10-02", 100, "In Progress", None, "Plot Gantt charts and average waiting times."),
        (1, "Laplace Transform Problem Set", "Solve 20 problems on Laplace, Inverse Laplace, and convolution theorem applications.", "2026-10-05", 50, "Pending", None, "Show all working steps clearly."),
        (4, "Design a 4-bit ALU Circuit", "Implement ADD, SUB, AND, OR operations using logic gates. Verify using truth tables.", "2026-10-08", 50, "Pending", None, "Draw circuit diagram and test with Logisim."),
        (5, "Mini Project: Student Grade Calculator", "Build a CLI-based grade calculator in Python with file persistence and error handling.", "2026-10-12", 100, "In Progress", None, "Submit code + README with usage instructions."),
        (6, "Design Thinking Case Study: Smart Campus", "Apply all 5 stages of design thinking to propose a smart campus solution.", "2026-10-15", 50, "Pending", None, "10-slide presentation + 2-page written report."),
        (7, "Essay: Ethics in AI Decision Making", "Analyze real-world examples of AI bias and propose ethical frameworks.", "2026-10-20", 30, "Pending", None, "1500 words, Harvard referencing."),
        (2, "Graph Algorithms: Dijkstra & Bellman-Ford", "Implement shortest path algorithms and compare performance on dense vs sparse graphs.", "2026-10-10", 100, "Pending", None, "Include time complexity analysis."),
        # Submitted / Graded
        (1, "Fourier Series Convergence Analysis", "Analyze convergence of Fourier series for piecewise functions.", "2026-09-12", 50, "Graded", 46.0, "Well-structured proofs. Excellent convergence discussion."),
        (2, "Linked List & Stack Implementation", "Implement singly linked list and stack with all operations in C.", "2026-09-15", 50, "Submitted", 48.0, "Submitted on time. Clean code with comments."),
        (3, "POSIX Thread Synchronization with Semaphores", "Implement producer-consumer problem and dining philosophers without deadlock.", "2026-09-18", 50, "Graded", 45.0, "Tested with 10 concurrent threads successfully."),
        (4, "Boolean Algebra Simplification Lab", "Simplify 15 Boolean expressions using K-map and verify with gates.", "2026-09-20", 40, "Submitted", 38.0, "All K-maps correct. Minor gate count issue."),
        (5, "File Encryption using XOR Cipher", "Implement file-level encryption and decryption using XOR in Python.", "2026-09-22", 60, "Graded", 57.0, "Excellent implementation. Well-documented code."),
    ]
    cursor.executemany(
        "INSERT INTO assignments (subject_id, title, description, due_date, max_marks, status, marks_obtained, submission_notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        assignments_data
    )

    # 11. NOTICES (16 rows)
    notices_data = [
        ("URGENT: Mid-Semester Examination Schedule Announced", "Exam", "Mid-term examinations for 3rd, 5th, and 7th semester students will commence from October 14, 2026. Hall tickets can be downloaded from the university portal starting Oct 5. Strictly no electronic devices inside examination halls.", "2026-09-22", 1, "All UG & PG Students"),
        ("Library Extended Night Hours for Exam Preparation", "Academic", "Starting October 1, 2026, Central Library (Block-D) will remain open 24x7 with high-speed Wi-Fi, silent study cubes, and cafeteria services on the first floor.", "2026-09-21", 1, "All Students"),
        ("Campus Placement: Registration Open for Phase 1 Drives", "Placement", "Pre-final and final year students with CGPA >= 7.0 and zero active backlogs must complete mandatory company registrations by September 30, 2026. Upload verified resumes to the TPC portal.", "2026-09-20", 1, "3rd & 4th Year Students"),
        ("Hostel Curfew & Late Entry Regulations Update", "Hostel", "Hostel gates will close promptly at 10:30 PM on weekdays and 11:00 PM on weekends. Any late entry requires prior written permission from the Chief Warden via student portal.", "2026-09-19", 0, "Hostel Residents"),
        ("Annual Convocation Ceremony Regalia Notice", "Academic", "The 18th Annual Convocation will be held on November 28, 2026 at Tagore Grand Auditorium. Graduating students must register for academic regalia by October 25.", "2026-09-18", 0, "Graduating Batch"),
        ("Merit & Means Scholarship 2026-27 Applications", "General", "Applications are invited for the National & Institutional Merit Scholarships. Eligible students with family income under 6 LPA can apply at Room 202, Block D.", "2026-09-17", 0, "All Students"),
        ("Campus Wi-Fi Maintenance & Certificate Upgrade", "Urgent", "Campus-wide IT network will undergo routine security patching on Saturday, Sep 26 between 01:00 AM - 05:00 AM. Intermittent internet outage expected.", "2026-09-16", 0, "All Campus"),
        ("Course Drop and Elective Change Deadline", "Academic", "The last date to request a change of open elective courses for the ongoing semester is September 28, 2026. Submit signed forms to the respective department head.", "2026-09-15", 0, "5th Semester Students"),
        ("Inter-College Sports Meet: Athlete Selections", "General", "Trials for Basketball, Volleyball, Track & Field, and Chess teams begin next Monday at the Sports Complex. Bring medical fitness certificate.", "2026-09-14", 0, "Sports Enthusiasts"),
        ("Call for Student Volunteers: Innovate 2026", "General", "Technical Council invites applications for core team and volunteers across Logistics, Web, PR, and Stage Management for Innovate 2026 fest.", "2026-09-13", 0, "1st to 3rd Year Students"),
        ("IEEE & ACM Student Memberships Subsidy", "Academic", "College is offering a 50% tuition subsidy on student professional memberships in IEEE and ACM. Contact Dr. Priya Nambiar in Block C-304.", "2026-09-12", 0, "Engineering Students"),
        ("Health Center Free Dental & Vision Screening", "General", "A two-day health camp with specialized dentists and ophthalmologists will be stationed at Block G Clinic on October 5-6.", "2026-09-11", 0, "All Students & Staff"),
        ("Cafeteria Hygiene & Menu Revision Feedback", "General", "Students can submit menu suggestions and rate food quality through the student union feedback portal before September 30.", "2026-09-10", 0, "All Students"),
        ("Mandatory Cyber Security Awareness Briefing", "Urgent", "Beware of phishing emails claiming to be from the registrar or examination board. The college never asks for passwords or UPI payments via SMS.", "2026-09-08", 0, "All Students & Staff"),
        ("Parking Regulations inside Campus West Gate", "General", "Two-wheeler and four-wheeler vehicles must display the 2026 campus RFID tag. Parking in non-designated zones in front of Block C will incur fines.", "2026-09-05", 0, "Commuter Students"),
        ("Student Research Grant 2026 Results Announced", "Academic", "Dean of R&D is delighted to announce 12 undergraduate project grants sanctioned for IoT, Clean Energy, and Generative AI research.", "2026-09-01", 0, "All Students"),
    ]
    cursor.executemany(
        "INSERT INTO notices (title, category, content, published_date, is_pinned, target_audience) VALUES (?, ?, ?, ?, ?, ?);",
        notices_data
    )

    # 12. STUDENT GRADES (16 rows across Semesters 1 to 4 to establish realistic CGPA)
    # CGPA calculation: sum(credits * grade_points) / sum(credits)
    grades_data = [
        # Semester 1 (Total Credits: 20, SGPA: 8.65)
        (1, "MA101", "Calculus & Linear Algebra", 4, "A+", 9.0),
        (1, "PH101", "Engineering Physics", 4, "A", 8.0),
        (1, "CS101", "Problem Solving & C Programming", 4, "O", 10.0),
        (1, "ME101", "Engineering Graphics & Design", 3, "B+", 7.0),
        (1, "HS101", "Communicative English", 3, "A+", 9.0),
        (1, "CS102", "Computing Lab I", 2, "O", 10.0),

        # Semester 2 (Total Credits: 21, SGPA: 8.52)
        (2, "MA102", "Differential Equations & Transforms", 4, "A", 8.0),
        (2, "CH101", "Engineering Chemistry", 4, "A+", 9.0),
        (2, "CS103", "Data Structures & Fundamentals", 4, "O", 10.0),
        (2, "EE101", "Basic Electrical Engineering", 3, "B+", 7.0),
        (2, "CS104", "Data Structures Lab", 2, "O", 10.0),
        (2, "EV101", "Environmental Studies", 2, "A", 8.0),
        (2, "ME102", "Workshop Practices", 2, "A+", 9.0),

        # Semester 3 (Total Credits: 20, SGPA: 8.70)
        (3, "CS201", "Object Oriented Programming (Java/C++)", 4, "O", 10.0),
        (3, "CS202", "Digital Logic & Computer Organization", 4, "A+", 9.0),
        (3, "MA201", "Discrete Mathematical Structures", 4, "A", 8.0),
        (3, "CS203", "Data Communications", 3, "A", 8.0),
        (3, "CS204", "OOP & System Lab", 2, "O", 10.0),
        (3, "HS201", "Universal Human Values", 3, "A+", 9.0),

        # Semester 4 (Total Credits: 20, SGPA: 8.85)
        (4, "CS205", "Theory of Computation", 4, "A+", 9.0),
        (4, "CS206", "Microprocessor Systems", 4, "A", 8.0),
        (4, "CS207", "Principles of Programming Languages", 3, "O", 10.0),
        (4, "MA202", "Probability & Random Processes", 4, "A+", 9.0),
        (4, "CS208", "Hardware & Microprocessor Lab", 2, "O", 10.0),
        (4, "MG201", "Industrial Economics & Management", 3, "A", 8.0),
    ]
    cursor.executemany(
        "INSERT INTO student_grades (semester, course_code, course_name, credits, grade_letter, grade_points) VALUES (?, ?, ?, ?, ?, ?);",
        grades_data
    )

    conn.commit()

# Run database setup immediately on module load
init_db()

# Subject Color Palette Helper
SUBJECT_COLORS = [
    "#4F46E5", "#0284C7", "#0D9488", "#16A34A", "#E11D48", 
    "#9333EA", "#D97706", "#DC2626", "#4338CA", "#2563EB", 
    "#0891B2", "#EA580C", "#CA8A04", "#65A30D", "#059669", "#C026D3"
]

def get_subject_color(subject_name: str) -> str:
    """Generates a stable color from subject name hash."""
    if not subject_name:
        return "#64748B"
    hash_val = sum(ord(c) for c in subject_name)
    return SUBJECT_COLORS[hash_val % len(SUBJECT_COLORS)]

def render_sidebar():
    """Renders the common sidebar role toggle and quick info across all pages."""
    import streamlit as st
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "Student"
    
    st.sidebar.subheader(" Campus Companion")
    st.sidebar.caption("Integrated Student Portal & ERP")
    
    current_idx = 0 if st.session_state["user_role"] == "Student" else 1
    role = st.sidebar.selectbox(
        "Switch User Role:",
        ["Student", "Admin"],
        index=current_idx,
        key="app_user_role_dropdown",
        help="Admin unlocks add/edit/delete forms across events, clubs, notices, and schedules."
    )
    st.session_state["user_role"] = role
    
    if role == "Admin":
        st.sidebar.warning(" **Admin Mode Active**\n\nFull administrative permissions granted to post circulars, schedule classes, add holidays, and organize events.")
    else:
        st.sidebar.info(" **Student Mode Active**\n\nAccess personal attendance logging, grade forecasting, assignment submissions, and class schedules.")
    
    st.sidebar.divider()
    st.sidebar.caption("Current Semester: **3rd Sem (Odd 2026)**")
    st.sidebar.caption("Roll No: **2024-CS-042**")
    st.sidebar.divider()
    return role

