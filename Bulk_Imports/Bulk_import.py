import sqlite3
import csv
import os
import sys
from datetime import datetime

# Ensure the script always runs in the folder where the Python file is located
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_NAME = "leave_manager.db"


# --- Database Setup ---
def create_database():
    """Initializes the database with the required schema."""
    con = sqlite3.connect(DB_NAME)
    c = con.cursor()

    # Enable Foreign Keys
    c.execute("PRAGMA foreign_keys = ON;")

    c.executescript("""
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
    con.commit()
    return con


# --- Date Formatting Helper ---
def clean_date(date_str):
    """Converts DD/MM/YYYY to YYYY-MM-DD so the database doesn't crash."""
    if not date_str:
        return None

    date_str = str(date_str).strip()

    formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    print(f"   ⚠️  Warning: Could not format date '{date_str}'. Inserting as is.")
    return date_str


# --- CSV Template Creation ---
def create_csv_templates():
    """Creates empty CSV files with headers only if they don't exist."""
    files_created = False

    # Used utf-8-sig to handle Excel files correctly
    if not os.path.exists("employees.csv"):
        with open("employees.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "employee_id", "hire_date", "is_archived"])
        print("📄 Created template: 'employees.csv'")
        files_created = True

    if not os.path.exists("annual_leave.csv"):
        with open("annual_leave.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "employee_id",
                    "start_date",
                    "end_date",
                    "reason",
                    "days_used",
                    "status",
                ]
            )
        print("📄 Created template: 'annual_leave.csv'")
        files_created = True

    if not os.path.exists("sick_leave.csv"):
        with open("sick_leave.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "employee_id",
                    "start_date",
                    "end_date",
                    "reason",
                    "days_used",
                    "medical_cert",
                    "status",
                ]
            )
        print("📄 Created template: 'sick_leave.csv'")
        files_created = True

    return files_created


# --- Import Logic ---
def get_employee_pk(cursor, emp_string_id):
    """Finds internal DB ID from string Employee ID."""
    if not emp_string_id:
        return None
    cursor.execute(
        "SELECT id FROM employees WHERE employee_id = ?", (emp_string_id.strip(),)
    )
    result = cursor.fetchone()
    return result[0] if result else None


# Helper to remove accidental leading spaces in CSV headers
def strip_dict_keys(row):
    return {k.strip(): str(v).strip() for k, v in row.items() if k is not None}


def run_import_process(conn):
    cursor = conn.cursor()

    # 1. Import Employees
    if os.path.exists("employees.csv"):
        print("\n📥 Importing Employees...")
        # utf-8-sig strips hidden Excel BOM characters
        with open("employees.csv", mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            for raw_row in reader:
                row = strip_dict_keys(raw_row)
                if not row.get("employee_id"):
                    continue  # Skip totally blank rows

                try:
                    hire_date = clean_date(row.get("hire_date"))
                    is_archived = (
                        row.get("is_archived") if row.get("is_archived") != "" else 0
                    )

                    cursor.execute(
                        "INSERT INTO employees (name, employee_id, hire_date, is_archived) VALUES (?, ?, ?, ?)",
                        (row["name"], row["employee_id"], hire_date, is_archived),
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    print(f"   - ⚠️  Skipped duplicate: {row.get('employee_id')}")
                except Exception as e:
                    print(f"   - ❌ Error on row {row}: {e}")
            conn.commit()
            print(f"✅ Processed {count} employees.")

    # 2. Import Annual Leave
    if os.path.exists("annual_leave.csv"):
        print("\n📥 Importing Annual Leave...")
        with open("annual_leave.csv", mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            for raw_row in reader:
                row = strip_dict_keys(raw_row)
                if not row.get("employee_id"):
                    continue

                emp_pk = get_employee_pk(cursor, row["employee_id"])
                if emp_pk:
                    try:
                        start = clean_date(row.get("start_date"))
                        end = clean_date(row.get("end_date"))
                        status = row.get("status") if row.get("status") else "Approved"

                        cursor.execute(
                            "INSERT INTO annualLeave (employee_id, start_date, end_date, reason, days_used, status) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                emp_pk,
                                start,
                                end,
                                row.get("reason", ""),
                                row.get("days_used", 0),
                                status,
                            ),
                        )
                        count += 1
                    except Exception as e:
                        print(f"   - ❌ Error on row {row}: {e}")
                else:
                    print(
                        f"   - ⚠️  Skipping: Employee ID '{row['employee_id']}' not found in Database."
                    )
            conn.commit()
            print(f"✅ Processed {count} annual leave records.")

    # 3. Import Sick Leave
    if os.path.exists("sick_leave.csv"):
        print("\n📥 Importing Sick Leave...")
        with open("sick_leave.csv", mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            for raw_row in reader:
                row = strip_dict_keys(raw_row)
                if not row.get("employee_id"):
                    continue

                emp_pk = get_employee_pk(cursor, row["employee_id"])
                if emp_pk:
                    try:
                        start = clean_date(row.get("start_date"))
                        end = clean_date(row.get("end_date"))
                        status = row.get("status") if row.get("status") else "Approved"

                        cursor.execute(
                            "INSERT INTO sickLeave (employee_id, start_date, end_date, reason, days_used, medical_cert, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                emp_pk,
                                start,
                                end,
                                row.get("reason", ""),
                                row.get("days_used", 0),
                                row.get("medical_cert", ""),
                                status,
                            ),
                        )
                        count += 1
                    except Exception as e:
                        print(f"   - ❌ Error on row {row}: {e}")
                else:
                    print(
                        f"   - ⚠️  Skipping: Employee ID '{row['employee_id']}' not found in Database."
                    )
            conn.commit()
            print(f"✅ Processed {count} sick leave records.")


# --- Main Menu ---
if __name__ == "__main__":
    print("--- Bulk Import Tool ---")

    conn = create_database()
    files_created = create_csv_templates()

    if files_created:
        print("\nℹ️  New CSV templates were created in:", os.getcwd())
    else:
        print("\nℹ️  Existing CSV files found in:", os.getcwd())

    print("\nSelect an option:")
    print("1. Continue to Import (I have filled out the CSV files)")
    print("2. Quit (I need to fill out the CSV files now)")

    choice = input("\nYour choice (1 or 2): ").strip()

    if choice == "1":
        run_import_process(conn)
        conn.close()
        print("\n🎉 Import Complete.")
        input("Press Enter to exit...")
    elif choice == "2":
        conn.close()
        print(
            f"\n👋 Exiting. Please fill out the CSVs located in {os.getcwd()} and run this script again."
        )
        input("Press Enter to exit...")
        sys.exit()
    else:
        conn.close()
        print("Invalid choice. Exiting.")
