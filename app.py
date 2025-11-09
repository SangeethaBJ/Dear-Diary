from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, os, json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'diary.db')

app = Flask(__name__)
app.secret_key = 'deardiary_secret_key_change_me'

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            phone TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            genre TEXT,
            title TEXT,
            content TEXT,
            meta TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm']
        if not name or not password or not email:
            flash('Please fill required fields')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            hashed = generate_password_hash(password)
            cur.execute('INSERT INTO users (name, phone, email, password) VALUES (?,?,?,?)',
                        (name, phone, email, hashed))
            conn.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('User exists')
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE name=?', (name,))
        user = cur.fetchone()
        conn.close()
        if user:
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash('Login successful')
                return redirect(url_for('home'))
            else:
                flash('Wrong password')
                return redirect(url_for('login'))
        else:
            flash('User not found')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    themes = [
        {'name': 'Classic Leather', 'class': 'theme-leather'},
        {'name': 'Floral', 'class': 'theme-floral'},
        {'name': 'Minimal', 'class': 'theme-minimal'},
        {'name': 'Retro', 'class': 'theme-retro'},
    ]
    genres = ['Diary', 'Habit Tracker', 'Manifestation', '21 Days Challenge', 'To Do']
    return render_template('home.html', themes=themes, genres=genres, user_name=session.get('user_name'))

@app.route('/save_entry', methods=['POST'])
def save_entry():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    data = request.get_json()
    genre = data.get('genre')
    title = data.get('title','')
    content = data.get('content','')
    meta = json.dumps(data.get('meta', {}))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO entries (user_id, genre, title, content, meta, created_at) VALUES (?,?,?,?,?,?)',
                (session['user_id'], genre, title, content, meta, current_time()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'message': 'Saved', 'time': current_time()})

@app.route('/entries/<genre>')
def entries(genre):
    if 'user_id' not in session:
        return jsonify([])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM entries WHERE user_id=? AND genre=? ORDER BY id DESC', (session['user_id'], genre))
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            'id': r['id'], 'title': r['title'], 'content': r['content'], 'meta': json.loads(r['meta'] or '{}'), 'created_at': r['created_at']
        })
    return jsonify(result)

@app.route('/genre/diary')
def genre_diary():
    return render_template('diary.html', user_name=session.get('user_name'))

@app.route('/genre/habit')
def genre_habit():
    return render_template('habit_tracker.html', user_name=session.get('user_name'))

@app.route('/genre/manifestation')
def genre_manifestation():
    return render_template('manifestation.html', user_name=session.get('user_name'))

@app.route('/genre/challenge21')
def genre_challenge21():
    return render_template('challenge21.html', user_name=session.get('user_name'))

@app.route('/genre/todo')
def genre_todo():
    return render_template('todo.html', user_name=session.get('user_name'))

@app.route('/admin')
def admin_page():
    # Only you (Sangeetha) can access this
    if 'user_name' not in session or session['user_name'].lower() != 'sangeetha':
        return "Access Denied ❌", 403

    # Connect to the database
    import sqlite3, os
    BASE = os.path.dirname(os.path.abspath(__file__))
    DB = os.path.join(BASE, "diary.db")

    # Count users from your 'users' table
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()

    # Simple styled output
    return f"""
    <div style='
        font-family: Poppins, sans-serif;
        display:flex; flex-direction:column;
        justify-content:center; align-items:center;
        height:100vh; background:#f5f5f5;'>
        <h2 style='color:#333;'>👑 Hello Sangeetha!</h2>
        <p style='font-size:20px;'>Total Registered Users: 
        <b style='color:#007bff;'>{count}</b></p>
    </div>
    """


if __name__ == '__main__':
    app.run(debug=True)
