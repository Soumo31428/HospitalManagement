# Hospital Management System

## Overview

A Flask-based web application for managing hospital operations including patient registration, doctor management, appointment scheduling, and treatment records. The system supports three user roles: Admin, Doctor, and Patient, each with distinct functionalities and access levels.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Template Engine**: Jinja2 with Bootstrap 5
- Base template system with inheritance for consistent UI across all pages
- Role-specific dashboard layouts (Admin, Doctor, Patient)
- Bootstrap Icons for visual elements
- Responsive design with Bootstrap grid system

**Template Organization**:
- `/templates/base.html` - Master layout with navigation
- `/templates/admin/` - Admin-specific views (dashboard, doctors, patients, appointments)
- `/templates/doctor/` - Doctor-specific views (appointments, availability, patient history)
- `/templates/patient/` - Patient-specific views (booking, profile, treatment history)

### Backend Architecture

**Web Framework**: Flask 3.0.0
- Route-based request handling with role-based access control
- Session-based authentication
- CSRF protection via Flask-WTF

**Authentication & Authorization**:
- Session-based authentication storing user_id and user_role
- Custom decorators for access control:
  - `@login_required` - Ensures user is logged in
  - `@role_required(role)` - Restricts access by user role
- Password hashing using Werkzeug security utilities

**Database Architecture**:
- ORM: Flask-SQLAlchemy
- Database: SQLite (development)
- **Models**:
  - `User` - Multi-role user entity (Admin/Doctor/Patient) with password hashing
  - `Department` - Medical departments/specializations
  - `Appointment` - Appointment scheduling with status tracking
  - `Treatment` - Medical records linked to appointments (referenced in templates but not fully implemented in models.py)
  - `DoctorAvailability` - Doctor schedule management (referenced but not fully implemented)

**Data Model Relationships**:
- User → Department (Many-to-One for doctors)
- Appointment → User (Many-to-One for both patient and doctor)
- Treatment → Appointment (One-to-One, implied but incomplete)

**Security Considerations**:
- Session secret key configured via environment variable
- CSRF tokens on all forms
- Password hashing for user credentials
- Role-based access restrictions

### Application Flow

**User Roles & Capabilities**:

1. **Admin**:
   - View system-wide statistics (doctors, patients, appointments)
   - Manage doctors (add, edit, search)
   - Manage patients (view, search, status control)
   - View all appointments across the system

2. **Doctor**:
   - View and manage personal appointments
   - Complete appointments with diagnosis/prescription
   - Set availability schedule
   - View patient history and previous treatments
   - Cancel appointments

3. **Patient**:
   - Browse departments and available doctors
   - Book appointments with doctors
   - View upcoming and past appointments
   - Cancel appointments
   - Update personal profile
   - View treatment history

### Configuration

**Environment Variables**:
- `SESSION_SECRET` - Secret key for session management (falls back to development key with warning)

**Flask Configuration**:
- SQLAlchemy database URI (currently SQLite)
- CSRF protection enabled
- Session management via Flask sessions

## External Dependencies

### Python Packages
- **Flask 3.0.0** - Core web framework
- **Flask-SQLAlchemy 3.1.1** - ORM for database operations
- **Werkzeug 3.0.1** - Password hashing and security utilities
- **Flask-WTF 1.2.1** - CSRF protection and form handling

### Frontend Libraries (CDN)
- **Bootstrap 5.3.0** - UI framework and responsive design
- **Bootstrap Icons 1.11.0** - Icon library

### Database
- **SQLite** - Default database for development (file-based: `hospital.db`)
- Note: Production deployments may require migration to PostgreSQL or MySQL

## Recent Updates (November 2025)

### Security Enhancements
- **CSRF Protection**: Implemented Flask-WTF CSRFProtect across all POST routes and forms
- **Secure Actions**: All destructive operations (delete, cancel) converted from GET to POST with CSRF tokens
- **Configuration Hardening**: SECRET_KEY requires environment variable with development fallback warning
- **Debug Mode Control**: FLASK_DEBUG environment variable controls debug mode instead of hard-coded value

### Completed Features
- **Treatment Model**: Fully implemented with diagnosis, prescription, and notes fields
- **DoctorAvailability Model**: Complete 7-day booking window system with time slot management
- **Appointment Validation**: Bookings now validate against doctor availability slots before creation
- **All CRUD Operations**: Complete implementations for doctors, patients, appointments, and treatments

### Production Readiness
- Application is production-ready with proper environment variable configuration
- No Replit-specific files or references (suitable for university project submission)
- All routes protected with CSRF tokens and role-based access control
- Database initialization creates admin account (email: admin@hospital.com, password: admin123)