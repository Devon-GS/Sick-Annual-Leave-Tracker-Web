# Employee Leave Management System

A robust Flask-based web application designed to track employee annual and sick leave. The system features automated balance calculations based on hire dates, medical certificate management, and an archival system for former employees.

## 🚀 Features

*   **Employee Management:** Add, edit, archive, and restore employee records.
*   **Annual Leave Tracking:** 
    *   Standard accrual: 1.25 days per month.
    *   Special accrual: 1.66 days per month for specific ID numbers.
*   **Sick Leave Logic:** 
    *   First 6 months: 6-day entitlement.
    *   After 6 months: 30 days per 36-month (3-year) cycle.
*   **Document Management:** Upload and view medical certificates (PDF, PNG, JPG, DOCX).
*   **Secure Authentication:** 
    *   Admin login with hashed passwords.
    *   Forced password change on first login.
*   **Data Persistence:** SQLite database storage.
*   **Docker Support:** Ready for containerized deployment.

---

## 🛠️ Installation & Local Setup

### Prerequisites
*   Python 3.8 or higher
*   Pip (Python package manager)

### Steps
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd leave-manager
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install Flask Werkzeug
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000`.

---

## 🐳 Docker Deployment

The application includes Docker support for easy hosting and environment consistency.

### Using Docker Compose
1.  **Build and start the container:**
    ```bash
    docker-compose up -d --build
    ```
---

## 🔐 Configuration

*   **Default Credentials:**
    *   **Username:** `admin`
    *   **Password:** `admin123` (System will prompt for a change on first login).
*   **Secret Key:** Set the `SECRET_KEY` environment variable in production for session security.
*   **Uploads:** Files are restricted to 5MB and specific extensions (`pdf`, `jpg`, `jpeg`, `png`, `doc`, `docx`).

---

## 📁 Project Structure

```text
.
├── app.py              # Main Flask application logic & API routes
├── Database/           # SQLite database storage (Auto-created)
├── uploads/            # Medical certificate storage (Auto-created)
├── templates/          # HTML files (index, login, change_password)
├── static/             # CSS and Frontend JavaScript (if applicable)
├── Dockerfile          # Docker configuration
└── README.md           # This file
```

---

## 📝 Technical Details

### Leave Calculation Logic
*   **Annual Leave:** Accrues monthly from the hire date. The system identifies specific IDs (e.g., `86013101`) to apply a higher accrual rate (20 days/year) vs. the standard (15 days/year).
*   **Sick Leave Cycle:** 
    *   The 36-month cycle starts exactly 180 days (6 months) after the hire date.
    *   Any leave taken during the first 6 months is deducted from the first 36-month cycle's 30-day allotment.

### API Endpoints
*   `GET /api/employees`: List all active employees and their current balances.
*   `POST /api/annual-leave`: Record a new annual leave entry.
*   `POST /api/sick-leave`: Record sick leave (supports `multipart/form-data` for file uploads).
*   `GET /api/archived-employees`: Retrieve records for deleted/archived staff.

---