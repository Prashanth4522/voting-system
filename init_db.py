# database.py
import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    face_image TEXT,
    face_encoding BLOB,
    has_voted BOOLEAN DEFAULT 0,
    voter_id TEXT UNIQUE,
    aadhaar TEXT UNIQUE,
    dob TEXT
    );
    )
''')

    # Candidates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party TEXT NOT NULL
        )
    ''')
    
    # Votes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            candidate_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(candidate_id) REFERENCES candidates(id)
        )
    ''')
    
    # Admin table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
     # Add any potentially missing columns to users table
    try:
        c.execute("SELECT face_encoding FROM users LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE users ADD COLUMN face_encoding BLOB")
    
    
    # Insert default admin if not exists
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        hashed_pw = generate_password_hash('admin123')
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                 ('admin', hashed_pw))
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('voting_system.db')
    conn.row_factory = sqlite3.Row
    return conn