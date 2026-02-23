# Here is a complete Python script to handle this.

# This script includes:

# Database Initialization: Creates the tables exactly as requested.

# CSV Generation (Optional): A helper function to create sample CSV files so you can test the script immediately.

# Import Logic:

# Uses csv.DictReader so column order doesn't matter.

# Crucial Logic: It maps the visible string employee_id (from the CSV) to the internal integer id (primary key) required by the Foreign Keys in the leave tables.

# Handles duplicate prevention for employees.

# The Python Script (bulk_import.py)

import sqlite3
import csv
import os
import sys
from datetime import datetime

# Configuration
# 1. Get the directory where this script is located
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Construct the full path
db_path = os.path.normpath(os.path.join(current_script_dir, "../../Database/leave_manager.db"))

DB_NAME = db_path

# --- Database Setup ---
def create_database():
    """Initializes the database with the required schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Enable Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.executescript("""
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
    """)
    conn.commit()
    return conn

# --- Date Formatting Helper ---
def clean_date(date_str):
    """
    Converts DD/MM/YYYY to YYYY-MM-DD so the database doesn't crash.
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Formats to try (Priority: SA/UK -> ISO -> US)
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    print(f"   ⚠️  Warning: Could not format date '{date_str}'. Inserting as is.")
    return date_str

# --- CSV Template Creation ---
def create_csv_templates():
    """Creates empty CSV files with headers only if they don't exist."""
    files_created = False
    
    # Employees
    if not os.path.exists('employees.csv'):
        with open('employees.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'employee_id', 'hire_date', 'is_archived'])
        print("📄 Created template: 'employees.csv'")
        files_created = True

    # Annual Leave
    if not os.path.exists('annual_leave.csv'):
        with open('annual_leave.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['employee_id', 'start_date', 'end_date', 'reason', 'days_used', 'status'])
        print("📄 Created template: 'annual_leave.csv'")
        files_created = True

    # Sick Leave
    if not os.path.exists('sick_leave.csv'):
        with open('sick_leave.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['employee_id', 'start_date', 'end_date', 'reason', 'days_used', 'medical_cert', 'status'])
        print("📄 Created template: 'sick_leave.csv'")
        files_created = True

    return files_created

# --- Import Logic ---
def get_employee_pk(cursor, emp_string_id):
    """Finds internal DB ID from string Employee ID."""
    cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (emp_string_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def run_import_process(conn):
    cursor = conn.cursor()
    
    # 1. Import Employees
    if os.path.exists('employees.csv'):
        print("\n📥 Importing Employees...")
        with open('employees.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    hire_date = clean_date(row['hire_date'])
                    cursor.execute("INSERT INTO employees (name, employee_id, hire_date, is_archived) VALUES (?, ?, ?, ?)", 
                                  (row['name'], row['employee_id'], hire_date, row.get('is_archived', 0)))
                    count += 1
                except sqlite3.IntegrityError:
                    print(f"   - Skipped duplicate: {row['employee_id']}")
                except Exception as e:
                    print(f"   - Error on row {row}: {e}")
            conn.commit()
            print(f"✅ Processed {count} employees.")

    # 2. Import Annual Leave
    if os.path.exists('annual_leave.csv'):
        print("\n📥 Importing Annual Leave...")
        with open('annual_leave.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                emp_pk = get_employee_pk(cursor, row['employee_id'])
                if emp_pk:
                    start = clean_date(row['start_date'])
                    end = clean_date(row['end_date'])
                    cursor.execute("INSERT INTO annualLeave (employee_id, start_date, end_date, reason, days_used, status) VALUES (?, ?, ?, ?, ?, ?)",
                                  (emp_pk, start, end, row.get('reason',''), row['days_used'], row.get('status', 'Approved')))
                    count += 1
                else:
                    print(f"   - ⚠️  Skipping: Employee ID '{row['employee_id']}' not found.")
            conn.commit()
            print(f"✅ Processed {count} annual leave records.")

    # 3. Import Sick Leave
    if os.path.exists('sick_leave.csv'):
        print("\n📥 Importing Sick Leave...")
        with open('sick_leave.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                emp_pk = get_employee_pk(cursor, row['employee_id'])
                if emp_pk:
                    start = clean_date(row['start_date'])
                    end = clean_date(row['end_date'])
                    cursor.execute("INSERT INTO sickLeave (employee_id, start_date, end_date, reason, days_used, medical_cert, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (emp_pk, start, end, row.get('reason',''), row['days_used'], row.get('medical_cert',''), row.get('status', 'Approved')))
                    count += 1
                else:
                    print(f"   - ⚠️  Skipping: Employee ID '{row['employee_id']}' not found.")
            conn.commit()
            print(f"✅ Processed {count} sick leave records.")

# --- Main Menu ---
if __name__ == "__main__":
    print("--- Bulk Import Tool ---")
    
    # 1. Setup DB
    conn = create_database()
    
    # 2. Check/Create CSVs
    files_created = create_csv_templates()
    
    if files_created:
        print("\nℹ️  New CSV templates were created.")
    else:
        print("\nℹ️  Existing CSV files found.")

    print("\nSelect an option:")
    print("1. Continue to Import (I have filled out the CSV files)")
    print("2. Quit (I need to fill out the CSV files now)")
    
    choice = input("\nYour choice (1 or 2): ").strip()
    
    if choice == '1':
        run_import_process(conn)
        conn.close()
        print("\n🎉 Import Complete.")
    elif choice == '2':
        conn.close()
        print("\n👋 Exiting. Please fill out 'employees.csv', 'annual_leave.csv', and 'sick_leave.csv' and run this script again.")
        sys.exit()
    else:
        conn.close()
        print("Invalid choice. Exiting.")

# Required CSV Formats

# To use this script, your CSV files must have headers that match the keys used in the script (order does not matter).

# 1. employees.csv
# name	employee_id	hire_date	is_archived
# John Doe	EMP001	2023-01-01	0
# 2. annual_leave.csv

# Note: Use the string employee_id (e.g., EMP001), the script will automatically find the internal integer ID.
# | employee_id | start_date | end_date | reason | days_used | status |
# | :--- | :--- | :--- | :--- | :--- | :--- |
# | EMP001 | 2023-10-01 | 2023-10-05 | Holiday | 5 | Approved |

# 3. sick_leave.csv
# employee_id	start_date	end_date	reason	days_used	medical_cert	status
# EMP001	2023-11-01	2023-11-02	Flu	2	doc.pdf	Approved
# How it works

# Duplicate Safety: If you try to import an employee with an employee_id that already exists, the script will skip it and warn you rather than crashing.

# Relational Integrity:

# The database stores an Integer ID for leave records (e.g., Employee ID 1).

# Humans/CSVs usually use String IDs (e.g., "EMP005").

# The get_employee_pk function translates "EMP005" -> 1 before inserting the leave record. If "EMP005" doesn't exist in the employees table, it skips the leave record to prevent database corruption.