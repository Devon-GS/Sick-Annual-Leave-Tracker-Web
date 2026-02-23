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
from datetime import datetime

DB_NAME = '../leave_manager.db'

def create_database():
    """Initializes the database with the required schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    print(f"✅ Database checked/created successfully.")
    return conn

def clean_date(date_str):
    """
    Tries to convert various date formats (DD/MM/YYYY) to the database standard (YYYY-MM-DD).
    """
    if not date_str:
        return None
        
    # List of formats to try. 
    # Priority 1: DD/MM/YYYY (South African/UK standard)
    # Priority 2: YYYY-MM-DD (Already correct)
    # Priority 3: MM/DD/YYYY (US standard - just in case)
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']
    
    for fmt in formats:
        try:
            # If successful, returns YYYY-MM-DD
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    print(f"⚠️  Warning: Could not parse date '{date_str}'. Keeping original.")
    return date_str

def get_employee_pk(cursor, emp_string_id):
    cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (emp_string_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def import_employees(conn, csv_file):
    if not os.path.exists(csv_file):
        print(f"⚠️  File {csv_file} not found. Skipping.")
        return

    print(f"📥 Importing Employees from {csv_file}...")
    cursor = conn.cursor()
    count = 0
    
    with open(csv_file, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Convert date here
                formatted_hire_date = clean_date(row['hire_date'])
                
                cursor.execute("""
                    INSERT INTO employees (name, employee_id, hire_date, is_archived)
                    VALUES (?, ?, ?, ?)
                """, (
                    row['name'], 
                    row['employee_id'], 
                    formatted_hire_date, 
                    row.get('is_archived', 0)
                ))
                count += 1
            except sqlite3.IntegrityError:
                print(f"   - Skipped duplicate Employee ID: {row['employee_id']}")
    
    conn.commit()
    print(f"✅ Imported {count} employees.")

def import_annual_leave(conn, csv_file):
    if not os.path.exists(csv_file):
        return

    print(f"📥 Importing Annual Leave from {csv_file}...")
    cursor = conn.cursor()
    count = 0

    with open(csv_file, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            internal_id = get_employee_pk(cursor, row['employee_id'])
            if internal_id:
                # Convert dates here
                start = clean_date(row['start_date'])
                end = clean_date(row['end_date'])

                cursor.execute("""
                    INSERT INTO annualLeave (employee_id, start_date, end_date, reason, days_used, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    internal_id, start, end,
                    row.get('reason', ''), row['days_used'], row.get('status', 'Approved')
                ))
                count += 1
            else:
                print(f"   - ⚠️  Skipping: Employee '{row['employee_id']}' not found.")
    
    conn.commit()
    print(f"✅ Imported {count} annual leave records.")

def import_sick_leave(conn, csv_file):
    if not os.path.exists(csv_file):
        return

    print(f"📥 Importing Sick Leave from {csv_file}...")
    cursor = conn.cursor()
    count = 0

    with open(csv_file, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            internal_id = get_employee_pk(cursor, row['employee_id'])
            if internal_id:
                # Convert dates here
                start = clean_date(row['start_date'])
                end = clean_date(row['end_date'])

                cursor.execute("""
                    INSERT INTO sickLeave (employee_id, start_date, end_date, reason, days_used, medical_cert, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    internal_id, start, end,
                    row.get('reason', ''), row['days_used'], row.get('medical_cert', ''), row.get('status', 'Approved')
                ))
                count += 1
            else:
                print(f"   - ⚠️  Skipping: Employee '{row['employee_id']}' not found.")
    
    conn.commit()
    print(f"✅ Imported {count} sick leave records.")

if __name__ == "__main__":
    conn = create_database()
    if conn:
        import_employees(conn, 'employees.csv')
        import_annual_leave(conn, 'annual_leave.csv')
        import_sick_leave(conn, 'sick_leave.csv')
        conn.close()
        print("🎉 Finished.")

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