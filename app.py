import os
import uuid
import cv2
import numpy as np
import face_recognition
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import traceback


# Initialize Flask with security configurations
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random secret key
app.permanent_session_lifetime = timedelta(minutes=30)

# Security-focused configurations
app.config.update(
    UPLOAD_FOLDER=os.path.join(os.path.dirname(__file__), 'static', 'uploads'),
    FACE_FOLDER=os.path.join(os.path.dirname(__file__), 'static', 'faces'),
    DATABASE=os.path.join(os.path.dirname(__file__), 'voting_system.db'),
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg'},
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB limit
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FACE_FOLDER'], exist_ok=True)

# Database connection
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Security validation functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def verify_image_integrity(filepath):
    try:
        img = cv2.imread(filepath)
        return img is not None
    except Exception:
        return False

# Face processing utilities
def process_face_image(file_stream):
    try:
        # Read image securely
        file_bytes = np.asarray(bytearray(file_stream.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            return None

        # Convert to RGB and resize if needed
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = rgb_img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            rgb_img = cv2.resize(rgb_img, (0,0), fx=scale, fy=scale)
        
        return rgb_img
    except Exception:
        return None
@app.route('/')
def home():
    """Main landing page with voting system overview"""
    return render_template('index.html')

@app.route('/features')
def features():
    """Dedicated features page"""
    return render_template('partials/_features.html')

def is_duplicate_face(new_encoding):
    conn = get_db_connection()
    users = conn.execute("SELECT face_encoding FROM users").fetchall()
    conn.close()

    for user in users:
        if user['face_encoding']:
            existing_encoding = np.frombuffer(user['face_encoding'], dtype=np.float64)
            match = face_recognition.compare_faces([existing_encoding], new_encoding, tolerance=0.45)[0]
            if match:
                return True
    return False

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            file = request.files.get('face_image')

            # Validate inputs
            if not all([username, password, file]):
                flash('All fields are required', 'danger')
                return render_template('register.html')

            if not allowed_file(file.filename):
                flash('Invalid file type. Only JPG/PNG allowed.', 'danger')
                return render_template('register.html')

            # Process image securely
            rgb_img = process_face_image(file)
            if rgb_img is None:
                flash('Invalid image file', 'danger')
                return render_template('register.html')

            # Face detection with fallback
            face_locations = face_recognition.face_locations(rgb_img, model="hog")
            if not face_locations:
                flash('No face detected. Please upload a clear front-facing photo.', 'danger')
                return render_template('register.html')

            # Generate encoding
            face_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]

            # 🔒 Check for duplicate face before saving
            if is_duplicate_face(face_encoding):
                flash('This face is already registered with another account.', 'danger')
                return render_template('register.html')

            # Save image file
            filename = secure_filename(f"{uuid.uuid4().hex}.jpg")
            filepath = os.path.join(app.config['FACE_FOLDER'], filename)
            cv2.imwrite(filepath, cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR))

            # Other validations
            from datetime import datetime
            voter_id = request.form['voter_id']
            aadhaar = request.form['aadhaar']
            dob_str = request.form['dob']

            dob = datetime.strptime(dob_str, '%Y-%m-%d')
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                flash('You must be at least 18 years old to vote.', 'danger')
                return render_template('register.html')

            # Save user data
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (username, password, face_image, face_encoding, voter_id, aadhaar, dob) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, generate_password_hash(password), filename, face_encoding.tobytes(), voter_id, aadhaar, dob_str)
            )
            conn.commit()
            conn.close()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            traceback.print_exc()
            flash('Registration error. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", 
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            return redirect(url_for('face_verify'))
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/face_verify', methods=['GET', 'POST'])
def face_verify():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            file = request.files.get('live_image')
            if not file or not allowed_file(file.filename):
                flash('Invalid image', 'danger')
                return redirect(url_for('face_verify'))

            # Process uploaded image
            rgb_img = process_face_image(file)
            if rgb_img is None:
                flash('Invalid image data', 'danger')
                return redirect(url_for('face_verify'))

            # Get stored face data
            conn = get_db_connection()
            user = conn.execute(
                "SELECT face_encoding FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            conn.close()

            if not user:
                flash('User data not found', 'danger')
                return redirect(url_for('register'))

            # Compare faces
            face_locations = face_recognition.face_locations(rgb_img)
            if not face_locations:
                flash('No face detected', 'danger')
                return redirect(url_for('face_verify'))

            upload_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
            stored_encoding = np.frombuffer(user['face_encoding'], dtype=np.float64)

            match = face_recognition.compare_faces(
                [stored_encoding],
                upload_encoding,
                tolerance=0.45
            )[0]

            if match:
                session['verified'] = True
                return redirect(url_for('vote'))
            
            flash('Face verification failed', 'danger')
            return redirect(url_for('face_verify'))

        except Exception as e:
            traceback.print_exc()
            flash('Verification error', 'danger')
    
    return render_template('face_verify.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user['has_voted']:
        flash('Your vote has already been recorded.', 'info')
        return render_template('already_voted.html')  # or redirect to a page that says so

    if request.method == 'POST':
        selected_candidate = request.form.get('candidate')
        # Save the vote to votes table
        conn.execute('INSERT INTO votes (user_id, candidate_id) VALUES (?, ?)', (user_id, selected_candidate))
        # Update user's has_voted status
        conn.execute('UPDATE users SET has_voted = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('Your vote has been recorded successfully!', 'success')
        return redirect(url_for('result'))

    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    conn.close()
    return render_template('vote.html', candidates=candidates)


@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    results = conn.execute('''
        SELECT c.id, c.name, c.party, COUNT(v.id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id
        GROUP BY c.id
        ORDER BY vote_count DESC
    ''').fetchall()
    conn.close()
    
    return render_template('result.html', results=results)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin'] = True
            session['admin_id'] = admin['id']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    results = conn.execute('''
        SELECT c.id, c.name, c.party, COUNT(v.id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id
        GROUP BY c.id
        ORDER BY vote_count DESC
    ''').fetchall()
    
    total_votes = conn.execute('SELECT COUNT(*) FROM votes').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    voted_users = conn.execute('SELECT COUNT(*) FROM users WHERE has_voted = TRUE').fetchone()[0]
    
    conn.close()

    return render_template('admin_dashboard.html', 
                         candidates=candidates, 
                         results=results,
                         total_votes=total_votes,
                         total_users=total_users,
                         voted_users=voted_users)

@app.route('/admin/add_candidate', methods=['POST'])
def add_candidate():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    name = request.form['name']
    party = request.form['party']
    logo_file = request.files['logo']
    

    if logo_file and logo_file.filename != '':
        UPLOAD_FOLDER = os.path.join('static', 'uploads')
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        filename = secure_filename(logo_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logo_file.save(filepath)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO candidates (name, party, logo) VALUES (?, ?, ?)',
                         (name, party, filename))
            conn.commit()
            flash('Candidate added successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding candidate: {str(e)}', 'danger')
        finally:
            conn.close()
    else:
        flash('Candidate logo image is required', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_candidate/<int:candidate_id>')
def delete_candidate(candidate_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
        conn.commit()
        flash('Candidate deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting candidate: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_id', None)
    flash('You have been logged out as admin', 'info')
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print(app.url_map)
    app.run(debug=True)