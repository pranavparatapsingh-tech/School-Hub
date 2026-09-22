import os
import sqlite3
import json
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cyber_study_hub_ultra_secure_key_2026'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}
OWNER_PASSWORD = 'owner123'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_FILE = 'cyber_study.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT status FROM meetings LIMIT 1")
    except sqlite3.OperationalError:
        conn.close()
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            target_class TEXT DEFAULT 'All',
            attachments TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_ips (
            ip TEXT PRIMARY KEY,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            user_agent TEXT,
            visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class_level TEXT NOT NULL,
            subject TEXT NOT NULL,
            material_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_level TEXT NOT NULL,
            subject TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            explanation TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class_level TEXT NOT NULL,
            subject TEXT NOT NULL,
            meeting_url TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            status TEXT DEFAULT '🟢 LIVE / ATTENDABLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM notes')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO notes (title, content, target_class, attachments) VALUES (?, ?, ?, ?)', 
                       ('System Online', 'Welcome to Cyber Study Hub Command Center.', 'All', '[]'))
    
    cursor.execute('SELECT COUNT(*) FROM quizzes')
    if cursor.fetchone()[0] == 0:
        sample_questions = [
            ('Class 10', 'Science', 'Easy', 'Which gas is evolved when dilute hydrochloric acid reacts with active metals?', 'Hydrogen', 'Oxygen', 'Carbon Dioxide', 'Nitrogen', 'A', 'Metals produce salt + hydrogen gas with acids.'),
            ('Class 12', 'Physics', 'Medium', 'SI Unit of Electric Flux:', 'N m^2 C^-1', 'Volt', 'Tesla', 'Ampere', 'A', 'N m^2 C^-1')
        ]
        cursor.executemany('''
            INSERT INTO quizzes (class_level, subject, difficulty, question, option_a, option_b, option_c, option_d, correct_option, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_questions)

    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def check_ip_and_log():
    user_ip = request.remote_addr
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT reason FROM banned_ips WHERE ip = ?', (user_ip,))
    banned = cursor.fetchone()
    
    if banned and request.endpoint != 'banned_page':
        conn.close()
        return redirect(url_for('banned_page'))
    
    if request.endpoint and request.endpoint not in ['static', 'banned_page']:
        cursor.execute('INSERT INTO visitor_logs (ip, user_agent) VALUES (?, ?)', 
                       (user_ip, request.headers.get('User-Agent', 'Unknown')))
        conn.commit()
    conn.close()

CYBERPUNK_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Study Hub</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

        :root {
            --bg-dark: #030712;
            --primary: #00f2fe;
            --secondary: #4facfe;
            --accent: #ff0844;
            --neon-green: #00ff88;
            --neon-purple: #7928ca;
            --neon-pink: #ff007f;
            --card-bg: rgba(10, 15, 30, 0.85);
            --border: rgba(0, 242, 254, 0.35);
            --glow: 0 0 15px rgba(0, 242, 254, 0.4);
            --text: #f8fafc;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Rajdhani', sans-serif; }
        
        body { 
            background: #02040a;
            color: var(--text); 
            min-height: 100vh; 
            overflow-x: hidden;
            position: relative;
        }

        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: 
                linear-gradient(rgba(0, 242, 254, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 242, 254, 0.05) 1px, transparent 1px);
            background-size: 35px 35px;
            z-index: -2;
            pointer-events: none;
        }

        body::after {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 50% -20%, rgba(0, 242, 254, 0.15) 0%, transparent 70%);
            z-index: -1;
            pointer-events: none;
        }

        nav {
            position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
            width: 95%; max-width: 1400px; background: rgba(5, 10, 25, 0.92);
            backdrop-filter: blur(20px); border: 1px solid var(--border);
            box-shadow: var(--glow);
            border-radius: 50px; padding: 10px 24px; display: flex;
            justify-content: space-between; align-items: center; z-index: 1000;
        }

        .logo { 
            font-family: 'Orbitron', sans-serif; font-size: 1.3rem; font-weight: 900; 
            color: var(--primary); display: flex; align-items: center; gap: 10px;
            text-shadow: 0 0 10px var(--primary);
        }

        .nav-links { display: flex; gap: 6px; list-style: none; align-items: center; }
        .nav-links a { 
            color: #94a3b8; text-decoration: none; font-size: 0.88rem; font-weight: 700; 
            padding: 8px 16px; border-radius: 25px; transition: all 0.3s ease;
            text-transform: uppercase; letter-spacing: 0.5px;
        }
        .nav-links a:hover, .nav-links a.active { 
            color: #fff; background: rgba(0, 242, 254, 0.18); border: 1px solid var(--primary);
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.5);
        }

        .container { max-width: 1350px; margin: 105px auto 40px auto; padding: 0 18px; }
        
        .glass-card {
            background: var(--card-bg); backdrop-filter: blur(20px);
            border: 1px solid var(--border); border-radius: 20px; padding: 26px;
            margin-bottom: 24px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            position: relative; overflow: hidden;
        }

        .glass-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }

        .hero-title {
            font-family: 'Orbitron', sans-serif; font-size: 2.2rem; font-weight: 900;
            text-align: center; margin-bottom: 22px; letter-spacing: 1.5px;
            background: linear-gradient(90deg, #00f2fe, #00ff88, #ff007f);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0,242,254,0.3);
        }

        input[type="text"], textarea, input[type="password"], select {
            width: 100%; padding: 12px 16px; background: rgba(2, 6, 23, 0.9);
            border: 1px solid var(--border); border-radius: 12px; color: #fff;
            margin-bottom: 14px; outline: none; font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        input:focus, textarea:focus, select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
        }

        .btn-glow {
            background: linear-gradient(45deg, var(--primary), var(--secondary));
            border: none; color: #000; font-weight: 800; padding: 10px 24px;
            border-radius: 30px; cursor: pointer; text-decoration: none; display: inline-flex;
            align-items: center; gap: 8px; text-transform: uppercase; font-size: 0.88rem;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.4); transition: all 0.3s ease;
        }

        .btn-glow:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.8);
        }

        .btn-danger {
            background: linear-gradient(45deg, #ff0844, #ff4e50); color: #fff;
            padding: 8px 18px; border-radius: 20px; text-decoration: none; font-size: 0.8rem; 
            border: none; cursor: pointer; font-weight: bold;
            box-shadow: 0 0 10px rgba(255, 8, 68, 0.4); transition: all 0.3s ease;
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.4s ease-in-out; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .sub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 20px; margin-top: 15px; }
        .sub-card { 
            background: rgba(4, 10, 26, 0.8); border: 1px solid var(--border); 
            padding: 22px; border-radius: 18px; text-align: center; transition: all 0.3s ease;
        }
        .sub-card:hover {
            border-color: var(--primary); transform: translateY(-4px);
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.3);
        }

        .quiz-card { 
            background: rgba(4, 10, 26, 0.9); border: 1px solid var(--border); 
            border-radius: 18px; padding: 22px; margin-bottom: 18px; 
        }
        .option-btn {
            display: block; width: 100%; text-align: left; padding: 12px 18px;
            background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px; color: #fff; margin-top: 10px; cursor: pointer;
            transition: all 0.3s ease; font-size: 0.95rem;
        }
        .option-btn:hover {
            border-color: var(--primary); background: rgba(0, 242, 254, 0.15);
        }

        .class-badge { 
            background: rgba(121, 40, 202, 0.3); border: 1px solid var(--neon-purple); 
            color: #d8b4fe; padding: 3px 12px; border-radius: 14px; font-size: 0.78rem; font-weight: bold; 
        }

        .clock-box {
            text-align: center; font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem; color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green);
            margin-bottom: 15px;
        }

        .important-note-card {
            border: 2px solid var(--accent) !important;
            box-shadow: 0 0 20px rgba(255, 8, 68, 0.4);
            animation: pulseGlow 2s infinite alternate;
        }

        @keyframes pulseGlow {
            0% { box-shadow: 0 0 15px rgba(255, 8, 68, 0.3); }
            100% { box-shadow: 0 0 30px rgba(255, 8, 68, 0.7); }
        }

        .pdf-chip {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(0, 242, 254, 0.12); border: 1px solid var(--primary);
            color: var(--primary); padding: 6px 14px; border-radius: 20px;
            text-decoration: none; font-size: 0.85rem; font-weight: bold;
            margin-top: 8px; margin-right: 8px; transition: all 0.3s ease;
        }
        .pdf-chip:hover { background: var(--primary); color: #000; }
    </style>
</head>
<body>

    <nav>
        <div class="logo">
            <i class="fa-solid fa-microchip" style="color: var(--neon-green);"></i> CYBER STUDY HUB
        </div>
        <ul class="nav-links">
            <li><a href="#" class="nav-item active" onclick="switchTab(event, 'notes-tab')">Announcements</a></li>
            <li><a href="#" class="nav-item" onclick="switchTab(event, 'ncert-tab')">Sub Prep Vault</a></li>
            <li><a href="#" class="nav-item" onclick="switchTab(event, 'meetings-tab')">Meeting Room</a></li>
            <li><a href="#" class="nav-item" onclick="switchTab(event, 'quiz-tab')">Test Engine</a></li>

            {% if is_owner %}
            <li><a href="#" class="nav-item" style="color: var(--accent);" onclick="switchTab(event, 'owner-tab')">Owner Panel</a></li>
            <li><a href="/logout" class="btn-danger">Logout</a></li>
            {% else %}
            <li><a href="#" onclick="showLoginModal()" class="btn-glow">Owner Login</a></li>
            {% endif %}
        </ul>
    </nav>

    <div class="container">

        <div class="clock-box" id="cyber-clock">00:00:00 UTC</div>

        <!-- OWNER LOGIN MODAL -->
        <div id="login-modal" class="glass-card" style="display: none; max-width: 420px; margin: 20px auto; text-align: center;">
            <h3 style="font-family: Orbitron; color: var(--primary); margin-bottom: 14px;">Owner Access</h3>
            <form action="/login" method="post">
                <input type="password" name="password" placeholder="Enter Owner Password..." required>
                <button type="submit" class="btn-glow" style="width: 100%; justify-content: center;">Access System</button>
            </form>
        </div>

        <!-- TAB 1: IMPORTANT ANNOUNCEMENTS -->
        <div id="notes-tab" class="tab-content active">
            <h1 class="hero-title">IMPORTANT ANNOUNCEMENTS</h1>
            
            {% if is_owner %}
            <div class="glass-card">
                <h3 style="color: var(--neon-green); margin-bottom: 12px;"><i class="fa-solid fa-bullhorn"></i> Post Announcement (Multiple PDFs Allowed)</h3>
                <form action="/add-note" method="post" enctype="multipart/form-data">
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 12px;">
                        <input type="text" name="title" placeholder="Announcement Title..." required>
                        <select name="target_class">
                            <option value="All">All Classes</option>
                            <option value="Class 9">Class 9th</option>
                            <option value="Class 10">Class 10th</option>
                            <option value="Class 11">Class 11th</option>
                            <option value="Class 12">Class 12th</option>
                        </select>
                    </div>
                    <textarea name="content" rows="3" placeholder="Write announcement details..." required></textarea>
                    
                    <label style="color: var(--primary); font-weight: bold; display: block; margin-bottom: 6px;">
                        <i class="fa-solid fa-paperclip"></i> Attach Multiple PDFs / Files:
                    </label>
                    <input type="file" name="pdf_files" multiple accept=".pdf,.png,.jpg,.jpeg" style="border: none; margin-bottom: 15px;">
                    <br>
                    <button type="submit" class="btn-glow"><i class="fa-solid fa-paper-plane"></i> Publish Announcement</button>
                </form>
            </div>
            {% endif %}

            <div class="glass-card">
                <h3 style="color: var(--primary); margin-bottom: 18px;"><i class="fa-solid fa-circle-exclamation"></i> Live Announcements</h3>
                {% for note in notes %}
                <div class="important-note-card" style="background: rgba(3, 8, 22, 0.85); padding: 18px; margin-top: 16px; border-radius: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="color: var(--primary); font-family: 'Orbitron'; font-size: 1.1rem;">📢 {{ note[1] }}</h4>
                        <div>
                            <span class="class-badge">{{ note[3] }}</span>
                            {% if is_owner %}
                            <a href="/delete-note/{{ note[0] }}" class="btn-danger" style="margin-left: 10px;">Delete</a>
                            {% endif %}
                        </div>
                    </div>
                    <p style="margin-top: 10px; font-size: 1rem; color: #e2e8f0; line-height: 1.5;">{{ note[2] }}</p>

                    {% if note[5] %}
                    <div style="margin-top: 12px;">
                        <span style="font-size: 0.85rem; color: var(--neon-green); font-weight: bold;">Attached Files:</span><br>
                        {% for file in note[5] %}
                        <a href="{{ url_for('uploaded_file', filename=file) }}" target="_blank" class="pdf-chip">
                            <i class="fa-solid fa-file-pdf"></i> {{ file }}
                        </a>
                        {% endfor %}
                    </div>
                    {% endif %}

                    <small style="color: #64748b; margin-top: 12px; display: block;"><i class="fa-regular fa-clock"></i> {{ note[4] }}</small>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- TAB 2: PREP VAULT -->
        <div id="ncert-tab" class="tab-content">
            <h1 class="hero-title">SUBJECT PREPARATION VAULT</h1>
            {% if is_owner %}
            <div class="glass-card">
                <h3 style="color: var(--neon-green); margin-bottom: 12px;"><i class="fa-solid fa-cloud-arrow-up"></i> Upload Class-wise Study Material</h3>
                <form action="/upload-material" method="post" enctype="multipart/form-data">
                    <input type="text" name="title" placeholder="Material / Book Title..." required>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
                        <select name="class_level" id="mat-class" onchange="updateSubjects('mat-class', 'mat-subject')" required>
                            <option value="Class 9">Class 9th</option>
                            <option value="Class 10">Class 10th</option>
                            <option value="Class 11">Class 11th</option>
                            <option value="Class 12">Class 12th</option>
                        </select>
                        <select name="subject" id="mat-subject" required>
                            <option value="Mathematics">Mathematics</option>
                            <option value="Science">Science</option>
                            <option value="Social Science">Social Science</option>
                            <option value="English">English</option>
                            <option value="Hindi">Hindi</option>
                        </select>
                        <select name="material_type" required>
                            <option value="NCERT Book">NCERT Book</option>
                            <option value="Notes">Notes</option>
                            <option value="Sample Paper">Sample Paper</option>
                        </select>
                    </div>
                    <input type="file" name="pdf_file" accept=".pdf,.png,.jpg" required style="border: none;">
                    <button type="submit" class="btn-glow">Upload Material</button>
                </form>
            </div>
            {% endif %}

            <div class="glass-card">
                <div style="display: flex; gap: 12px; margin-bottom: 22px; flex-wrap: wrap; justify-content: center;">
                    <button class="btn-glow" onclick="filterClass('All')">ALL CLASSES</button>
                    <button class="btn-glow" onclick="filterClass('Class 9')">CLASS 9</button>
                    <button class="btn-glow" onclick="filterClass('Class 10')">CLASS 10</button>
                    <button class="btn-glow" onclick="filterClass('Class 11')">CLASS 11</button>
                    <button class="btn-glow" onclick="filterClass('Class 12')">CLASS 12</button>
                </div>

                <div class="sub-grid">
                    {% for mat in materials %}
                    <div class="sub-card material-card" data-class="{{ mat[2] }}">
                        <i class="fa-solid fa-file-pdf" style="font-size: 2.8rem; color: var(--neon-green); margin-bottom: 10px;"></i>
                        <div>
                            <span class="class-badge">{{ mat[2] }}</span>
                            <span style="font-size: 0.85rem; color: var(--primary); font-weight: bold; margin-left: 6px;">{{ mat[3] }}</span>
                        </div>
                        <p style="font-weight: bold; margin: 10px 0; font-size: 1.05rem;">{{ mat[1] }}</p>
                        <div style="display: flex; gap: 8px; justify-content: center; margin-top: 10px;">
                            <a href="{{ url_for('uploaded_file', filename=mat[5]) }}" target="_blank" class="btn-glow" style="padding: 6px 14px; font-size: 0.8rem;">View File</a>
                            {% if is_owner %}
                            <a href="/delete-material/{{ mat[0] }}" class="btn-danger">Delete</a>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- TAB 3: MEETING ROOM -->
        <div id="meetings-tab" class="tab-content">
            <h1 class="hero-title">MEETING ROOM</h1>
            {% if is_owner %}
            <div class="glass-card">
                <h3 style="color: var(--neon-green); margin-bottom: 12px;"><i class="fa-solid fa-headset"></i> Schedule Attendable Meeting</h3>
                <form action="/add-meeting" method="post">
                    <input type="text" name="title" placeholder="Meeting Topic..." required>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <select name="class_level" id="meet-class" onchange="updateSubjects('meet-class', 'meet-subject')" required>
                            <option value="Class 9">Class 9th</option>
                            <option value="Class 10">Class 10th</option>
                            <option value="Class 11">Class 11th</option>
                            <option value="Class 12">Class 12th</option>
                        </select>
                        <select name="subject" id="meet-subject" required>
                            <option value="Mathematics">Mathematics</option>
                            <option value="Science">Science</option>
                            <option value="Social Science">Social Science</option>
                            <option value="English">English</option>
                            <option value="Hindi">Hindi</option>
                        </select>
                    </div>
                    <input type="text" name="meeting_url" placeholder="Google Meet / Zoom URL..." required>
                    <input type="text" name="scheduled_time" placeholder="Date & Time (e.g. Today 6:00 PM)" required>
                    <select name="status" required>
                        <option value="🟢 LIVE / ATTENDABLE">🟢 LIVE NOW / Attendable</option>
                        <option value="⏳ UPCOMING">⏳ Upcoming</option>
                        <option value="🔴 CONCLUDED">🔴 Concluded</option>
                    </select>
                    <button type="submit" class="btn-glow">Create Meeting</button>
                </form>
            </div>
            {% endif %}

            <div class="glass-card">
                <h3 style="color: var(--primary); margin-bottom: 18px;"><i class="fa-solid fa-users"></i> Attendable Live Meetings & Classes</h3>
                <div class="sub-grid">
                    {% for m in meetings %}
                    <div class="sub-card">
                        <i class="fa-solid fa-video" style="font-size: 2.5rem; color: var(--neon-pink); margin-bottom: 10px;"></i>
                        <div>
                            <span class="class-badge">{{ m[2] }}</span>
                            <span style="font-size: 0.85rem; color: var(--primary); font-weight: bold; margin-left: 6px;">{{ m[3] }}</span>
                        </div>
                        <h4 style="margin: 10px 0; color: #fff;">{{ m[1] }}</h4>
                        <p style="color: var(--neon-green); font-size: 0.85rem; margin-bottom: 6px;"><i class="fa-regular fa-clock"></i> {{ m[5] }}</p>
                        <p style="color: var(--accent); font-weight: bold; font-size: 0.9rem; margin-bottom: 12px;">{{ m[6] }}</p>
                        <a href="{{ m[4] }}" target="_blank" class="btn-glow" style="width: 100%; justify-content: center;"><i class="fa-solid fa-right-to-bracket"></i> Attend Meeting</a>
                        {% if is_owner %}
                        <a href="/delete-meeting/{{ m[0] }}" class="btn-danger" style="display: inline-block; margin-top: 8px;">Delete</a>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- TAB 4: TEST ENGINE (With Hindi, English & SST Added) -->
        <div id="quiz-tab" class="tab-content">
            <h1 class="hero-title">PRACTICE TEST ENGINE</h1>
            {% if is_owner %}
            <div class="glass-card">
                <h3 style="color: var(--neon-green); margin-bottom: 12px;"><i class="fa-solid fa-square-plus"></i> Add Question</h3>
                <form action="/add-quiz" method="post">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
                        <select name="class_level" id="quiz-class" onchange="updateSubjects('quiz-class', 'quiz-subject')" required>
                            <option value="Class 9">Class 9th</option>
                            <option value="Class 10">Class 10th</option>
                            <option value="Class 11">Class 11th</option>
                            <option value="Class 12">Class 12th</option>
                        </select>
                        <select name="subject" id="quiz-subject" required>
                            <option value="Mathematics">Mathematics</option>
                            <option value="Science">Science</option>
                            <option value="Social Science">Social Science</option>
                            <option value="English">English</option>
                            <option value="Hindi">Hindi</option>
                        </select>
                        <select name="difficulty" required>
                            <option value="Easy">Easy</option>
                            <option value="Medium">Medium</option>
                            <option value="Hard">Hard</option>
                        </select>
                    </div>
                    <textarea name="question" rows="2" placeholder="Enter Question text..." required></textarea>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <input type="text" name="option_a" placeholder="Option A" required>
                        <input type="text" name="option_b" placeholder="Option B" required>
                        <input type="text" name="option_c" placeholder="Option C" required>
                        <input type="text" name="option_d" placeholder="Option D" required>
                    </div>
                    <select name="correct_option" required>
                        <option value="A">Correct: A</option>
                        <option value="B">Correct: B</option>
                        <option value="C">Correct: C</option>
                        <option value="D">Correct: D</option>
                    </select>
                    <input type="text" name="explanation" placeholder="Detailed Explanation..." required>
                    <button type="submit" class="btn-glow">Save Question</button>
                </form>
            </div>
            {% endif %}

            <div class="glass-card">
                <button class="btn-glow" onclick="generateTest()"><i class="fa-solid fa-play"></i> Start Practice Test</button>
                <div id="test-container" style="margin-top: 20px;"></div>
                <div id="test-result-box" style="display: none; text-align: center; margin-top: 20px;">
                    <h2 id="res-score" style="color: var(--neon-green); font-family: 'Orbitron';"></h2>
                </div>
            </div>
        </div>

        <!-- TAB 5: OWNER CONTROL PANEL -->
        {% if is_owner %}
        <div id="owner-tab" class="tab-content">
            <h1 class="hero-title" style="color: var(--accent);">OWNER SECURITY COMMAND CENTER</h1>
            <div class="glass-card">
                <h3 style="color: var(--accent); margin-bottom: 12px;"><i class="fa-solid fa-ban"></i> Block IP Address</h3>
                <form action="/ban-ip" method="post">
                    <input type="text" name="ip" placeholder="Target IP Address..." required>
                    <input type="text" name="reason" placeholder="Reason for ban..." required>
                    <button type="submit" class="btn-danger">Block IP</button>
                </form>
            </div>
        </div>
        {% endif %}

    </div>

    <script>
        const rawQuizzes = {{ quizzes_json | safe }};
        let userAnswers = {};

        // Class-wise subjects mapping (Hindi, SST, English included for all classes)
        const classSubjects = {
            "Class 9": ["Mathematics", "Science", "Social Science", "English", "Hindi", "Computer Applications"],
            "Class 10": ["Mathematics", "Science", "Social Science", "English", "Hindi", "Information Technology"],
            "Class 11": ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science", "English", "Hindi", "Economics", "Accountancy", "Business Studies"],
            "Class 12": ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science", "English", "Hindi", "Economics", "Accountancy", "Business Studies"]
        };

        function updateSubjects(classSelectId, subjectSelectId) {
            const classVal = document.getElementById(classSelectId).value;
            const subSelect = document.getElementById(subjectSelectId);
            if (!subSelect) return;
            subSelect.innerHTML = "";
            const subs = classSubjects[classVal] || ["Mathematics", "Science", "English", "Hindi"];
            subs.forEach(sub => {
                const opt = document.createElement('option');
                opt.value = sub;
                opt.textContent = sub;
                subSelect.appendChild(opt);
            });
        }

        // Initialize subject dropdowns on load
        window.addEventListener('DOMContentLoaded', () => {
            updateSubjects('mat-class', 'mat-subject');
            updateSubjects('meet-class', 'meet-subject');
            updateSubjects('quiz-class', 'quiz-subject');
        });

        function updateClock() {
            const now = new Date();
            document.getElementById('cyber-clock').innerText = 'SYSTEM TIME: ' + now.toUTCString();
        }
        setInterval(updateClock, 1000);
        updateClock();

        function switchTab(evt, tabId) {
            evt.preventDefault();
            playAudioChime();
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
        }

        function showLoginModal() {
            playAudioChime();
            const m = document.getElementById('login-modal');
            m.style.display = m.style.display === 'none' ? 'block' : 'none';
        }

        function filterClass(cls) {
            playAudioChime();
            document.querySelectorAll('.material-card').forEach(item => {
                if (cls === 'All' || item.dataset.class === cls) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        function playAudioChime() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(800, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(400, ctx.currentTime + 0.08);
                gain.gain.setValueAtTime(0.1, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.08);
            } catch(e) {}
        }

        function generateTest() {
            playAudioChime();
            const container = document.getElementById('test-container');
            let html = '';
            rawQuizzes.forEach((q, idx) => {
                html += `
                    <div class="quiz-card">
                        <p style="font-size: 1.1rem; font-weight: bold;"><b>Q${idx + 1}.</b> [${q.subject}] ${q.question}</p>
                        <button class="option-btn" onclick="selectOption(${q.id}, 'A')">A) ${q.option_a}</button>
                        <button class="option-btn" onclick="selectOption(${q.id}, 'B')">B) ${q.option_b}</button>
                        <button class="option-btn" onclick="selectOption(${q.id}, 'C')">C) ${q.option_c}</button>
                        <button class="option-btn" onclick="selectOption(${q.id}, 'D')">D) ${q.option_d}</button>
                    </div>
                `;
            });
            html += `<button class="btn-glow" onclick="submitTest()"><i class="fa-solid fa-check"></i> Submit Test</button>`;
            container.innerHTML = html;
        }

        function selectOption(qId, opt) {
            playAudioChime();
            userAnswers[qId] = opt;
        }

        function submitTest() {
            playAudioChime();
            let score = 0;
            rawQuizzes.forEach((q) => {
                if (userAnswers[q.id] === q.correct_option) score++;
            });
            document.getElementById('res-score').innerText = `Your Score: ${score} / ${rawQuizzes.length}`;
            document.getElementById('test-result-box').style.display = 'block';
        }
    </script>
</body>
</html>
"""

BANNED_HTML = """
<!DOCTYPE html>
<html>
<head><title>Access Denied</title></head>
<body style="background: #030712; color: #ff0844; text-align: center; padding-top: 100px; font-family: sans-serif;">
    <h1>🚫 ACCESS DENIED - SYSTEM LOCKED</h1>
    <p>Your IP has been flagged by Cyber Study Hub Owner.</p>
</body>
</html>
"""

@app.route('/banned')
def banned_page():
    return render_template_string(BANNED_HTML), 403

@app.route('/')
def index():
    is_owner = session.get('is_owner', False)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, content, target_class, created_at, attachments FROM notes ORDER BY id DESC')
    notes_raw = cursor.fetchall()
    notes = []
    for n in notes_raw:
        attachments = json.loads(n[5]) if n[5] else []
        notes.append((n[0], n[1], n[2], n[3], n[4], attachments))

    cursor.execute('SELECT id, title, class_level, subject, material_type, filename, uploaded_at FROM study_materials ORDER BY id DESC')
    materials = cursor.fetchall()

    cursor.execute('SELECT id, title, class_level, subject, meeting_url, scheduled_time, status FROM meetings ORDER BY id DESC')
    meetings = cursor.fetchall()

    cursor.execute('SELECT id, class_level, subject, difficulty, question, option_a, option_b, option_c, option_d, correct_option, explanation FROM quizzes')
    quizzes_raw = cursor.fetchall()
    
    quizzes = []
    for q in quizzes_raw:
        quizzes.append({
            'id': q[0], 'class_level': q[1], 'subject': q[2], 'difficulty': q[3], 'question': q[4],
            'option_a': q[5], 'option_b': q[6], 'option_c': q[7], 'option_d': q[8],
            'correct_option': q[9], 'explanation': q[10]
        })

    conn.close()
    return render_template_string(
        CYBERPUNK_HTML, 
        is_owner=is_owner, 
        notes=notes, 
        materials=materials, 
        meetings=meetings,
        quizzes_json=json.dumps(quizzes)
    )

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == OWNER_PASSWORD:
        session['is_owner'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('is_owner', None)
    return redirect(url_for('index'))

@app.route('/add-note', methods=['POST'])
def add_note():
    if not session.get('is_owner'): return redirect(url_for('index'))
    title = request.form.get('title')
    content = request.form.get('content')
    target_class = request.form.get('target_class')
    uploaded_files = request.files.getlist('pdf_files')
    
    saved_filenames = []
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            saved_filenames.append(fname)

    if title and content:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notes (title, content, target_class, attachments) VALUES (?, ?, ?, ?)', 
                       (title, content, target_class, json.dumps(saved_filenames)))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete-note/<int:note_id>')
def delete_note(note_id):
    if not session.get('is_owner'): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/upload-material', methods=['POST'])
def upload_material():
    if not session.get('is_owner'): return redirect(url_for('index'))
    title = request.form.get('title')
    class_level = request.form.get('class_level')
    subject = request.form.get('subject')
    material_type = request.form.get('material_type')
    file = request.files.get('pdf_file')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO study_materials (title, class_level, subject, material_type, filename) VALUES (?, ?, ?, ?, ?)', 
                       (title, class_level, subject, material_type, filename))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete-material/<int:mat_id>')
def delete_material(mat_id):
    if not session.get('is_owner'): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM study_materials WHERE id = ?', (mat_id,))
    res = cursor.fetchone()
    if res:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], res[0])
        if os.path.exists(file_path): os.remove(file_path)
        cursor.execute('DELETE FROM study_materials WHERE id = ?', (mat_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add-meeting', methods=['POST'])
def add_meeting():
    if not session.get('is_owner'): return redirect(url_for('index'))
    title = request.form.get('title')
    class_level = request.form.get('class_level')
    subject = request.form.get('subject')
    meeting_url = request.form.get('meeting_url')
    scheduled_time = request.form.get('scheduled_time')
    status = request.form.get('status', '🟢 LIVE / ATTENDABLE')
    
    if title and meeting_url:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO meetings (title, class_level, subject, meeting_url, scheduled_time, status) VALUES (?, ?, ?, ?, ?, ?)', 
                       (title, class_level, subject, meeting_url, scheduled_time, status))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete-meeting/<int:m_id>')
def delete_meeting(m_id):
    if not session.get('is_owner'): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM meetings WHERE id = ?', (m_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add-quiz', methods=['POST'])
def add_quiz():
    if not session.get('is_owner'): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quizzes (class_level, subject, difficulty, question, option_a, option_b, option_c, option_d, correct_option, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form.get('class_level'),
        request.form.get('subject'),
        request.form.get('difficulty'),
        request.form.get('question'),
        request.form.get('option_a'),
        request.form.get('option_b'),
        request.form.get('option_c'),
        request.form.get('option_d'),
        request.form.get('correct_option'),
        request.form.get('explanation')
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/ban-ip', methods=['POST'])
def ban_ip():
    if not session.get('is_owner'): return redirect(url_for('index'))
    ip = request.form.get('ip')
    reason = request.form.get('reason', 'Blocked by Owner')
    if ip:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO banned_ips (ip, reason) VALUES (?, ?)', (ip, reason))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
