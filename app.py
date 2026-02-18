from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import sqlite3
import os
import json

app = Flask(__name__)
app.config['DATABASE'] = 'leave_manager.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def get_db():
    """Get database connection"""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                password_changed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_id TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                email TEXT,
                phone TEXT
            );
            
            CREATE TABLE IF NOT EXISTS annualLeave (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT,
                days_used REAL NOT NULL,
                status TEXT DEFAULT 'Approved',
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS sickLeave (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT,
                days_used REAL NOT NULL,
                medical_cert TEXT,
                status TEXT DEFAULT 'Approved',
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
        ''')
        db.commit()
        
        # Create default admin user if it doesn't exist
        try:
            db.execute(
                'INSERT INTO users (username, password, password_changed) VALUES (?, ?, ?)',
                ('admin', generate_password_hash('admin123'), 0)
            )
            db.commit()
        except sqlite3.IntegrityError:
            pass

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Force password change if it hasn't been changed
        if session.get('force_password_change'):
            return redirect(url_for('change_password'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_annual_leave_balance(employee_id):
    """Calculate annual leave balance based on hire date and used days"""
    db = get_db()
    
    # Get employee hire date
    emp = db.execute(
        'SELECT hire_date FROM employees WHERE id = ?',
        (employee_id,)
    ).fetchone()
    
    if not emp:
        return 0, 0
    
    hire_date = datetime.strptime(emp['hire_date'], '%Y-%m-%d')
    today = datetime.now()
    months_employed = (today.year - hire_date.year) * 12 + (today.month - hire_date.month)
    
    # Calculate entitlement: 1.25 days per month
    entitlement = min(months_employed * 1.25, 30)  # Max 30 days per year
    
    # Get used days
    used = db.execute(
        'SELECT COALESCE(SUM(days_used), 0) as total FROM annualLeave WHERE employee_id = ? AND status = "Approved"',
        (employee_id,)
    ).fetchone()
    
    used_days = float(used['total']) if used else 0
    balance = entitlement - used_days
    
    return entitlement, balance

def calculate_sick_leave_balance(employee_id):
    """Calculate sick leave balance - 30 days per 36 months"""
    db = get_db()
    
    # Get employee hire date
    emp = db.execute(
        'SELECT hire_date FROM employees WHERE id = ?',
        (employee_id,)
    ).fetchone()
    
    if not emp:
        return 0, 0
    
    hire_date = datetime.strptime(emp['hire_date'], '%Y-%m-%d')
    today = datetime.now()
    months_employed = (today.year - hire_date.year) * 12 + (today.month - hire_date.month)
    
    # Calculate entitlement: 30 days per 36 months
    cycles = months_employed / 36
    entitlement = cycles * 30
    
    # Get used days
    used = db.execute(
        'SELECT COALESCE(SUM(days_used), 0) as total FROM sickLeave WHERE employee_id = ? AND status = "Approved"',
        (employee_id,)
    ).fetchone()
    
    used_days = float(used['total']) if used else 0
    balance = entitlement - used_days
    
    return entitlement, balance

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['password'], password):
            error = 'Invalid password'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Force password change on first login
            if not user['password_changed']:
                session['force_password_change'] = True
                return redirect(url_for('change_password'))
            
            return redirect(url_for('index'))
        
        return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change password - required on first login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        error = None
        
        if not new_password:
            error = 'New password is required'
        elif len(new_password) < 6:
            error = 'Password must be at least 6 characters long'
        elif new_password != confirm_password:
            error = 'Passwords do not match'
        
        if error is None:
            db = get_db()
            db.execute(
                'UPDATE users SET password = ?, password_changed = 1 WHERE id = ?',
                (generate_password_hash(new_password), session['user_id'])
            )
            db.commit()
            
            # Clear the force password change flag
            session.pop('force_password_change', None)
            return redirect(url_for('index'))
        
        return render_template('change_password.html', error=error, force_change=True)
    
    force_change = session.get('force_password_change', False)
    return render_template('change_password.html', force_change=force_change)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/employees', methods=['GET', 'POST'])
@login_required
def employees():
    """Get all employees or add new employee"""
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        try:
            cursor = db.execute(
                '''INSERT INTO employees (name, employee_id, department, hire_date, email, phone)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (data['name'], data['employee_id'], '', data['hire_date'], '', '')
            )
            db.commit()
            
            emp_id = cursor.lastrowid
            return jsonify({
                'id': emp_id,
                'name': data['name'],
                'employee_id': data['employee_id'],
                'department': '',
                'hire_date': data['hire_date'],
                'email': '',
                'phone': ''
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET - fetch all employees with leave balances
    employees_list = db.execute('SELECT * FROM employees ORDER BY name').fetchall()
    result = []
    
    for emp in employees_list:
        annual_ent, annual_bal = calculate_annual_leave_balance(emp['id'])
        sick_ent, sick_bal = calculate_sick_leave_balance(emp['id'])
        
        result.append({
            'id': emp['id'],
            'name': emp['name'],
            'employee_id': emp['employee_id'],
            'department': emp['department'],
            'hire_date': emp['hire_date'],
            'email': emp['email'],
            'phone': emp['phone'],
            'annual_leave_balance': round(annual_bal, 2),
            'annual_leave_entitlement': round(annual_ent, 2),
            'sick_leave_balance': round(sick_bal, 2),
            'sick_leave_entitlement': round(sick_ent, 2)
        })
    
    return jsonify(result), 200

@app.route('/api/employees/<int:emp_id>', methods=['PUT', 'DELETE'])
@login_required
def employee_detail(emp_id):
    """Update or delete employee"""
    db = get_db()
    
    if request.method == 'DELETE':
        try:
            db.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
            db.commit()
            return jsonify({'message': 'Employee deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    if request.method == 'PUT':
        data = request.json
        try:
            db.execute(
                '''UPDATE employees 
                   SET name = ?, employee_id = ?, hire_date = ?
                   WHERE id = ?''',
                (data['name'], data['employee_id'], data['hire_date'], emp_id)
            )
            db.commit()
            return jsonify({'message': 'Employee updated'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/annual-leave', methods=['GET', 'POST'])
@login_required
def annual_leave():
    """Get or add annual leave records"""
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        try:
            db.execute(
                '''INSERT INTO annualLeave (employee_id, start_date, end_date, reason, days_used, status)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (data['employee_id'], data['start_date'], data['end_date'], 
                 data.get('reason', ''), data['days_used'], data.get('status', 'Approved'))
            )
            db.commit()
            return jsonify({'message': 'Annual leave added'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET
    emp_id = request.args.get('employee_id')
    if emp_id:
        leaves = db.execute(
            '''SELECT a.id, a.employee_id, e.name as employee_name, a.start_date, a.end_date, 
                      a.reason, a.days_used, a.status 
               FROM annualLeave a
               LEFT JOIN employees e ON a.employee_id = e.id
               WHERE a.employee_id = ? 
               ORDER BY a.start_date DESC''',
            (emp_id,)
        ).fetchall()
    else:
        leaves = db.execute(
            '''SELECT a.id, a.employee_id, e.name as employee_name, a.start_date, a.end_date, 
                      a.reason, a.days_used, a.status 
               FROM annualLeave a
               LEFT JOIN employees e ON a.employee_id = e.id
               ORDER BY a.start_date DESC'''
        ).fetchall()
    
    result = [dict(leaf) for leaf in leaves]
    return jsonify(result), 200

@app.route('/api/annual-leave/<int:leave_id>', methods=['PUT', 'DELETE'])
@login_required
def annual_leave_detail(leave_id):
    """Update or delete annual leave"""
    db = get_db()
    
    if request.method == 'DELETE':
        try:
            db.execute('DELETE FROM annualLeave WHERE id = ?', (leave_id,))
            db.commit()
            return jsonify({'message': 'Annual leave deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    if request.method == 'PUT':
        data = request.json
        try:
            db.execute(
                '''UPDATE annualLeave 
                   SET start_date = ?, end_date = ?, reason = ?, days_used = ?, status = ?
                   WHERE id = ?''',
                (data['start_date'], data['end_date'], data.get('reason', ''), 
                 data['days_used'], data.get('status', 'Approved'), leave_id)
            )
            db.commit()
            return jsonify({'message': 'Annual leave updated'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/sick-leave', methods=['GET', 'POST'])
@login_required
def sick_leave():
    """Get or add sick leave records"""
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        try:
            db.execute(
                '''INSERT INTO sickLeave (employee_id, start_date, end_date, reason, days_used, medical_cert, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (data['employee_id'], data['start_date'], data['end_date'], 
                 data.get('reason', ''), data['days_used'], data.get('medical_cert', ''), 
                 data.get('status', 'Approved'))
            )
            db.commit()
            return jsonify({'message': 'Sick leave added'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET
    emp_id = request.args.get('employee_id')
    if emp_id:
        leaves = db.execute(
            '''SELECT s.id, s.employee_id, e.name as employee_name, s.start_date, s.end_date, 
                      s.reason, s.days_used, s.medical_cert, s.status 
               FROM sickLeave s
               LEFT JOIN employees e ON s.employee_id = e.id
               WHERE s.employee_id = ? 
               ORDER BY s.start_date DESC''',
            (emp_id,)
        ).fetchall()
    else:
        leaves = db.execute(
            '''SELECT s.id, s.employee_id, e.name as employee_name, s.start_date, s.end_date, 
                      s.reason, s.days_used, s.medical_cert, s.status 
               FROM sickLeave s
               LEFT JOIN employees e ON s.employee_id = e.id
               ORDER BY s.start_date DESC'''
        ).fetchall()
    
    result = [dict(leaf) for leaf in leaves]
    return jsonify(result), 200

@app.route('/api/sick-leave/<int:leave_id>', methods=['PUT', 'DELETE'])
@login_required
def sick_leave_detail(leave_id):
    """Update or delete sick leave"""
    db = get_db()
    
    if request.method == 'DELETE':
        try:
            db.execute('DELETE FROM sickLeave WHERE id = ?', (leave_id,))
            db.commit()
            return jsonify({'message': 'Sick leave deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    if request.method == 'PUT':
        data = request.json
        try:
            db.execute(
                '''UPDATE sickLeave 
                   SET start_date = ?, end_date = ?, reason = ?, days_used = ?, medical_cert = ?, status = ?
                   WHERE id = ?''',
                (data['start_date'], data['end_date'], data.get('reason', ''), 
                 data['days_used'], data.get('medical_cert', ''), data.get('status', 'Approved'), leave_id)
            )
            db.commit()
            return jsonify({'message': 'Sick leave updated'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/view-leave', methods=['GET'])
@login_required
def view_leave():
    """Get all leave records with employee info"""
    db = get_db()
    
    # Get all annual leave with employee names
    annual = db.execute('''
        SELECT a.id, a.employee_id, a.start_date, a.end_date, a.reason, a.days_used, a.status,
               e.name as employee_name, e.employee_id as emp_number FROM annualLeave a
        JOIN employees e ON a.employee_id = e.id
        ORDER BY a.start_date DESC
    ''').fetchall()
    
    # Get all sick leave with employee names
    sick = db.execute('''
        SELECT s.id, s.employee_id, s.start_date, s.end_date, s.reason, s.days_used, s.medical_cert, s.status,
               e.name as employee_name, e.employee_id as emp_number FROM sickLeave s
        JOIN employees e ON s.employee_id = e.id
        ORDER BY s.start_date DESC
    ''').fetchall()
    
    return jsonify({
        'annual': [dict(row) for row in annual],
        'sick': [dict(row) for row in sick]
    }), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
