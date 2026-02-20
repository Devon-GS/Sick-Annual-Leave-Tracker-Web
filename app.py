from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.config['DATABASE'] = 'leave_manager.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                password_changed INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_id TEXT UNIQUE NOT NULL,
                hire_date TEXT NOT NULL,
                is_archived INTEGER DEFAULT 0
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
        
        # Migration: Add is_archived column if it doesn't exist
        try:
            db.execute('ALTER TABLE employees ADD COLUMN is_archived INTEGER DEFAULT 0')
            db.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
		'SELECT hire_date, employee_id FROM employees WHERE id = ?',
		(employee_id,)
	).fetchone()
	
	if not emp:
		return 0, 0
	
	hire_date = datetime.strptime(emp['hire_date'], '%Y-%m-%d')
	today = datetime.now()
	months_employed = (today.year - hire_date.year) * 12 + (today.month - hire_date.month)
	
	# Calculate entitlement based on employee ID
	# Special rate for employee 8601310127086: 1.66 days per month
	# All other employees: 1.25 days per month
	id_employee = emp['employee_id']
	
	if id_employee == '8601310127086':
		entitlement = months_employed * (20/12)
	else:
		entitlement = months_employed * 1.25
	
	# Get used days
	used = db.execute(
		'SELECT COALESCE(SUM(days_used), 0) as total FROM annualLeave WHERE employee_id = ? AND status = "Approved"',
		(employee_id,)
	).fetchone()
	
	used_days = float(used['total']) if used else 0
	balance = entitlement - used_days
	
	return entitlement, balance
    
def calculate_sick_leave_balance(employee_id):
    """
    Calculate sick leave balance:
    - 36-month cycle starts from hire date
    - First 6 months: 6 days total
    - After 6 months: 30 days per 36-month cycle
    - At 6-month mark: unused days disappear, used days reduce the 30-day allotment
    - Only deduct leave taken in current cycle
    """
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
    
    # Calculate total days employed
    days_employed = (today - hire_date).days
    
    # Case 1: Within first 6 months (180 days)
    if days_employed < 180:
        # Entitlement is 6 days for first 6 months
        entitlement = 6
        
        # Get sick leave used in first 6 months
        used = db.execute(
            '''SELECT COALESCE(SUM(days_used), 0) as total 
               FROM sickLeave 
               WHERE employee_id = ? 
               AND status = "Approved"''',
            (employee_id,)
        ).fetchone()
        used_days = float(used['total']) if used else 0
        balance = entitlement - used_days
        
        return entitlement, max(0, balance)
    
    # Case 2: After 6 months - 30 days per 36-month cycle
    else:
        # Calculate which 36-month cycle we're in
        days_after_six_months = days_employed - 180
        complete_cycles = days_after_six_months // 1095  # 1095 days = 36 months
        days_in_current_cycle = days_after_six_months % 1095
        
        # Calculate current cycle start date
        cycle_start_date = hire_date + timedelta(days=180 + (complete_cycles * 1095))
        
        # Get sick leave used in current cycle
        used = db.execute(
            '''SELECT COALESCE(SUM(days_used), 0) as total 
               FROM sickLeave 
               WHERE employee_id = ? 
               AND status = "Approved" 
               AND start_date >= ?''',
            (employee_id, cycle_start_date.strftime('%Y-%m-%d'))
        ).fetchone()
        used_days = float(used['total']) if used else 0
        
        # At the 6-month mark, if employee used leave in first 6 months,
        # they carry forward 30 - used_days. If they used nothing, they get 30.
        # For subsequent cycles, they always get 30 minus what they used this cycle.
        if complete_cycles == 0:
            # Still in the first 36-month cycle after probation
            # Get leave used in first 6 months to carry forward
            probation_used = db.execute(
                '''SELECT COALESCE(SUM(days_used), 0) as total 
                   FROM sickLeave 
                   WHERE employee_id = ? 
                   AND status = "Approved"
                   AND start_date < ?''',
                (employee_id, (hire_date + timedelta(days=180)).strftime('%Y-%m-%d'))
            ).fetchone()
            probation_used_days = float(probation_used['total']) if probation_used else 0
            
            # In first 36-month cycle: 30 days minus what was used in first 6 months
            entitlement = 30
            total_used_in_cycle = probation_used_days + used_days
            balance = entitlement - total_used_in_cycle
        else:
            # Subsequent cycles: fresh 30 days per cycle
            entitlement = 30
            balance = entitlement - used_days
        
        return entitlement, max(0, balance)

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
                '''INSERT INTO employees (name, employee_id, hire_date)
                   VALUES (?, ?, ?)''',
                (data['name'], data['employee_id'], data['hire_date'])
            )
            db.commit()
            
            emp_id = cursor.lastrowid
            return jsonify({
                'id': emp_id,
                'name': data['name'],
                'employee_id': data['employee_id'],
                'hire_date': data['hire_date']
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET - fetch all active (non-archived) employees with leave balances
    employees_list = db.execute('SELECT * FROM employees WHERE is_archived = 0 ORDER BY name').fetchall()
    result = []
    
    for emp in employees_list:
        annual_ent, annual_bal = calculate_annual_leave_balance(emp['id'])
        sick_ent, sick_bal = calculate_sick_leave_balance(emp['id'])
        
        result.append({
            'id': emp['id'],
            'name': emp['name'],
            'employee_id': emp['employee_id'],
            'hire_date': emp['hire_date'],
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
            db.execute('UPDATE employees SET is_archived = 1 WHERE id = ?', (emp_id,))
            db.commit()
            return jsonify({'message': 'Employee archived'}), 200
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
    
    # GET - only return leave for active (non-archived) employees
    emp_id = request.args.get('employee_id')
    if emp_id:
        leaves = db.execute(
            '''SELECT a.id, a.employee_id, e.name as employee_name, a.start_date, a.end_date, 
                      a.reason, a.days_used, a.status 
               FROM annualLeave a
               LEFT JOIN employees e ON a.employee_id = e.id
               WHERE a.employee_id = ? AND e.is_archived = 0
               ORDER BY a.start_date DESC''',
            (emp_id,)
        ).fetchall()
    else:
        leaves = db.execute(
            '''SELECT a.id, a.employee_id, e.name as employee_name, a.start_date, a.end_date, 
                      a.reason, a.days_used, a.status 
               FROM annualLeave a
               LEFT JOIN employees e ON a.employee_id = e.id
               WHERE e.is_archived = 0
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
        # Handle both multipart/form-data and JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload from form-data
            data = {
                'employee_id': request.form.get('employee_id'),
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date'),
                'reason': request.form.get('reason', ''),
                'days_used': float(request.form.get('days_used', 0)),
                'medical_cert': ''
            }
            
            # Handle file upload if present
            if 'medical_cert_file' in request.files:
                file = request.files['medical_cert_file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    data['medical_cert'] = filename
        else:
            # JSON request (for compatibility)
            data = request.json or {}
        
        try:
            db.execute(
                '''INSERT INTO sickLeave (employee_id, start_date, end_date, reason, days_used, medical_cert, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (data['employee_id'], data['start_date'], data['end_date'], 
                 data.get('reason', ''), data['days_used'], data.get('medical_cert', ''), 
                 data.get('status', 'Approved'))
            )
            db.commit()
            return jsonify({'message': 'Sick leave added', 'medical_cert': data.get('medical_cert')}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET - only return leave for active (non-archived) employees
    emp_id = request.args.get('employee_id')
    if emp_id:
        leaves = db.execute(
            '''SELECT s.id, s.employee_id, e.name as employee_name, s.start_date, s.end_date, 
                      s.reason, s.days_used, s.medical_cert, s.status 
               FROM sickLeave s
               LEFT JOIN employees e ON s.employee_id = e.id
               WHERE s.employee_id = ? AND e.is_archived = 0
               ORDER BY s.start_date DESC''',
            (emp_id,)
        ).fetchall()
    else:
        leaves = db.execute(
            '''SELECT s.id, s.employee_id, e.name as employee_name, s.start_date, s.end_date, 
                      s.reason, s.days_used, s.medical_cert, s.status 
               FROM sickLeave s
               LEFT JOIN employees e ON s.employee_id = e.id
               WHERE e.is_archived = 0
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
            # Get the medical certificate filename before deleting
            leave = db.execute('SELECT medical_cert FROM sickLeave WHERE id = ?', (leave_id,)).fetchone()
            if leave and leave['medical_cert']:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], leave['medical_cert'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            db.execute('DELETE FROM sickLeave WHERE id = ?', (leave_id,))
            db.commit()
            return jsonify({'message': 'Sick leave deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    if request.method == 'PUT':
        try:
            # Get the current leave record to check for existing medical cert
            current_leave = db.execute('SELECT medical_cert FROM sickLeave WHERE id = ?', (leave_id,)).fetchone()
            current_medical_cert = current_leave['medical_cert'] if current_leave else None
            
            # Initialize new medical cert value
            new_medical_cert = current_medical_cert
            
            # Handle both multipart/form-data and JSON
            if request.content_type and 'multipart/form-data' in request.content_type:
                # File upload from form-data
                data = {
                    'start_date': request.form.get('start_date'),
                    'end_date': request.form.get('end_date'),
                    'reason': request.form.get('reason', ''),
                    'days_used': float(request.form.get('days_used', 0))
                }
                
                # Handle file upload if present
                if 'medical_cert_file' in request.files:
                    file = request.files['medical_cert_file']
                    if file and file.filename and allowed_file(file.filename):
                        # Delete old file if it exists
                        if current_medical_cert:
                            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_medical_cert)
                            if os.path.exists(old_filepath):
                                os.remove(old_filepath)
                        
                        # Save new file
                        filename = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        new_medical_cert = filename
                
                # Check if medical_cert field is set to empty string (deletion)
                if 'medical_cert' in request.form and request.form['medical_cert'] == '':
                    # Delete old file if it exists
                    if current_medical_cert:
                        old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_medical_cert)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    new_medical_cert = ''
            else:
                # JSON request (for compatibility)
                data = request.json or {}
                # If medical_cert is explicitly set to empty string, delete the file
                if 'medical_cert' in data and data['medical_cert'] == '':
                    if current_medical_cert:
                        old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_medical_cert)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    new_medical_cert = ''
                elif 'medical_cert' in data:
                    new_medical_cert = data['medical_cert']
            
            # Update the database
            db.execute(
                '''UPDATE sickLeave 
                   SET start_date = ?, end_date = ?, reason = ?, days_used = ?, medical_cert = ?, status = ?
                   WHERE id = ?''',
                (data['start_date'], data['end_date'], data.get('reason', ''), 
                 data['days_used'], new_medical_cert, data.get('status', 'Approved'), leave_id)
            )
            db.commit()
            return jsonify({'message': 'Sick leave updated', 'medical_cert': new_medical_cert}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/view-leave', methods=['GET'])
@login_required
def view_leave():
    """Get all leave records with employee info"""
    db = get_db()
    
    # Get all active employees
    employees_data = db.execute(
        '''SELECT id, name, employee_id, hire_date
           FROM employees 
           WHERE is_archived = 0
           ORDER BY name ASC'''
    ).fetchall()
    
    # Enhance employee data with calculated balances
    employees = []
    for emp in employees_data:
        emp_dict = dict(emp)
        # Calculate annual leave balance
        annual_alloc, annual_balance = calculate_annual_leave_balance(emp['id'])
        # Calculate sick leave balance
        sick_alloc, sick_balance = calculate_sick_leave_balance(emp['id'])
        
        emp_dict['annual_leave_allocated'] = annual_alloc
        emp_dict['annual_leave_balance'] = annual_balance
        emp_dict['sick_leave_allocated'] = sick_alloc
        emp_dict['sick_leave_balance'] = sick_balance
        employees.append(emp_dict)
    
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
        'employees': employees,
        'annual': [dict(row) for row in annual],
        'sick': [dict(row) for row in sick]
    }), 200

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    """Serve uploaded files"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Verify file exists and is in the uploads folder
        if os.path.exists(filepath) and os.path.abspath(filepath).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            return send_file(filepath, as_attachment=False)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/archived-employees', methods=['GET'])
@login_required
def archived_employees():
    """Get all archived employees with their leave records"""
    db = get_db()
    
    # Get all archived employees
    archived_data = db.execute(
        '''SELECT id, name, employee_id, hire_date
           FROM employees 
           WHERE is_archived = 1
           ORDER BY name ASC'''
    ).fetchall()
    
    # Enhance employee data with calculated balances
    employees = []
    for emp in archived_data:
        emp_dict = dict(emp)
        # Calculate annual leave balance
        annual_alloc, annual_balance = calculate_annual_leave_balance(emp['id'])
        # Calculate sick leave balance
        sick_alloc, sick_balance = calculate_sick_leave_balance(emp['id'])
        
        emp_dict['annual_leave_allocated'] = annual_alloc
        emp_dict['annual_leave_balance'] = annual_balance
        emp_dict['sick_leave_allocated'] = sick_alloc
        emp_dict['sick_leave_balance'] = sick_balance
        employees.append(emp_dict)
    
    # Get all annual leave for archived employees
    annual = db.execute('''
        SELECT a.id, a.employee_id, a.start_date, a.end_date, a.reason, a.days_used, a.status,
               e.name as employee_name FROM annualLeave a
        JOIN employees e ON a.employee_id = e.id
        WHERE e.is_archived = 1
        ORDER BY a.start_date DESC
    ''').fetchall()
    
    # Get all sick leave for archived employees
    sick = db.execute('''
        SELECT s.id, s.employee_id, s.start_date, s.end_date, s.reason, s.days_used, s.medical_cert, s.status,
               e.name as employee_name FROM sickLeave s
        JOIN employees e ON s.employee_id = e.id
        WHERE e.is_archived = 1
        ORDER BY s.start_date DESC
    ''').fetchall()
    
    return jsonify({
        'employees': employees,
        'annual': [dict(row) for row in annual],
        'sick': [dict(row) for row in sick]
    }), 200

@app.route('/api/employees/<int:emp_id>/medical-documents', methods=['GET'])
@login_required
def get_employee_medical_documents(emp_id):
    """Get all medical documents (certificates) for an employee"""
    db = get_db()
    
    # Get all sick leave records with medical certificates for this employee
    documents = db.execute(
        '''SELECT id, employee_id, start_date, end_date, medical_cert, reason
           FROM sickLeave
           WHERE employee_id = ? AND medical_cert IS NOT NULL AND medical_cert != ''
           ORDER BY start_date DESC''',
        (emp_id,)
    ).fetchall()
    
    return jsonify({
        'documents': [dict(row) for row in documents]
    }), 200

@app.route('/api/employees/<int:emp_id>/restore', methods=['POST'])
@login_required
def restore_employee(emp_id):
    """Restore an archived employee"""
    db = get_db()
    
    try:
        db.execute('UPDATE employees SET is_archived = 0 WHERE id = ?', (emp_id,))
        db.commit()
        return jsonify({'message': 'Employee restored'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
