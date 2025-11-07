# Hospital Management System

A Flask-based web application for managing hospital operations with role-based access for Admin, Doctor, and Patient users.

## Features

### Admin
- Manage doctors (add, view, update)
- Manage patients (view, update)
- View and manage all appointments
- Dashboard with system overview

### Doctor
- Set and update availability schedule
- View assigned appointments
- Complete appointments and add notes
- Access patient medical history
- Personal dashboard

### Patient
- Browse available doctors
- Book new appointments based on doctor availability
- View personal appointment history
- Manage profile information
- Personal dashboard

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```
   cd HospitalManagement
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Run the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and go to:
   ```
   http://localhost:5000
   ```

## Default Login Credentials

- **Admin**: 
  - Username: admin
  - Password: admin123

- **Doctor**:
  - Username: doctor
  - Password: doctor123

- **Patient**:
  - Username: patient
  - Password: patient123

## Project Structure

```
HospitalManagement/
├── templates/
│   ├── admin/         # Admin-specific pages
│   ├── doctor/        # Doctor-specific pages
│   ├── patient/       # Patient-specific pages
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── login.html     # Login page
│   └── register.html  # Registration page
├── app.py             # Main application file
├── models.py          # Database models
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Technologies Used

- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Werkzeug**: Password hashing
- **Flask-WTF**: Form handling and validation

## Database

The application uses SQLite as the database which is automatically created when you run the application for the first time.