from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from models import db, User, Department, Appointment, Treatment, DoctorAvailability
from datetime import datetime, timedelta, date, time
from functools import wraps
import os

app = Flask(__name__)

if not os.environ.get('SESSION_SECRET'):
    print("WARNING: SESSION_SECRET not set. Using development key. DO NOT USE IN PRODUCTION!")
    app.config['SECRET_KEY'] = 'development-key-please-change'
else:
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True

csrf = CSRFProtect(app)
db.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if not user or user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'Doctor':
            return redirect(url_for('doctor_dashboard'))
        elif user.role == 'Patient':
            return redirect(url_for('patient_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'Doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user.role == 'Patient':
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        gender = request.form.get('gender')
        dob_str = request.form.get('date_of_birth')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            name=name,
            email=email,
            role='Patient',
            phone=phone,
            address=address,
            gender=gender
        )
        
        if dob_str:
            user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@role_required('Admin')
def admin_dashboard():
    total_doctors = User.query.filter_by(role='Doctor', is_active=True).count()
    total_patients = User.query.filter_by(role='Patient', is_active=True).count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='Pending').count()
    
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments,
                         recent_appointments=recent_appointments)

@app.route('/admin/doctors')
@role_required('Admin')
def admin_doctors():
    search_query = request.args.get('search', '')
    
    if search_query:
        doctors = User.query.filter(
            User.role == 'Doctor',
            db.or_(
                User.name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        doctors = User.query.filter_by(role='Doctor').all()
    
    departments = Department.query.all()
    return render_template('admin/doctors.html', doctors=doctors, departments=departments)

@app.route('/admin/doctor/add', methods=['POST'])
@role_required('Admin')
def admin_add_doctor():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    department_id = request.form.get('department_id')
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin_doctors'))
    
    doctor = User(
        name=name,
        email=email,
        role='Doctor',
        phone=phone,
        department_id=department_id if department_id else None
    )
    doctor.set_password(password)
    
    db.session.add(doctor)
    db.session.commit()
    
    flash('Doctor added successfully.', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/doctor/edit/<int:doctor_id>', methods=['POST'])
@role_required('Admin')
def admin_edit_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    
    doctor.name = request.form.get('name')
    doctor.email = request.form.get('email')
    doctor.phone = request.form.get('phone')
    department_id = request.form.get('department_id')
    doctor.department_id = department_id if department_id else None
    
    password = request.form.get('password')
    if password:
        doctor.set_password(password)
    
    db.session.commit()
    flash('Doctor updated successfully.', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/doctor/delete/<int:doctor_id>', methods=['POST'])
@role_required('Admin')
def admin_delete_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    doctor.is_active = False
    db.session.commit()
    flash('Doctor removed successfully.', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/patients')
@role_required('Admin')
def admin_patients():
    search_query = request.args.get('search', '')
    
    if search_query:
        patients = User.query.filter(
            User.role == 'Patient',
            db.or_(
                User.name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.phone.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        patients = User.query.filter_by(role='Patient').all()
    
    return render_template('admin/patients.html', patients=patients)

@app.route('/admin/patient/edit/<int:patient_id>', methods=['POST'])
@role_required('Admin')
def admin_edit_patient(patient_id):
    patient = User.query.get_or_404(patient_id)
    
    patient.name = request.form.get('name')
    patient.email = request.form.get('email')
    patient.phone = request.form.get('phone')
    patient.address = request.form.get('address')
    
    db.session.commit()
    flash('Patient updated successfully.', 'success')
    return redirect(url_for('admin_patients'))

@app.route('/admin/patient/delete/<int:patient_id>', methods=['POST'])
@role_required('Admin')
def admin_delete_patient(patient_id):
    patient = User.query.get_or_404(patient_id)
    patient.is_active = False
    db.session.commit()
    flash('Patient removed successfully.', 'success')
    return redirect(url_for('admin_patients'))

@app.route('/admin/appointments')
@role_required('Admin')
def admin_appointments():
    appointments = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments)

@app.route('/admin/appointment/approve/<int:appointment_id>', methods=['POST'])
@role_required('Admin')
def admin_approve_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'Booked'
    db.session.commit()
    flash('Appointment approved successfully.', 'success')
    return redirect(url_for('admin_appointments'))

@app.route('/admin/appointment/cancel/<int:appointment_id>', methods=['POST'])
@role_required('Admin')
def admin_cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled successfully.', 'info')
    return redirect(url_for('admin_appointments'))

@app.route('/doctor/dashboard')
@role_required('Doctor')
def doctor_dashboard():
    doctor = User.query.get(session['user_id'])
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= today,
        Appointment.date <= week_later,
        Appointment.status == 'Booked'  # Only show approved appointments to doctors
    ).order_by(Appointment.date, Appointment.time).all()
    
    patients = db.session.query(User).join(
        Appointment, User.id == Appointment.patient_id
    ).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().all()
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         upcoming_appointments=upcoming_appointments,
                         patients=patients)

@app.route('/doctor/appointments')
@role_required('Doctor')
def doctor_appointments():
    doctor = User.query.get(session['user_id'])
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template('doctor/appointments.html', appointments=appointments)

@app.route('/doctor/appointment/complete/<int:appointment_id>', methods=['GET', 'POST'])
@role_required('Doctor')
def doctor_complete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        appointment.status = 'Completed'
        
        treatment = Treatment(
            appointment_id=appointment.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )
        
        db.session.add(treatment)
        db.session.commit()
        
        flash('Appointment completed and treatment recorded.', 'success')
        return redirect(url_for('doctor_appointments'))
    
    return render_template('doctor/complete_appointment.html', appointment=appointment)

@app.route('/doctor/appointment/cancel/<int:appointment_id>', methods=['POST'])
@role_required('Doctor')
def doctor_cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('doctor_appointments'))

@app.route('/doctor/patient/<int:patient_id>')
@role_required('Doctor')
def doctor_patient_history(patient_id):
    patient = User.query.get_or_404(patient_id)
    
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=session['user_id'],
        status='Completed'
    ).order_by(Appointment.date.desc()).all()
    
    return render_template('doctor/patient_history.html', patient=patient, appointments=appointments)

@app.route('/doctor/availability', methods=['GET', 'POST'])
@role_required('Doctor')
def doctor_availability():
    doctor = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        availability_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        
        availability = DoctorAvailability(
            doctor_id=doctor.id,
            date=availability_date,
            start_time=start_time_obj,
            end_time=end_time_obj
        )
        
        db.session.add(availability)
        db.session.commit()
        
        flash('Availability added successfully.', 'success')
        return redirect(url_for('doctor_availability'))
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_later
    ).order_by(DoctorAvailability.date).all()
    
    return render_template('doctor/availability.html', availabilities=availabilities)

@app.route('/patient/dashboard')
@role_required('Patient')
def patient_dashboard():
    patient = User.query.get(session['user_id'])
    departments = Department.query.all()
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    available_doctors = User.query.filter_by(role='Doctor', is_active=True).all()
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today,
        Appointment.status.in_(['Booked', 'Pending'])  # Show both approved and pending appointments
    ).order_by(Appointment.date, Appointment.time).all()
    
    return render_template('patient/dashboard.html',
                         patient=patient,
                         departments=departments,
                         available_doctors=available_doctors,
                         upcoming_appointments=upcoming_appointments)

@app.route('/patient/doctors')
@role_required('Patient')
def patient_doctors():
    search_query = request.args.get('search', '')
    department_id = request.args.get('department_id', '')
    
    query = User.query.filter_by(role='Doctor', is_active=True)
    
    if search_query:
        query = query.filter(User.name.ilike(f'%{search_query}%'))
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    doctors = query.all()
    departments = Department.query.all()
    
    return render_template('patient/doctors.html', doctors=doctors, departments=departments)

@app.route('/patient/book/<int:doctor_id>', methods=['GET', 'POST'])
@role_required('Patient')
def patient_book_appointment(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        reason = request.form.get('reason')
        
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        availability = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.date == appointment_date,
            DoctorAvailability.start_time <= appointment_time,
            DoctorAvailability.end_time >= appointment_time,
            DoctorAvailability.is_available == True
        ).first()
        
        if not availability:
            flash('Doctor is not available at this time. Please choose a time within the available slots.', 'danger')
            return redirect(url_for('patient_book_appointment', doctor_id=doctor_id))
        
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            status='Booked'
        ).first()
        
        if existing:
            flash('This time slot is already booked. Please choose another time.', 'danger')
            return redirect(url_for('patient_book_appointment', doctor_id=doctor_id))
        
        appointment = Appointment(
            patient_id=session['user_id'],
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            reason=reason,
            status='Pending'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient_appointments'))
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_later
    ).order_by(DoctorAvailability.date).all()
    
    return render_template('patient/book_appointment.html', doctor=doctor, availabilities=availabilities)

@app.route('/patient/appointments')
@role_required('Patient')
def patient_appointments():
    patient = User.query.get(session['user_id'])
    
    upcoming = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= date.today(),
        Appointment.status.in_(['Booked', 'Pending'])  # Show both approved and pending appointments
    ).order_by(Appointment.date, Appointment.time).all()
    
    past = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        db.or_(
            Appointment.status == 'Completed',
            Appointment.status == 'Cancelled'
        )
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    return render_template('patient/appointments.html', upcoming=upcoming, past=past)

@app.route('/patient/appointment/cancel/<int:appointment_id>', methods=['POST'])
@role_required('Patient')
def patient_cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('patient_appointments'))
    
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully.', 'info')
    return redirect(url_for('patient_appointments'))

@app.route('/patient/profile', methods=['GET', 'POST'])
@role_required('Patient')
def patient_profile():
    patient = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.email = request.form.get('email')
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('address')
        patient.gender = request.form.get('gender')
        
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            patient.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        password = request.form.get('password')
        if password:
            patient.set_password(password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient_profile'))
    
    return render_template('patient/profile.html', patient=patient)

def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(email='admin@hospital.com').first():
            admin = User(
                name='Admin',
                email='admin@hospital.com',
                role='Admin',
                phone='1234567890'
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        departments_data = [
            ('Cardiology', 'Heart and cardiovascular system'),
            ('Neurology', 'Brain and nervous system'),
            ('Orthopedics', 'Bones and joints'),
            ('Pediatrics', 'Children healthcare'),
            ('Dermatology', 'Skin conditions'),
            ('General Medicine', 'General health issues')
        ]
        
        for dept_name, dept_desc in departments_data:
            if not Department.query.filter_by(name=dept_name).first():
                dept = Department(name=dept_name, description=dept_desc)
                db.session.add(dept)
        
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print("WARNING: Running in DEBUG mode. DO NOT USE IN PRODUCTION!")
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
