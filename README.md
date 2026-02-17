# Employee Leave Manager - Flask Web App

A web-based application for managing employee annual leave and sick leave records.

## Features

- **Employee Management**: Add, edit, and delete employees with their basic information
- **Annual Leave Tracking**: Manage annual leave records with automatic balance calculation (1.25 days/month)
- **Sick Leave Tracking**: Manage sick leave records with automatic balance calculation (30 days per 36 months)
- **Leave Reports**: View all leave records by employee or leave type
- **Leave Balance**: Automatic calculation of remaining leave balance based on hire date and used days

## Requirements

- Python 3.7+
- Flask 3.0.0

## Installation

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### First Login

On the first login, you must change the default admin password:
- Default username: `admin`
- Default password: `admin123`

After logging in, you will be redirected to a mandatory password change screen. This is a security requirement before accessing the application dashboard.

## Database

The application uses SQLite3 for data storage. The database is automatically created on first run with the following tables:
- `employees`: Employee information
- `annualLeave`: Annual leave records
- `sickLeave`: Sick leave records

## Usage

1. **Add Employees**: Go to the Employees tab and click "Add Employee" to create new employee records
2. **Add Leave**: Use the Annual Leave or Sick Leave tabs to add leave records for employees
3. **View Leave**: Use the "View All Leave" tab to see a complete report of all leave records
4. **Edit/Delete**: Click the edit button next to any record to modify or delete it

## Leave Balance Calculation

### Annual Leave
- Entitlement: 1.25 days per month employed
- Maximum: 30 days per year
- Balance = Entitlement - Used Days

### Sick Leave
- Entitlement: 30 days per 36 months employed
- Balance = Entitlement - Used Days
