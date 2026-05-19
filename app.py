from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
import json
import os
from datetime import datetime
import uuid

# Disable template cache for development
app = Flask(__name__, template_folder='templates', static_folder='static')
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}
app.secret_key = 'your_secret_key_here'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            address TEXT,
            role TEXT NOT NULL CHECK (role IN ('user', 'policy_provider', 'voting_member')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            adhar_card_path TEXT,
            policy_document_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Policies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_provider_id INTEGER,
            policy_name TEXT NOT NULL,
            policy_description TEXT,
            policy_cost REAL,
            required_documents TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (policy_provider_id) REFERENCES users (id)
        )
    ''')
    
    # User policies (purchased policies) table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            policy_id INTEGER,
            blockchain_hash TEXT,
            payment_status TEXT,
            policy_approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (policy_id) REFERENCES policies (id)
        )
    ''')
    
    # Claims table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_policy_id INTEGER,
            claim_amount REAL,
            accident_picture_path TEXT,
            policy_document_path TEXT,
            adhar_path TEXT,
            vehicle_rc_path TEXT,
            claim_status TEXT DEFAULT 'pending',
            blockchain_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_policy_id) REFERENCES user_policies (id)
        )
    ''')
    
    # Votes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id INTEGER,
            voting_member_id INTEGER,
            vote TEXT CHECK (vote IN ('approve', 'reject')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (claim_id) REFERENCES claims (id),
            FOREIGN KEY (voting_member_id) REFERENCES users (id)
        )
    ''')
    
    # Blockchain table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blockchain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_data TEXT,
            block_hash TEXT,
            previous_hash TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Simple blockchain implementation - in-memory
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        genesis_block = {
            'index': 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': 'Genesis Block',
            'previous_hash': '0',
            'hash': self.calculate_hash('Genesis Block', '0', 0)
        }
        self.chain.append(genesis_block)
    
    def calculate_hash(self, data, previous_hash, index):
        block_string = f"{index}{previous_hash}{data}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def add_block(self, data):
        previous_block = self.chain[-1]
        new_block = {
            'index': len(self.chain),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': data,
            'previous_hash': previous_block['hash'],
            'hash': self.calculate_hash(data, previous_block['hash'], len(self.chain))
        }
        self.chain.append(new_block)
        return new_block['hash']
    
    def generate_transaction_hash(self, username, policy_name, amount=None):
        transaction_data = {
            'username': username,
            'policy_name': policy_name,
            'amount': amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return self.add_block(transaction_data)

# Initialize blockchain (will be created after database is initialized)
blockchain = None

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(role=None):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'error')
                return redirect(url_for('login'))
            
            if role and session.get('role') != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone_number = request.form['phone_number']
        address = request.form.get('address', '')
        role = request.form['role']
        
        conn = sqlite3.connect('insurance.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, email, phone_number, address, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, generate_password_hash(password), email, phone_number, address, role))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('insurance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[3]
            session['role'] = user[6]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required()
def dashboard():
    if session['role'] == 'user':
        return render_template('user_dashboard.html')
    elif session['role'] == 'policy_provider':
        return render_template('policy_provider_dashboard.html')
    elif session['role'] == 'voting_member':
        return render_template('voting_member_dashboard.html')

# User Profile Management
@app.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    if request.method == 'POST':
        if 'adhar_card' in request.files:
            adhar_file = request.files['adhar_card']
            if adhar_file and allowed_file(adhar_file.filename):
                filename = secure_filename(adhar_file.filename)
                adhar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"adhar_{session['user_id']}_{filename}"))
                
                conn = sqlite3.connect('insurance.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profiles (user_id, adhar_card_path)
                    VALUES (?, ?)
                ''', (session['user_id'], f"adhar_{session['user_id']}_{filename}"))
                conn.commit()
                conn.close()
        
        if 'policy_document' in request.files:
            policy_file = request.files['policy_document']
            if policy_file and allowed_file(policy_file.filename):
                filename = secure_filename(policy_file.filename)
                policy_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"policy_{session['user_id']}_{filename}"))
                
                conn = sqlite3.connect('insurance.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profiles (user_id, policy_document_path)
                    VALUES (?, ?)
                ''', (session['user_id'], f"policy_{session['user_id']}_{filename}"))
                conn.commit()
                conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT up.*, u.username, u.email, u.phone_number, u.address
        FROM user_profiles up
        JOIN users u ON up.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],))
    profile_data = cursor.fetchone()
    conn.close()
    
    return render_template('profile.html', profile=profile_data)

# Policy Management
@app.route('/policies')
@login_required()
def policies():
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.username as provider_name
        FROM policies p
        JOIN users u ON p.policy_provider_id = u.id
        ORDER BY p.created_at DESC
    ''')
    policy_list = cursor.fetchall()
    conn.close()
    
    return render_template('policies.html', policies=policy_list)

@app.route('/purchase_policy/<int:policy_id>', methods=['GET', 'POST'])
@login_required()
def purchase_policy(policy_id):
    global blockchain
    if request.method == 'POST':
        conn = sqlite3.connect('insurance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM policies WHERE id = ?', (policy_id,))
        policy = cursor.fetchone()
        
        if policy:
            # Generate blockchain hash
            if blockchain is None:
                blockchain = Blockchain()
            blockchain_hash = blockchain.generate_transaction_hash(
                session['username'],
                policy[2],
                policy[4]
            )
            
            # Create user policy record
            cursor.execute('''
                INSERT INTO user_policies (user_id, policy_id, blockchain_hash, payment_status)
                VALUES (?, ?, ?, ?)
            ''', (session['user_id'], policy_id, blockchain_hash, 'paid'))
            
            conn.commit()
            flash(f'Policy purchased successfully! Blockchain Hash: {blockchain_hash}', 'success')
            return redirect(url_for('my_policies'))
        
        conn.close()
    
    return redirect(url_for('policies'))

@app.route('/my_policies')
@login_required()
def my_policies():
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT up.*, p.policy_name, p.policy_description, p.policy_cost
        FROM user_policies up
        JOIN policies p ON up.policy_id = p.id
        WHERE up.user_id = ?
        ORDER BY up.created_at DESC
    ''', (session['user_id'],))
    my_policies_list = cursor.fetchall()
    conn.close()
    
    return render_template('my_policies.html', policies=my_policies_list)

# Claim Management
@app.route('/file_claim/<int:user_policy_id>', methods=['GET', 'POST'])
@login_required()
def file_claim(user_policy_id):
    if request.method == 'POST':
        claim_amount = float(request.form['claim_amount'])
        
        # Handle file uploads
        accident_picture = None
        policy_document = None
        adhar_path = None
        vehicle_rc = None
        
        if 'accident_picture' in request.files:
            accident_file = request.files['accident_picture']
            if accident_file and allowed_file(accident_file.filename):
                filename = secure_filename(accident_file.filename)
                accident_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"accident_{user_policy_id}_{filename}"))
                accident_picture = f"accident_{user_policy_id}_{filename}"
        
        if 'policy_document' in request.files:
            policy_file = request.files['policy_document']
            if policy_file and allowed_file(policy_file.filename):
                filename = secure_filename(policy_file.filename)
                policy_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"claim_policy_{user_policy_id}_{filename}"))
                policy_document = f"claim_policy_{user_policy_id}_{filename}"
        
        if 'adhar' in request.files:
            adhar_file = request.files['adhar']
            if adhar_file and allowed_file(adhar_file.filename):
                filename = secure_filename(adhar_file.filename)
                adhar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"claim_adhar_{user_policy_id}_{filename}"))
                adhar_path = f"claim_adhar_{user_policy_id}_{filename}"
        
        if 'vehicle_rc' in request.files:
            rc_file = request.files['vehicle_rc']
            if rc_file and allowed_file(rc_file.filename):
                filename = secure_filename(rc_file.filename)
                rc_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"claim_rc_{user_policy_id}_{filename}"))
                vehicle_rc = f"claim_rc_{user_policy_id}_{filename}"
        
        # Create claim
        conn = sqlite3.connect('insurance.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO claims (user_policy_id, claim_amount, accident_picture_path, 
                              policy_document_path, adhar_path, vehicle_rc_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_policy_id, claim_amount, accident_picture, policy_document, adhar_path, vehicle_rc))
        
        conn.commit()
        conn.close()
        
        flash('Claim filed successfully!', 'success')
        return redirect(url_for('my_claims'))
    
    return render_template('file_claim.html', user_policy_id=user_policy_id)

@app.route('/my_claims')
@login_required()
def my_claims():
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, p.policy_name
        FROM claims c
        JOIN user_policies up ON c.user_policy_id = up.id
        JOIN policies p ON up.policy_id = p.id
        WHERE up.user_id = ?
        ORDER BY c.created_at DESC
    ''', (session['user_id'],))
    claims_list = cursor.fetchall()
    conn.close()
    
    return render_template('my_claims.html', claims=claims_list)

# Policy Provider Routes
@app.route('/add_policy', methods=['GET', 'POST'])
@login_required(role='policy_provider')
def add_policy():
    if request.method == 'POST':
        policy_name = request.form['policy_name']
        policy_description = request.form['policy_description']
        policy_cost = float(request.form['policy_cost'])
        required_documents = request.form['required_documents']
        
        conn = sqlite3.connect('insurance.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO policies (policy_provider_id, policy_name, policy_description,
                                policy_cost, required_documents)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], policy_name, policy_description, policy_cost, required_documents))
        conn.commit()
        conn.close()
        
        flash('Policy added successfully!', 'success')
        return redirect(url_for('my_policies_provided'))
    
    return render_template('add_policy.html')

@app.route('/my_policies_provided')
@login_required(role='policy_provider')
def my_policies_provided():
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, COUNT(up.id) as purchase_count,
               COALESCE(SUM(p.policy_cost), 0) as total_revenue
        FROM policies p
        LEFT JOIN user_policies up ON p.id = up.policy_id
        WHERE p.policy_provider_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (session['user_id'],))
    provided_policies = cursor.fetchall()
    conn.close()
    
    return render_template('my_policies_provided.html', policies=provided_policies)

@app.route('/get_policy_holders/<int:policy_id>')
@login_required(role='policy_provider')
def get_policy_holders(policy_id):
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.username, u.email, u.phone_number, up.blockchain_hash, up.created_at,
               up.payment_status
        FROM user_policies up
        JOIN users u ON up.user_id = u.id
        WHERE up.policy_id = ?
        ORDER BY up.created_at DESC
    ''', (policy_id,))
    
    holders = cursor.fetchall()
    conn.close()
    
    return jsonify({'holders': holders})

# Voting Member Routes
@app.route('/view_claims')
@login_required(role='voting_member')
def view_claims():
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    
    # Get all pending claims with voting status and whether current user has voted
    cursor.execute('''
        SELECT c.*, p.policy_name, u.username,
               (SELECT COUNT(*) FROM votes v WHERE v.claim_id = c.id) as vote_count,
               (SELECT COUNT(*) FROM votes v WHERE v.claim_id = c.id AND v.vote = 'approve') as approve_votes,
               CASE WHEN EXISTS (
                   SELECT 1 FROM votes v2 WHERE v2.claim_id = c.id AND v2.voting_member_id = ?
               ) THEN 1 ELSE 0 END as user_has_voted
        FROM claims c
        JOIN user_policies up ON c.user_policy_id = up.id
        JOIN policies p ON up.policy_id = p.id
        JOIN users u ON up.user_id = u.id
        WHERE c.claim_status = 'pending'
        ORDER BY c.created_at DESC
    ''', (session['user_id'],))
    claims_list = cursor.fetchall()
    conn.close()
    
    return render_template('view_claims.html', claims=claims_list)


@app.route('/vote_claim/<int:claim_id>/<action>')
@login_required(role='voting_member')
def vote_claim(claim_id, action):
    global blockchain
    if action not in ['approve', 'reject']:
        flash('Invalid vote action', 'error')
        return redirect(url_for('view_claims'))
    
    conn = sqlite3.connect('insurance.db')
    cursor = conn.cursor()
    
    # Check if user has already voted
    cursor.execute('''
        SELECT * FROM votes WHERE claim_id = ? AND voting_member_id = ?
    ''', (claim_id, session['user_id']))
    
    if cursor.fetchone():
        conn.close()
        flash('You have already voted on this claim', 'error')
        return redirect(url_for('view_claims'))
    
    # Add vote
    cursor.execute('''
        INSERT INTO votes (claim_id, voting_member_id, vote)
        VALUES (?, ?, ?)
    ''', (claim_id, session['user_id'], action))

    # Count total votes AFTER inserting the current one
    cursor.execute('''
        SELECT COUNT(*) FROM votes WHERE claim_id = ?
    ''', (claim_id,))
    total_votes = cursor.fetchone()[0]

    # Only make a decision once all 3 voting members have voted
    if total_votes >= 3:
        cursor.execute('''
            SELECT COUNT(*) FROM votes WHERE claim_id = ? AND vote = 'approve'
        ''', (claim_id,))
        approve_votes = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM votes WHERE claim_id = ? AND vote = 'reject'
        ''', (claim_id,))
        reject_votes = cursor.fetchone()[0]

        if approve_votes >= 2:
            # Approve the claim and generate blockchain hash
            cursor.execute('''
                UPDATE claims SET claim_status = 'approved' WHERE id = ?
            ''', (claim_id,))

            cursor.execute('''
                SELECT u.username, p.policy_name, c.claim_amount
                FROM claims c
                JOIN user_policies up ON c.user_policy_id = up.id
                JOIN users u ON up.user_id = u.id
                JOIN policies p ON up.policy_id = p.id
                WHERE c.id = ?
            ''', (claim_id,))
            claim_data = cursor.fetchone()

            if claim_data:
                if blockchain is None:
                    blockchain = Blockchain()
                blockchain_hash = blockchain.generate_transaction_hash(
                    claim_data[0],
                    claim_data[1],
                    claim_data[2]
                )
                cursor.execute('''
                    UPDATE claims SET blockchain_hash = ? WHERE id = ?
                ''', (blockchain_hash, claim_id))

        elif reject_votes >= 2:
            # Reject the claim
            cursor.execute('''
                UPDATE claims SET claim_status = 'rejected' WHERE id = ?
            ''', (claim_id,))

    conn.commit()
    conn.close()
    
    flash('Vote recorded successfully!', 'success')
    return redirect(url_for('view_claims'))

# File Download Route
@app.route('/download/<path:filename>')
@login_required()
def download_file(filename):
    """Download uploaded files"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('File not found', 'error')
            return redirect(request.referrer or url_for('dashboard'))
    except Exception as e:
        flash('Error downloading file', 'error')
        return redirect(request.referrer or url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    # Initialize blockchain after database is ready
    blockchain = Blockchain()
    app.run(debug=True)