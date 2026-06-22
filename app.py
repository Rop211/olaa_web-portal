# ============================================
# BRIGHT MINDS ACADEMY - COMPLETE SCHOOL SYSTEM
# Full Application with Parent Portal, SMS & All Features
# ============================================

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from functools import wraps
import os
import hashlib
import json
import re
import csv
from io import StringIO

# ===== AI CHATBOT IMPORTS =====
import openai
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# ============================================
# APP CONFIGURATION
# ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bright-minds-academy-secret-key-2026-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# ===== OPENAI API CONFIGURATION =====
openai.api_key = "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"
print("🔑 API Key loaded:", openai.api_key[:15] + "..." if openai.api_key else "❌ NOT LOADED")

# SMS Configuration (Africa's Talking - Optional)
app.config['AFRICASTALKING_USERNAME'] = 'sandbox'
app.config['AFRICASTALKING_API_KEY'] = 'your-api-key'
app.config['AFRICASTALKING_SHORTCODE'] = '12345'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ============================================
# DATABASE MODELS - COMPLETE SCHEMA (FIXED ORDER)
# ============================================

class AdminUser(db.Model):
    """Admin users for dashboard access"""
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    announcements = db.relationship('Announcement', backref='author', lazy=True)
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'


class Application(db.Model):
    """Student admission applications"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    child_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    additional_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    fee_payments = db.relationship('FeePayment', backref='application', lazy=True)
    
    def __repr__(self):
        return f'<Application {self.child_name}>'


class TourBooking(db.Model):
    """School tour bookings"""
    __tablename__ = 'tour_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.String(20), nullable=False)
    number_of_people = db.Column(db.Integer, default=2)
    child_age = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<TourBooking {self.parent_name}>'


class NewsletterSubscriber(db.Model):
    """Email newsletter subscribers"""
    __tablename__ = 'newsletter_subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now())
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Subscriber {self.email}>'


class Testimonial(db.Model):
    """Parent testimonials"""
    __tablename__ = 'testimonials'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    child_grade = db.Column(db.String(20))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Testimonial {self.name}>'


class GalleryImage(db.Model):
    """School gallery images"""
    __tablename__ = 'gallery_images'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    filename = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))
    category = db.Column(db.String(50))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now())
    
    def __repr__(self):
        return f'<GalleryImage {self.title or self.filename}>'


class ContactMessage(db.Model):
    """Contact form messages"""
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_replied = db.Column(db.Boolean, default=False)
    replied_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    
    def __repr__(self):
        return f'<ContactMessage {self.name}>'


class Staff(db.Model):
    """School staff members"""
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    position = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50))
    qualifications = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    hire_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Staff {self.staff_id}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Student(db.Model):
    """Enrolled students"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    admission_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))
    grade = db.Column(db.String(20), nullable=False)
    guardian_name = db.Column(db.String(100), nullable=False)
    guardian_phone = db.Column(db.String(20), nullable=False)
    guardian_email = db.Column(db.String(100))
    address = db.Column(db.Text)
    medical_notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    enrolled_date = db.Column(db.Date, default=lambda: datetime.now().date())
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Student {self.admission_number}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class FeeStructure(db.Model):
    """Fee structure for different grades"""
    __tablename__ = 'fee_structures'
    
    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(20), unique=True, nullable=False)
    tuition_fee = db.Column(db.Float, default=0.0)
    activity_fee = db.Column(db.Float, default=0.0)
    lunch_fee = db.Column(db.Float, default=0.0)
    transport_fee = db.Column(db.Float, default=0.0)
    other_fees = db.Column(db.Float, default=0.0)
    total_fee = db.Column(db.Float, default=0.0)
    term = db.Column(db.String(20))
    academic_year = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def calculate_total(self):
        self.total_fee = self.tuition_fee + self.activity_fee + self.lunch_fee + self.transport_fee + self.other_fees
        return self.total_fee
    
    def __repr__(self):
        return f'<FeeStructure {self.grade}>'


class FeePayment(db.Model):
    """Fee payments made by parents"""
    __tablename__ = 'fee_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=lambda: datetime.now().date())
    payment_method = db.Column(db.String(50))
    transaction_reference = db.Column(db.String(100))
    receipt_number = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(200))
    term = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Paid')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<FeePayment {self.receipt_number}>'


class Event(db.Model):
    """School events and calendar"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(20))
    end_date = db.Column(db.Date)
    location = db.Column(db.String(100))
    event_type = db.Column(db.String(50))
    is_public = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Event {self.title}>'


class Announcement(db.Model):
    """School announcements and notices"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    priority = db.Column(db.String(20), default='Normal')
    is_published = db.Column(db.Boolean, default=False)
    publish_date = db.Column(db.DateTime, default=lambda: datetime.now())
    expiry_date = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Announcement {self.title}>'


class SchoolSetting(db.Model):
    """School settings and configuration"""
    __tablename__ = 'school_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_group = db.Column(db.String(50))
    description = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<SchoolSetting {self.setting_key}>'


class ActivityLog(db.Model):
    """System activity logs"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'


class Parent(db.Model):
    """Parent/Guardian accounts for parent portal"""
    __tablename__ = 'parents'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def __repr__(self):
        return f'<Parent {self.full_name}>'


class AttendanceRecord(db.Model):
    """Student attendance records"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now().date())
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    student = db.relationship('Student', backref='attendance_records', lazy=True)
    
    def __repr__(self):
        return f'<AttendanceRecord - {self.date}>'


class StaffAttendance(db.Model):
    """Staff attendance records"""
    __tablename__ = 'staff_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now().date())
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    staff = db.relationship('Staff', backref='attendance_records', lazy=True)
    
    def __repr__(self):
        return f'<StaffAttendance - {self.date}>'


class Subject(db.Model):
    """School subjects"""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    code = db.Column(db.String(10), unique=True)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Subject {self.name}>'


class Exam(db.Model):
    """Exams and tests"""
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    term = db.Column(db.String(20), nullable=False)
    max_score = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Exam {self.name} - {self.subject}>'


class ExamResult(db.Model):
    """Student exam results/marks"""
    __tablename__ = 'exam_results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, default=100.0)
    grade = db.Column(db.String(2))
    grade_point = db.Column(db.Float)
    remarks = db.Column(db.String(200))
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    student = db.relationship('Student', backref='exam_results', lazy=True)
    exam = db.relationship('Exam', backref='exam_results', lazy=True)
    subject = db.relationship('Subject', backref='exam_results', lazy=True)
    
    def calculate_grade(self):
        """Calculate grade based on marks"""
        percentage = (self.marks_obtained / self.total_marks) * 100 if self.total_marks > 0 else 0
        
        if percentage >= 80:
            self.grade = 'A'
            self.grade_point = 12
        elif percentage >= 75:
            self.grade = 'A-'
            self.grade_point = 11
        elif percentage >= 70:
            self.grade = 'B+'
            self.grade_point = 10
        elif percentage >= 65:
            self.grade = 'B'
            self.grade_point = 9
        elif percentage >= 60:
            self.grade = 'B-'
            self.grade_point = 8
        elif percentage >= 55:
            self.grade = 'C+'
            self.grade_point = 7
        elif percentage >= 50:
            self.grade = 'C'
            self.grade_point = 6
        elif percentage >= 45:
            self.grade = 'C-'
            self.grade_point = 5
        elif percentage >= 40:
            self.grade = 'D+'
            self.grade_point = 4
        elif percentage >= 35:
            self.grade = 'D'
            self.grade_point = 3
        elif percentage >= 30:
            self.grade = 'D-'
            self.grade_point = 2
        else:
            self.grade = 'E'
            self.grade_point = 1
        
        return self.grade
    
    def __repr__(self):
        return f'<ExamResult - {self.marks_obtained}>'


class Term(db.Model):
    """Academic terms"""
    __tablename__ = 'terms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Term {self.name} - {self.academic_year}>'


class Backup(db.Model):
    """Database backup records"""
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    size = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    
    def __repr__(self):
        return f'<Backup {self.filename}>'


# ============================================
# SMS SERVICE
# ============================================

def send_sms(phone_number, message):
    """Send SMS using Africa's Talking API (Simulated for now)"""
    try:
        print(f"📱 SMS to {phone_number}: {message[:50]}...")
        return True, "SMS sent (simulated)"
    except Exception as e:
        return False, str(e)


def send_bulk_sms(phone_numbers, message):
    """Send bulk SMS to multiple recipients"""
    success_count = 0
    fail_count = 0
    for phone in phone_numbers:
        if phone:
            success, msg = send_sms(phone, message[:160])
            if success:
                success_count += 1
            else:
                fail_count += 1
    return success_count, fail_count


# ============================================
# CREATE DATABASE TABLES
# ============================================

with app.app_context():
    db.create_all()
    
    # Create default admin
    if not AdminUser.query.first():
        admin = AdminUser(
            username='admin',
            email='admin@brightminds.ac.ke',
            full_name='System Administrator',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin created: admin / admin123")
    
    # Create default school settings
    if not SchoolSetting.query.first():
        default_settings = [
            ('school_name', 'Bright Minds Academy', 'General', 'School name'),
            ('school_tagline', 'Where every child\'s future begins', 'General', 'School tagline'),
            ('school_address', 'Nairobi, Kenya', 'Contact', 'School address'),
            ('school_phone', '+254 700 000 000', 'Contact', 'School phone number'),
            ('school_email', 'info@brightminds.ac.ke', 'Contact', 'School email'),
            ('school_facebook', 'https://facebook.com/brightminds', 'Social', 'Facebook URL'),
            ('school_twitter', 'https://twitter.com/brightminds', 'Social', 'Twitter URL'),
            ('school_instagram', 'https://instagram.com/brightminds', 'Social', 'Instagram URL'),
            ('school_youtube', 'https://youtube.com/brightminds', 'Social', 'YouTube URL'),
            ('school_mission', 'To provide quality, holistic education that prepares children for a bright future.', 'About', 'School mission'),
            ('school_vision', 'To be a leading primary school in Kenya, raising confident, creative, and compassionate leaders.', 'About', 'School vision'),
            ('school_values', 'Excellence, Integrity, Respect, Creativity, Community', 'About', 'School values')
        ]
        for key, value, group, desc in default_settings:
            setting = SchoolSetting(
                setting_key=key,
                setting_value=value,
                setting_group=group,
                description=desc
            )
            db.session.add(setting)
        db.session.commit()
        print("✅ Default school settings created")
    
    # Create default parent account
    if not Parent.query.first():
        parent = Parent(
            username='parent',
            full_name='Test Parent',
            email='parent@example.com',
            phone='+254700000000',
            address='Nairobi, Kenya'
        )
        parent.set_password('parent123')
        db.session.add(parent)
        db.session.commit()
        print("✅ Default parent created: parent / parent123")
    
    # Create sample student
    if Student.query.count() == 0:
        student = Student(
            admission_number='BMA/2026/0001',
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime(2018, 5, 15),
            gender='Male',
            grade='Grade 3',
            guardian_name='Jane Doe',
            guardian_phone='+254700000000',
            guardian_email='parent@example.com',
            address='Nairobi, Kenya',
            is_active=True
        )
        db.session.add(student)
        db.session.commit()
        print("✅ Sample student created: John Doe")
    
    # Create sample fee structure
    if FeeStructure.query.count() == 0:
        fee = FeeStructure(
            grade='Grade 3',
            tuition_fee=15000.0,
            activity_fee=2000.0,
            lunch_fee=3000.0,
            transport_fee=2500.0,
            other_fees=500.0,
            term='Term 1',
            academic_year='2026',
            is_active=True
        )
        fee.calculate_total()
        db.session.add(fee)
        db.session.commit()
        print("✅ Sample fee structure created")
    
    # Create sample attendance
    if AttendanceRecord.query.count() == 0:
        student = Student.query.first()
        if student:
            for i in range(30):
                record_date = datetime.now().date() - timedelta(days=i)
                if record_date.weekday() < 5:
                    status = 'present' if i % 5 != 0 else 'absent'
                    record = AttendanceRecord(
                        student_id=student.id,
                        date=record_date,
                        status=status,
                        notes='' if status == 'present' else 'Sick'
                    )
                    db.session.add(record)
            db.session.commit()
            print("✅ Sample attendance records created")
    
    # Create sample subject
    if Subject.query.count() == 0:
        subjects = [
            ('Mathematics', 'MAT101', 'Basic mathematics skills'),
            ('English', 'ENG101', 'English language and literature'),
            ('Science', 'SCI101', 'Basic science concepts'),
            ('Kiswahili', 'KIS101', 'Kiswahili language'),
            ('Social Studies', 'SST101', 'Social studies and life skills'),
            ('Creative Arts', 'ART101', 'Art and music')
        ]
        for name, code, desc in subjects:
            subject = Subject(name=name, code=code, description=desc)
            db.session.add(subject)
        db.session.commit()
        print("✅ Sample subjects created")
    
    # Create sample exam
    if Exam.query.count() == 0:
        exam = Exam(
            name='Mid-Term Exam',
            grade='Grade 3',
            subject='Mathematics',
            exam_date=datetime.now().date(),
            term='Term 1',
            max_score=100
        )
        db.session.add(exam)
        db.session.commit()
        print("✅ Sample exam created")
    
    # Create sample exam result
    if ExamResult.query.count() == 0:
        student = Student.query.first()
        exam = Exam.query.first()
        subject = Subject.query.first()
        if student and exam and subject:
            result = ExamResult(
                student_id=student.id,
                exam_id=exam.id,
                subject_id=subject.id,
                marks_obtained=85.5,
                total_marks=100,
                remarks='Good performance'
            )
            result.calculate_grade()
            db.session.add(result)
            db.session.commit()
            print("✅ Sample exam result created")
    
    # Create sample event
    if Event.query.count() == 0:
        event = Event(
            title='Annual Sports Day',
            description='Come and support our students in various sports activities',
            event_date=datetime.now().date() + timedelta(days=14),
            event_time='8:00 AM',
            location='School Playground',
            event_type='Sports',
            is_public=True,
            is_featured=True
        )
        db.session.add(event)
        db.session.commit()
        print("✅ Sample event created")
    
    print("✅ Database initialized successfully!")


# ============================================
# DECORATORS
# ============================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access the admin panel.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def parent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('parent_logged_in'):
            flash('Please login to access the parent portal.', 'warning')
            return redirect(url_for('parent_login'))
        return f(*args, **kwargs)
    return decorated_function


def log_activity(user_id, action, entity_type=None, entity_id=None, details=None):
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()
    except:
        pass


# ============================================
# PUBLIC ROUTES
# ============================================

@app.route('/')
def index():
    testimonials = Testimonial.query.filter_by(is_approved=True).limit(6).all()
    events = Event.query.filter_by(is_public=True, is_featured=True).order_by(Event.event_date).limit(3).all()
    announcements = Announcement.query.filter_by(is_published=True).order_by(Announcement.publish_date.desc()).limit(3).all()
    gallery = GalleryImage.query.filter_by(is_featured=True).order_by(GalleryImage.sort_order).limit(8).all()
    return render_template('index.html', 
                         testimonials=testimonials, 
                         events=events, 
                         announcements=announcements,
                         gallery=gallery)


@app.route('/about')
def about():
    settings = SchoolSetting.query.all()
    settings_dict = {s.setting_key: s.setting_value for s in settings}
    staff = Staff.query.filter_by(is_active=True).all()
    return render_template('about.html', settings=settings_dict, staff=staff)


@app.route('/programs')
def programs():
    return render_template('programs.html')


@app.route('/gallery')
def gallery():
    images = GalleryImage.query.order_by(GalleryImage.sort_order, GalleryImage.uploaded_at.desc()).all()
    categories = db.session.query(GalleryImage.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('gallery.html', images=images, categories=categories)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    settings = SchoolSetting.query.all()
    settings_dict = {s.setting_key: s.setting_value for s in settings}
    
    if request.method == 'POST':
        try:
            message = ContactMessage(
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                subject=request.form.get('subject'),
                message=request.form.get('message')
            )
            db.session.add(message)
            db.session.commit()
            flash('✅ Your message has been sent. We will get back to you soon!', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
    
    return render_template('contact.html', settings=settings_dict)


@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            application = Application(
                child_name=request.form.get('child_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d'),
                grade=request.form.get('grade'),
                parent_name=request.form.get('parent_name'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                additional_notes=request.form.get('additional_notes')
            )
            db.session.add(application)
            db.session.commit()
            
            if application.phone:
                send_sms(application.phone, f"Bright Minds Academy: Application for {application.child_name} received. We'll contact you within 24hrs. Thank you!")
            
            flash('✅ Application submitted successfully! We will contact you within 24 hours.', 'success')
            return redirect(url_for('apply'))
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
    return render_template('apply.html')


@app.route('/book-tour', methods=['GET', 'POST'])
def book_tour():
    if request.method == 'POST':
        try:
            booking = TourBooking(
                parent_name=request.form.get('parent_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                preferred_date=datetime.strptime(request.form.get('preferred_date'), '%Y-%m-%d'),
                preferred_time=request.form.get('preferred_time'),
                number_of_people=int(request.form.get('number_of_people', 2)),
                child_age=request.form.get('child_age')
            )
            db.session.add(booking)
            db.session.commit()
            
            if booking.phone:
                send_sms(booking.phone, f"Bright Minds Academy: Tour booked for {booking.preferred_date.strftime('%d/%m/%y')} at {booking.preferred_time}. See you soon!")
            
            flash('✅ Tour booked successfully! We will confirm your slot within 24 hours.', 'success')
            return redirect(url_for('book_tour'))
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
    return render_template('book_tour.html')


@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        try:
            existing = NewsletterSubscriber.query.filter_by(email=email).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.unsubscribed_at = None
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Re-subscribed successfully!'})
                return jsonify({'success': False, 'message': 'Email already subscribed!'})
            
            subscriber = NewsletterSubscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Subscribed successfully!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    return jsonify({'success': False, 'message': 'Invalid email!'})


@app.route('/submit-testimonial', methods=['POST'])
def submit_testimonial():
    try:
        testimonial = Testimonial(
            name=request.form.get('name'),
            child_grade=request.form.get('child_grade'),
            content=request.form.get('content'),
            rating=int(request.form.get('rating', 5))
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('✅ Thank you for your testimonial! It will appear after approval.', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('index'))


@app.route('/events')
def events():
    upcoming = Event.query.filter(Event.event_date >= date.today(), Event.is_public == True).order_by(Event.event_date).all()
    past = Event.query.filter(Event.event_date < date.today(), Event.is_public == True).order_by(Event.event_date.desc()).limit(10).all()
    return render_template('events.html', upcoming=upcoming, past=past)


@app.route('/news')
def news():
    announcements = Announcement.query.filter_by(is_published=True).order_by(Announcement.publish_date.desc()).all()
    return render_template('news.html', announcements=announcements)


# ============================================
# AI SMART ADMISSIONS ASSISTANT
# ============================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Smart Admissions Assistant – answers parent queries using OpenAI."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Check if OpenAI API key is configured
    if not openai.api_key:
        return jsonify({'error': 'AI service is not configured. Please contact the school office.'}), 503
    
    # System prompt – defines the AI's role and knowledge
    system_prompt = """
You are the Smart Admissions Assistant for Bright Minds Academy, a school in Nairobi, Kenya.

Key school details:
- School Name: Bright Minds Academy
- Motto: Where every child's future begins
- Location: Nairobi, Kenya
- Grades: PPI – Grade 9 (CBC)
- Subjects: English, Kiswahili, Mathematics, Science, Computer Studies, Creative Arts, CRE, Agriculture, Home Science, Social Studies, Pre-Technical, French
- Contact: +254 700 000 000, info@brightminds.ac.ke
- Office Hours: Mon–Fri, 7:30AM – 4:30PM

Admission details:
- Admission is open throughout the year, main intake in January.
- Application forms at school office or online.
- Documents: Birth certificate, previous school report, immunization card, 2 passport photos.
- Fee structure (approx):
    - PPI – PP2: KES 25,000 per term
    - Grade 1 – 6: KES 30,000 per term
    - Grade 7 – 9: KES 35,000 per term
- School tours: Available by appointment.
- Bus service: Available for KES 8,000 per term.

Always be polite, encouraging, and offer to help further. Keep responses concise (1-2 short paragraphs) and conversational. Use a warm, friendly tone.
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({'reply': reply})
    
    except openai.error.AuthenticationError:
        return jsonify({'error': 'AI service authentication failed. Please contact the school office.'}), 503
    except openai.error.RateLimitError:
        return jsonify({'error': 'AI service is currently busy. Please try again in a few moments.'}), 429
    except openai.error.APIError:
        return jsonify({'error': 'AI service is temporarily unavailable. Please try again later.'}), 503
    except Exception as e:
        print(f"OpenAI error: {e}")
        return jsonify({'error': 'Sorry, I am having trouble right now. Please contact the school office directly.'}), 500


# ============================================
# ADMIN ROUTES - AUTH & DASHBOARD
# ============================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = AdminUser.query.filter_by(username=username, is_active=True).first()
        if admin and admin.check_password(password):
            session['admin_logged_in'] = True
            session['admin_user_id'] = admin.id
            session['admin_username'] = admin.username
            session['admin_role'] = admin.role
            
            admin.last_login = datetime.now()
            db.session.commit()
            
            log_activity(admin.id, 'login', 'AdminUser', admin.id, f'Logged in from {request.remote_addr}')
            
            flash('✅ Welcome back, ' + admin.full_name + '!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid username or password.', 'danger')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    if session.get('admin_user_id'):
        log_activity(session.get('admin_user_id'), 'logout', 'AdminUser', session.get('admin_user_id'), 'Logged out')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_applications': Application.query.count(),
        'pending_applications': Application.query.filter_by(status='Pending').count(),
        'total_tours': TourBooking.query.count(),
        'pending_tours': TourBooking.query.filter_by(status='Pending').count(),
        'subscribers': NewsletterSubscriber.query.filter_by(is_active=True).count(),
        'testimonials': Testimonial.query.count(),
        'pending_testimonials': Testimonial.query.filter_by(is_approved=False).count(),
        'messages': ContactMessage.query.filter_by(is_read=False).count(),
        'gallery_count': GalleryImage.query.count(),
        'students': Student.query.filter_by(is_active=True).count(),
        'staff': Staff.query.filter_by(is_active=True).count(),
        'events': Event.query.filter(Event.event_date >= date.today()).count(),
        'parents': Parent.query.count()
    }
    
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()
    recent_tours = TourBooking.query.order_by(TourBooking.created_at.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         stats=stats,
                         recent_applications=recent_applications,
                         recent_tours=recent_tours,
                         recent_messages=recent_messages,
                         recent_activities=recent_activities)


# ============================================
# ADMIN - APPLICATIONS
# ============================================

@app.route('/admin/applications')
@admin_required
def admin_applications():
    applications = Application.query.order_by(Application.created_at.desc()).all()
    return render_template('admin_applications.html', applications=applications)


@app.route('/admin/application/<int:id>')
@admin_required
def admin_application_detail(id):
    application = Application.query.get_or_404(id)
    return render_template('admin_application_detail.html', application=application)


@app.route('/admin/application/<int:id>/update-status', methods=['POST'])
@admin_required
def admin_update_application_status(id):
    application = Application.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Contacted', 'Enrolled', 'Rejected']:
        old_status = application.status
        application.status = new_status
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'update_application_status', 'Application', id, 
                    f'Status changed from {old_status} to {new_status}')
        flash(f'✅ Status updated to {new_status}', 'success')
    return redirect(url_for('admin_application_detail', id=id))


@app.route('/admin/application/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_application(id):
    application = Application.query.get_or_404(id)
    db.session.delete(application)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_application', 'Application', id, 'Application deleted')
    flash('✅ Application deleted', 'success')
    return redirect(url_for('admin_applications'))


# ============================================
# ADMIN - TOURS
# ============================================

@app.route('/admin/tours')
@admin_required
def admin_tours():
    tours = TourBooking.query.order_by(TourBooking.created_at.desc()).all()
    return render_template('admin_tours.html', tours=tours)


@app.route('/admin/tour/<int:id>')
@admin_required
def admin_tour_detail(id):
    tour = TourBooking.query.get_or_404(id)
    return render_template('admin_tour_detail.html', tour=tour)


@app.route('/admin/tour/<int:id>/update-status', methods=['POST'])
@admin_required
def admin_update_tour_status(id):
    tour = TourBooking.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
        old_status = tour.status
        tour.status = new_status
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'update_tour_status', 'TourBooking', id,
                    f'Status changed from {old_status} to {new_status}')
        flash(f'✅ Tour status updated to {new_status}', 'success')
    return redirect(url_for('admin_tour_detail', id=id))


@app.route('/admin/tour/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_tour(id):
    tour = TourBooking.query.get_or_404(id)
    db.session.delete(tour)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_tour', 'TourBooking', id, 'Tour booking deleted')
    flash('✅ Tour booking deleted', 'success')
    return redirect(url_for('admin_tours'))


# ============================================
# ADMIN - TESTIMONIALS
# ============================================

@app.route('/admin/testimonials')
@admin_required
def admin_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin_testimonials.html', testimonials=testimonials)


@app.route('/admin/testimonial/<int:id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    testimonial.is_approved = not testimonial.is_approved
    db.session.commit()
    status = 'approved' if testimonial.is_approved else 'hidden'
    log_activity(session.get('admin_user_id'), 'toggle_testimonial', 'Testimonial', id,
                f'Testimonial {status}')
    flash(f'✅ Testimonial {status}', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonial/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_testimonial', 'Testimonial', id, 'Testimonial deleted')
    flash('✅ Testimonial deleted', 'success')
    return redirect(url_for('admin_testimonials'))


# ============================================
# ADMIN - GALLERY
# ============================================

@app.route('/admin/gallery')
@admin_required
def admin_gallery():
    images = GalleryImage.query.order_by(GalleryImage.sort_order, GalleryImage.uploaded_at.desc()).all()
    return render_template('admin_gallery.html', images=images)


@app.route('/admin/gallery/upload', methods=['POST'])
@admin_required
def admin_upload_gallery():
    if 'image' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('admin_gallery'))
    
    file = request.files['image']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin_gallery'))
    
    if file:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        image = GalleryImage(
            title=request.form.get('title', file.filename),
            filename=filename,
            caption=request.form.get('caption', ''),
            category=request.form.get('category', 'General'),
            is_featured=bool(request.form.get('is_featured')),
            sort_order=int(request.form.get('sort_order', 0))
        )
        db.session.add(image)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'upload_gallery', 'GalleryImage', image.id,
                    f'Uploaded {filename}')
        flash('✅ Image uploaded successfully!', 'success')
    return redirect(url_for('admin_gallery'))


@app.route('/admin/gallery/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_gallery(id):
    image = GalleryImage.query.get_or_404(id)
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass
    db.session.delete(image)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_gallery', 'GalleryImage', id,
                f'Deleted {image.filename}')
    flash('✅ Image deleted', 'success')
    return redirect(url_for('admin_gallery'))


@app.route('/admin/gallery/<int:id>/feature', methods=['POST'])
@admin_required
def admin_toggle_featured_gallery(id):
    image = GalleryImage.query.get_or_404(id)
    image.is_featured = not image.is_featured
    db.session.commit()
    status = 'featured' if image.is_featured else 'unfeatured'
    flash(f'✅ Image {status}', 'success')
    return redirect(url_for('admin_gallery'))


# ============================================
# ADMIN - MESSAGES
# ============================================

@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)


@app.route('/admin/message/<int:id>/read', methods=['POST'])
@admin_required
def admin_mark_message_read(id):
    message = ContactMessage.query.get_or_404(id)
    message.is_read = True
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'mark_message_read', 'ContactMessage', id, 'Message marked as read')
    flash('✅ Message marked as read', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/admin/message/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_message(id):
    message = ContactMessage.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_message', 'ContactMessage', id, 'Message deleted')
    flash('✅ Message deleted', 'success')
    return redirect(url_for('admin_messages'))


# ============================================
# ADMIN - SUBSCRIBERS
# ============================================

@app.route('/admin/subscribers')
@admin_required
def admin_subscribers():
    subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    return render_template('admin_subscribers.html', subscribers=subscribers)


@app.route('/admin/subscriber/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_subscriber(id):
    subscriber = NewsletterSubscriber.query.get_or_404(id)
    db.session.delete(subscriber)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_subscriber', 'NewsletterSubscriber', id,
                f'Removed {subscriber.email}')
    flash('✅ Subscriber removed', 'success')
    return redirect(url_for('admin_subscribers'))


@app.route('/admin/subscriber/<int:id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_subscriber(id):
    subscriber = NewsletterSubscriber.query.get_or_404(id)
    subscriber.is_active = not subscriber.is_active
    if subscriber.is_active:
        subscriber.unsubscribed_at = None
    else:
        subscriber.unsubscribed_at = datetime.now()
    db.session.commit()
    status = 'activated' if subscriber.is_active else 'deactivated'
    flash(f'✅ Subscriber {status}', 'success')
    return redirect(url_for('admin_subscribers'))


# ============================================
# ADMIN - STUDENTS
# ============================================

@app.route('/admin/students')
@admin_required
def admin_students():
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('admin_students.html', students=students)


@app.route('/admin/student/<int:id>')
@admin_required
def admin_student_detail(id):
    student = Student.query.get_or_404(id)
    payments = FeePayment.query.filter_by(student_id=id).order_by(FeePayment.payment_date.desc()).all()
    return render_template('admin_student_detail.html', student=student, payments=payments)


@app.route('/admin/students/create', methods=['GET', 'POST'])
@admin_required
def admin_create_student():
    if request.method == 'POST':
        try:
            year = datetime.now().year
            count = Student.query.count() + 1
            admission_number = f"BMA/{year}/{count:04d}"
            
            student = Student(
                admission_number=admission_number,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d'),
                gender=request.form.get('gender'),
                grade=request.form.get('grade'),
                guardian_name=request.form.get('guardian_name'),
                guardian_phone=request.form.get('guardian_phone'),
                guardian_email=request.form.get('guardian_email'),
                address=request.form.get('address'),
                medical_notes=request.form.get('medical_notes'),
                enrolled_date=datetime.strptime(request.form.get('enrolled_date'), '%Y-%m-%d') if request.form.get('enrolled_date') else datetime.now().date()
            )
            db.session.add(student)
            db.session.commit()
            log_activity(session.get('admin_user_id'), 'create_student', 'Student', student.id,
                        f'Created student {student.full_name}')
            flash(f'✅ Student created successfully! Admission Number: {admission_number}', 'success')
            return redirect(url_for('admin_student_detail', id=student.id))
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
    
    return render_template('admin_student_create.html')


@app.route('/admin/student/<int:id>/update', methods=['POST'])
@admin_required
def admin_update_student(id):
    student = Student.query.get_or_404(id)
    try:
        student.first_name = request.form.get('first_name')
        student.last_name = request.form.get('last_name')
        student.gender = request.form.get('gender')
        student.grade = request.form.get('grade')
        student.guardian_name = request.form.get('guardian_name')
        student.guardian_phone = request.form.get('guardian_phone')
        student.guardian_email = request.form.get('guardian_email')
        student.address = request.form.get('address')
        student.medical_notes = request.form.get('medical_notes')
        student.is_active = bool(request.form.get('is_active', False))
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'update_student', 'Student', id,
                    f'Updated student {student.full_name}')
        flash('✅ Student updated successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_student_detail', id=id))


@app.route('/admin/student/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_student', 'Student', id,
                f'Deleted student {student.full_name}')
    flash('✅ Student deleted', 'success')
    return redirect(url_for('admin_students'))


# ============================================
# ADMIN - STAFF
# ============================================

@app.route('/admin/staff')
@admin_required
def admin_staff():
    staff = Staff.query.order_by(Staff.created_at.desc()).all()
    return render_template('admin_staff.html', staff=staff)


@app.route('/admin/staff/create', methods=['GET', 'POST'])
@admin_required
def admin_create_staff():
    if request.method == 'POST':
        try:
            year = datetime.now().year
            count = Staff.query.count() + 1
            staff_id = f"STF/{year}/{count:04d}"
            
            staff = Staff(
                staff_id=staff_id,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                position=request.form.get('position'),
                department=request.form.get('department'),
                qualifications=request.form.get('qualifications'),
                experience_years=int(request.form.get('experience_years', 0)),
                bio=request.form.get('bio'),
                hire_date=datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d') if request.form.get('hire_date') else None
            )
            db.session.add(staff)
            db.session.commit()
            log_activity(session.get('admin_user_id'), 'create_staff', 'Staff', staff.id,
                        f'Created staff {staff.full_name}')
            flash(f'✅ Staff created successfully! Staff ID: {staff_id}', 'success')
            return redirect(url_for('admin_staff'))
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
    
    return render_template('admin_staff_create.html')


@app.route('/admin/staff/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_staff(id):
    staff = Staff.query.get_or_404(id)
    db.session.delete(staff)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_staff', 'Staff', id,
                f'Deleted staff {staff.full_name}')
    flash('✅ Staff deleted', 'success')
    return redirect(url_for('admin_staff'))


# ============================================
# ADMIN - FEE STRUCTURES
# ============================================

@app.route('/admin/fees')
@admin_required
def admin_fees():
    fees = FeeStructure.query.order_by(FeeStructure.grade).all()
    return render_template('admin_fees.html', fees=fees)


@app.route('/admin/fees/create', methods=['POST'])
@admin_required
def admin_create_fee():
    try:
        fee = FeeStructure(
            grade=request.form.get('grade'),
            tuition_fee=float(request.form.get('tuition_fee', 0)),
            activity_fee=float(request.form.get('activity_fee', 0)),
            lunch_fee=float(request.form.get('lunch_fee', 0)),
            transport_fee=float(request.form.get('transport_fee', 0)),
            other_fees=float(request.form.get('other_fees', 0)),
            term=request.form.get('term'),
            academic_year=request.form.get('academic_year'),
            is_active=bool(request.form.get('is_active', False))
        )
        fee.calculate_total()
        db.session.add(fee)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'create_fee_structure', 'FeeStructure', fee.id,
                    f'Created fee for {fee.grade}')
        flash('✅ Fee structure created successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_fees'))


@app.route('/admin/fees/<int:id>/update', methods=['POST'])
@admin_required
def admin_update_fee(id):
    fee = FeeStructure.query.get_or_404(id)
    try:
        fee.grade = request.form.get('grade')
        fee.tuition_fee = float(request.form.get('tuition_fee', 0))
        fee.activity_fee = float(request.form.get('activity_fee', 0))
        fee.lunch_fee = float(request.form.get('lunch_fee', 0))
        fee.transport_fee = float(request.form.get('transport_fee', 0))
        fee.other_fees = float(request.form.get('other_fees', 0))
        fee.term = request.form.get('term')
        fee.academic_year = request.form.get('academic_year')
        fee.is_active = bool(request.form.get('is_active', False))
        fee.calculate_total()
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'update_fee_structure', 'FeeStructure', id,
                    f'Updated fee for {fee.grade}')
        flash('✅ Fee structure updated successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_fees'))


@app.route('/admin/fees/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_fee(id):
    fee = FeeStructure.query.get_or_404(id)
    db.session.delete(fee)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_fee_structure', 'FeeStructure', id,
                f'Deleted fee for {fee.grade}')
    flash('✅ Fee structure deleted', 'success')
    return redirect(url_for('admin_fees'))


# ============================================
# ADMIN - EVENTS
# ============================================

@app.route('/admin/events')
@admin_required
def admin_events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin_events.html', events=events)


@app.route('/admin/events/create', methods=['POST'])
@admin_required
def admin_create_event():
    try:
        event = Event(
            title=request.form.get('title'),
            description=request.form.get('description'),
            event_date=datetime.strptime(request.form.get('event_date'), '%Y-%m-%d'),
            event_time=request.form.get('event_time'),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None,
            location=request.form.get('location'),
            event_type=request.form.get('event_type'),
            is_public=bool(request.form.get('is_public', False)),
            is_featured=bool(request.form.get('is_featured', False))
        )
        db.session.add(event)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'create_event', 'Event', event.id,
                    f'Created event {event.title}')
        flash('✅ Event created successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_events'))


@app.route('/admin/events/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_event', 'Event', id,
                f'Deleted event {event.title}')
    flash('✅ Event deleted', 'success')
    return redirect(url_for('admin_events'))


# ============================================
# ADMIN - ANNOUNCEMENTS
# ============================================

@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin_announcements.html', announcements=announcements)


@app.route('/admin/announcements/create', methods=['POST'])
@admin_required
def admin_create_announcement():
    try:
        announcement = Announcement(
            title=request.form.get('title'),
            content=request.form.get('content'),
            category=request.form.get('category'),
            priority=request.form.get('priority', 'Normal'),
            is_published=bool(request.form.get('is_published', False)),
            publish_date=datetime.strptime(request.form.get('publish_date'), '%Y-%m-%d %H:%M') if request.form.get('publish_date') else datetime.now(),
            expiry_date=datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d %H:%M') if request.form.get('expiry_date') else None,
            created_by=session.get('admin_user_id')
        )
        db.session.add(announcement)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'create_announcement', 'Announcement', announcement.id,
                    f'Created announcement {announcement.title}')
        flash('✅ Announcement created successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_announcements'))


@app.route('/admin/announcements/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_announcement', 'Announcement', id,
                f'Deleted announcement {announcement.title}')
    flash('✅ Announcement deleted', 'success')
    return redirect(url_for('admin_announcements'))


# ============================================
# ADMIN - SETTINGS
# ============================================

@app.route('/admin/settings')
@admin_required
def admin_settings():
    settings = SchoolSetting.query.all()
    settings_dict = {s.setting_key: s.setting_value for s in settings}
    return render_template('admin_settings.html', settings=settings, settings_dict=settings_dict)


@app.route('/admin/settings/update', methods=['POST'])
@admin_required
def admin_update_settings():
    try:
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                setting = SchoolSetting.query.filter_by(setting_key=setting_key).first()
                if setting:
                    setting.setting_value = value
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'update_settings', 'SchoolSetting', None,
                    'Updated school settings')
        flash('✅ Settings updated successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_settings'))


# ============================================
# ADMIN - SMS
# ============================================

@app.route('/admin/sms')
@admin_required
def admin_sms():
    parents = []
    applications = Application.query.filter(Application.status == 'Enrolled').all()
    for app in applications:
        if app.phone:
            parents.append({
                'name': app.parent_name,
                'phone': app.phone,
                'child': app.child_name,
                'grade': app.grade
            })
    return render_template('admin_sms.html', parents=parents)


@app.route('/admin/sms/send-bulk', methods=['POST'])
@admin_required
def admin_send_bulk_sms():
    message = request.form.get('message')
    recipients = request.form.getlist('recipients')
    
    if not message or not recipients:
        flash('❌ Please provide message and select recipients', 'danger')
        return redirect(url_for('admin_sms'))
    
    success_count, fail_count = send_bulk_sms(recipients, message)
    
    log_activity(session.get('admin_user_id'), 'send_bulk_sms', 'SMS', None, 
                f'Bulk SMS sent to {success_count} recipients, {fail_count} failed')
    
    flash(f'✅ SMS sent! Success: {success_count}, Failed: {fail_count}', 'success')
    return redirect(url_for('admin_sms'))


@app.route('/admin/sms/send-single', methods=['POST'])
@admin_required
def admin_send_single_sms():
    phone = request.form.get('phone')
    message = request.form.get('message')
    
    if not phone or not message:
        flash('❌ Please provide phone number and message', 'danger')
        return redirect(url_for('admin_sms'))
    
    success, msg = send_sms(phone, message)
    
    log_activity(session.get('admin_user_id'), 'send_single_sms', 'SMS', None, 
                f'Sent SMS to {phone}')
    
    if success:
        flash('✅ SMS sent successfully!', 'success')
    else:
        flash(f'❌ Failed to send SMS: {msg}', 'danger')
    
    return redirect(url_for('admin_sms'))


@app.route('/admin/sms/test')
@admin_required
def admin_test_sms():
    test_phone = request.args.get('phone', '254700000000')
    success, message = send_sms(test_phone, "Test SMS from Bright Minds Academy")
    
    if success:
        flash('✅ Test SMS sent successfully!', 'success')
    else:
        flash(f'❌ Failed to send test SMS: {message}', 'danger')
    
    return redirect(url_for('admin_sms'))


# ============================================
# ADMIN - PARENTS
# ============================================

@app.route('/admin/parents')
@admin_required
def admin_parents():
    parents = Parent.query.order_by(Parent.created_at.desc()).all()
    return render_template('admin_parents.html', parents=parents)


@app.route('/admin/parents/create', methods=['GET', 'POST'])
@admin_required
def admin_create_parent():
    if request.method == 'POST':
        try:
            parent = Parent(
                username=request.form.get('username'),
                full_name=request.form.get('full_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address')
            )
            parent.set_password(request.form.get('password'))
            db.session.add(parent)
            db.session.commit()
            
            log_activity(session.get('admin_user_id'), 'create_parent', 'Parent', parent.id,
                        f'Created parent {parent.full_name}')
            flash('✅ Parent account created successfully!', 'success')
            return redirect(url_for('admin_parents'))
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
    
    return render_template('admin_parent_create.html')


@app.route('/admin/parents/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_parent(id):
    parent = Parent.query.get_or_404(id)
    
    children = Student.query.filter_by(guardian_email=parent.email).count()
    if children > 0:
        flash('❌ Cannot delete parent with enrolled children. Remove children first.', 'danger')
        return redirect(url_for('admin_parents'))
    
    db.session.delete(parent)
    db.session.commit()
    
    log_activity(session.get('admin_user_id'), 'delete_parent', 'Parent', id,
                f'Deleted parent {parent.full_name}')
    flash('✅ Parent deleted successfully!', 'success')
    return redirect(url_for('admin_parents'))


@app.route('/admin/parents/<int:id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_parent(id):
    parent = Parent.query.get_or_404(id)
    parent.is_active = not parent.is_active
    db.session.commit()
    
    status = 'activated' if parent.is_active else 'deactivated'
    log_activity(session.get('admin_user_id'), 'toggle_parent', 'Parent', id,
                f'Parent {status}')
    flash(f'✅ Parent {status}!', 'success')
    return redirect(url_for('admin_parents'))


# ============================================
# ADMIN - EXPORTS
# ============================================

@app.route('/admin/export/applications')
@admin_required
def admin_export_applications():
    applications = Application.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Child Name', 'DOB', 'Grade', 'Parent', 'Phone', 'Email', 'Status', 'Date'])
    
    for app_item in applications:
        writer.writerow([
            app_item.id, 
            app_item.child_name, 
            app_item.date_of_birth.strftime('%Y-%m-%d') if app_item.date_of_birth else '',
            app_item.grade, 
            app_item.parent_name, 
            app_item.phone, 
            app_item.email,
            app_item.status, 
            app_item.created_at.strftime('%Y-%m-%d %H:%M') if app_item.created_at else ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=applications_export.csv'
    
    log_activity(session.get('admin_user_id'), 'export_applications', 'Application', None, 'Exported applications CSV')
    return response


@app.route('/admin/export/students')
@admin_required
def admin_export_students():
    students = Student.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Admission No', 'First Name', 'Last Name', 'Grade', 'Guardian', 'Phone', 'Email', 'Enrolled'])
    
    for s in students:
        writer.writerow([
            s.admission_number, s.first_name, s.last_name, s.grade,
            s.guardian_name, s.guardian_phone, s.guardian_email,
            s.enrolled_date.strftime('%Y-%m-%d') if s.enrolled_date else ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=students_export.csv'
    
    log_activity(session.get('admin_user_id'), 'export_students', 'Student', None, 'Exported students CSV')
    return response


# ============================================
# ADMIN - ATTENDANCE
# ============================================

@app.route('/admin/attendance')
@admin_required
def admin_attendance():
    selected_date = request.args.get('date', datetime.now().date().strftime('%Y-%m-%d'))
    grade = request.args.get('grade', 'all')
    
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        selected_date = datetime.now().date()
    
    if grade == 'all':
        students = Student.query.filter_by(is_active=True).all()
    else:
        students = Student.query.filter_by(grade=grade, is_active=True).all()
    
    present_count = 0
    absent_count = 0
    late_count = 0
    
    for student in students:
        record = AttendanceRecord.query.filter_by(student_id=student.id, date=selected_date).first()
        if record:
            if record.status == 'present':
                present_count += 1
            elif record.status == 'absent':
                absent_count += 1
            elif record.status == 'late':
                late_count += 1
    
    return render_template('admin/attendance.html',
                         students=students,
                         selected_date=selected_date.strftime('%Y-%m-%d'),
                         present_count=present_count,
                         absent_count=absent_count,
                         late_count=late_count,
                         total_students=len(students))


@app.route('/admin/attendance/mark', methods=['POST'])
@admin_required
def admin_mark_attendance():
    date_str = request.form.get('date')
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        attendance_date = datetime.now().date()
    
    success_count = 0
    for key, value in request.form.items():
        if key.startswith('attendance_'):
            student_id = int(key.replace('attendance_', ''))
            status = value
            notes_key = f'notes_{student_id}'
            notes = request.form.get(notes_key, '')
            
            record = AttendanceRecord.query.filter_by(student_id=student_id, date=attendance_date).first()
            if record:
                record.status = status
                record.notes = notes
            else:
                record = AttendanceRecord(
                    student_id=student_id,
                    date=attendance_date,
                    status=status,
                    notes=notes
                )
                db.session.add(record)
            success_count += 1
    
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'mark_attendance', 'Attendance', None,
                f'Marked attendance for {success_count} students on {attendance_date}')
    flash(f'✅ Attendance saved for {success_count} students!', 'success')
    return redirect(url_for('admin_attendance', date=date_str))


@app.route('/admin/attendance/report')
@admin_required
def admin_attendance_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    student_id = request.args.get('student_id', 'all')
    
    all_students = Student.query.filter_by(is_active=True).all()
    
    query = AttendanceRecord.query
    if student_id != 'all':
        query = query.filter_by(student_id=int(student_id))
    
    if from_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(AttendanceRecord.date >= from_date)
        except:
            pass
    
    if to_date:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(AttendanceRecord.date <= to_date)
        except:
            pass
    
    records = query.order_by(AttendanceRecord.date.desc()).all()
    
    present_count = len([r for r in records if r.status == 'present'])
    absent_count = len([r for r in records if r.status == 'absent'])
    late_count = len([r for r in records if r.status == 'late'])
    total = len(records)
    attendance_rate = int((present_count / total) * 100) if total > 0 else 0
    
    return render_template('admin/attendance_report.html',
                         attendance_records=records,
                         all_students=all_students,
                         from_date=from_date.strftime('%Y-%m-%d') if from_date else '',
                         to_date=to_date.strftime('%Y-%m-%d') if to_date else '',
                         present_count=present_count,
                         absent_count=absent_count,
                         late_count=late_count,
                         attendance_rate=attendance_rate)


@app.route('/admin/staff/attendance')
@admin_required
def admin_staff_attendance():
    selected_date = request.args.get('date', datetime.now().date().strftime('%Y-%m-%d'))
    department = request.args.get('department', 'all')
    
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        selected_date = datetime.now().date()
    
    if department == 'all':
        staff = Staff.query.filter_by(is_active=True).all()
    else:
        staff = Staff.query.filter_by(department=department, is_active=True).all()
    
    present_count = 0
    absent_count = 0
    leave_count = 0
    
    for member in staff:
        record = StaffAttendance.query.filter_by(staff_id=member.id, date=selected_date).first()
        if record:
            if record.status == 'present':
                present_count += 1
            elif record.status == 'absent':
                absent_count += 1
            elif record.status == 'leave':
                leave_count += 1
    
    return render_template('admin/staff_attendance.html',
                         staff=staff,
                         selected_date=selected_date.strftime('%Y-%m-%d'),
                         present_count=present_count,
                         absent_count=absent_count,
                         leave_count=leave_count,
                         total_staff=len(staff))


@app.route('/admin/staff/attendance/mark', methods=['POST'])
@admin_required
def admin_mark_staff_attendance():
    date_str = request.form.get('date')
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        attendance_date = datetime.now().date()
    
    success_count = 0
    for key, value in request.form.items():
        if key.startswith('attendance_'):
            staff_id = int(key.replace('attendance_', ''))
            status = value
            notes_key = f'notes_{staff_id}'
            notes = request.form.get(notes_key, '')
            
            record = StaffAttendance.query.filter_by(staff_id=staff_id, date=attendance_date).first()
            if record:
                record.status = status
                record.notes = notes
            else:
                record = StaffAttendance(
                    staff_id=staff_id,
                    date=attendance_date,
                    status=status,
                    notes=notes
                )
                db.session.add(record)
            success_count += 1
    
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'mark_staff_attendance', 'StaffAttendance', None,
                f'Marked staff attendance for {success_count} staff on {attendance_date}')
    flash(f'✅ Staff attendance saved for {success_count} staff!', 'success')
    return redirect(url_for('admin_staff_attendance', date=date_str))


# ============================================
# ADMIN - RESULTS & MARKS
# ============================================

@app.route('/admin/results')
@admin_required
def admin_results_dashboard():
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    subjects = Subject.query.filter_by(is_active=True).all()
    
    stats = {
        'total_exams': Exam.query.count(),
        'total_subjects': Subject.query.filter_by(is_active=True).count(),
        'total_results': ExamResult.query.count(),
        'published_results': ExamResult.query.filter_by(is_published=True).count()
    }
    
    return render_template('admin/results_dashboard.html',
                         exams=exams,
                         subjects=subjects,
                         stats=stats)


@app.route('/admin/subjects')
@admin_required
def admin_subjects():
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('admin/subjects.html', subjects=subjects)


@app.route('/admin/subjects/create', methods=['POST'])
@admin_required
def admin_create_subject():
    try:
        subject = Subject(
            name=request.form.get('name'),
            code=request.form.get('code'),
            description=request.form.get('description')
        )
        db.session.add(subject)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'create_subject', 'Subject', subject.id,
                    f'Created subject {subject.name}')
        flash('✅ Subject created successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_subjects'))


@app.route('/admin/subjects/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_subject(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_subject', 'Subject', id,
                f'Deleted subject {subject.name}')
    flash('✅ Subject deleted', 'success')
    return redirect(url_for('admin_subjects'))


@app.route('/admin/exams')
@admin_required
def admin_exams():
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    return render_template('admin/exams.html', exams=exams)


@app.route('/admin/exams/create', methods=['POST'])
@admin_required
def admin_create_exam():
    try:
        exam = Exam(
            name=request.form.get('name'),
            grade=request.form.get('grade'),
            subject=request.form.get('subject'),
            exam_date=datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d'),
            term=request.form.get('term'),
            max_score=float(request.form.get('max_score', 100))
        )
        db.session.add(exam)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'create_exam', 'Exam', exam.id,
                    f'Created exam {exam.name}')
        flash('✅ Exam created successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_exams'))


@app.route('/admin/exams/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_exam(id):
    exam = Exam.query.get_or_404(id)
    db.session.delete(exam)
    db.session.commit()
    log_activity(session.get('admin_user_id'), 'delete_exam', 'Exam', id,
                f'Deleted exam {exam.name}')
    flash('✅ Exam deleted', 'success')
    return redirect(url_for('admin_exams'))


@app.route('/admin/exams/<int:exam_id>/enter-marks')
@admin_required
def admin_enter_marks(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    students = Student.query.filter_by(grade=exam.grade, is_active=True).all()
    
    existing_results = {}
    for result in ExamResult.query.filter_by(exam_id=exam_id).all():
        existing_results[result.student_id] = result
    
    return render_template('admin/enter_marks.html',
                         exam=exam,
                         students=students,
                         existing_results=existing_results)


@app.route('/admin/exams/<int:exam_id>/save-marks', methods=['POST'])
@admin_required
def admin_save_marks(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    try:
        subject_name = request.form.get('subject_name', exam.subject)
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name, code=subject_name[:3].upper())
            db.session.add(subject)
            db.session.commit()
        
        for key, value in request.form.items():
            if key.startswith('marks_'):
                student_id = int(key.replace('marks_', ''))
                marks = float(value) if value else 0
                
                result = ExamResult.query.filter_by(
                    student_id=student_id,
                    exam_id=exam_id,
                    subject_id=subject.id
                ).first()
                
                if result:
                    result.marks_obtained = marks
                    result.total_marks = exam.max_score
                    result.calculate_grade()
                else:
                    result = ExamResult(
                        student_id=student_id,
                        exam_id=exam_id,
                        subject_id=subject.id,
                        marks_obtained=marks,
                        total_marks=exam.max_score
                    )
                    result.calculate_grade()
                    db.session.add(result)
        
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'save_marks', 'ExamResult', exam_id,
                    f'Saved marks for exam {exam.name}')
        flash('✅ Marks saved successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin_enter_marks', exam_id=exam_id))


@app.route('/admin/exams/<int:exam_id>/publish')
@admin_required
def admin_publish_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    try:
        results = ExamResult.query.filter_by(exam_id=exam_id).all()
        for result in results:
            result.is_published = True
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'publish_results', 'Exam', exam_id,
                    f'Published results for exam {exam.name}')
        flash('✅ Results published successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin_results_dashboard'))


@app.route('/admin/student/<int:student_id>/results')
@admin_required
def admin_student_results(student_id):
    student = Student.query.get_or_404(student_id)
    
    results = ExamResult.query.filter_by(student_id=student_id).join(Exam).order_by(Exam.exam_date.desc()).all()
    
    total_marks = sum(r.marks_obtained for r in results)
    total_possible = sum(r.total_marks for r in results)
    average = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    percentages = [((r.marks_obtained / r.total_marks) * 100) for r in results if r.total_marks > 0]
    highest = max(percentages) if percentages else 0
    lowest = min(percentages) if percentages else 0
    
    return render_template('admin/student_results.html',
                         student=student,
                         results=results,
                         total_marks=total_marks,
                         total_possible=total_possible,
                         average=average,
                         highest=highest,
                         lowest=lowest)


@app.route('/admin/student/<int:student_id>/report-card/<term>')
@admin_required
def admin_generate_report_card(student_id, term):
    student = Student.query.get_or_404(student_id)
    
    results = ExamResult.query.filter_by(
        student_id=student_id,
        is_published=True
    ).join(Exam).filter(Exam.term == term).all()
    
    if not results:
        flash(f'No published results found for {student.full_name} in {term}', 'warning')
        return redirect(url_for('admin_student_results', student_id=student_id))
    
    total_marks = sum(r.marks_obtained for r in results)
    total_possible = sum(r.total_marks for r in results)
    average = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    grade_points = [r.grade_point for r in results if r.grade_point]
    avg_grade_point = sum(grade_points) / len(grade_points) if grade_points else 0
    
    return render_template('admin/report_card.html',
                         student=student,
                         results=results,
                         term=term,
                         total_marks=total_marks,
                         total_possible=total_possible,
                         average=average,
                         avg_grade_point=avg_grade_point)


@app.route('/admin/results/export/<int:exam_id>')
@admin_required
def admin_export_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    results = ExamResult.query.filter_by(exam_id=exam_id).join(Student).order_by(Student.full_name).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Admission No', 'Grade', 'Marks', 'Total', 'Percentage', 'Grade', 'Remarks'])
    
    for result in results:
        percentage = (result.marks_obtained / result.total_marks * 100) if result.total_marks > 0 else 0
        writer.writerow([
            result.student.full_name if result.student else 'Unknown',
            result.student.admission_number if result.student else '',
            result.student.grade if result.student else '',
            result.marks_obtained,
            result.total_marks,
            f"{percentage:.1f}%",
            result.grade,
            result.remarks or ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=exam_results_{exam.name}_{exam.term}.csv'
    
    log_activity(session.get('admin_user_id'), 'export_results', 'Exam', exam_id,
                f'Exported results for exam {exam.name}')
    return response


@app.route('/admin/terms')
@admin_required
def admin_terms():
    terms = Term.query.order_by(Term.academic_year.desc(), Term.id).all()
    return render_template('admin/terms.html', terms=terms)


@app.route('/admin/terms/create', methods=['POST'])
@admin_required
def admin_create_term():
    try:
        term = Term(
            name=request.form.get('name'),
            academic_year=request.form.get('academic_year'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d'),
            is_active=bool(request.form.get('is_active', False))
        )
        db.session.add(term)
        db.session.commit()
        log_activity(session.get('admin_user_id'), 'create_term', 'Term', term.id,
                    f'Created term {term.name} - {term.academic_year}')
        flash('✅ Term created successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('admin_terms'))


@app.route('/admin/terms/<int:id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_term(id):
    term = Term.query.get_or_404(id)
    term.is_active = not term.is_active
    db.session.commit()
    status = 'activated' if term.is_active else 'deactivated'
    flash(f'✅ Term {status}!', 'success')
    return redirect(url_for('admin_terms'))


@app.route('/admin/terms/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_term(id):
    term = Term.query.get_or_404(id)
    db.session.delete(term)
    db.session.commit()
    flash('✅ Term deleted', 'success')
    return redirect(url_for('admin_terms'))


# ============================================
# ADMIN - BACKUP
# ============================================

@app.route('/admin/backup')
@admin_required
def admin_backup():
    backups = Backup.query.order_by(Backup.created_at.desc()).all()
    last_backup = backups[0].created_at.strftime('%d/%m/%Y %H:%M') if backups else None
    return render_template('admin/backup.html', backups=backups, last_backup=last_backup)


@app.route('/admin/backup/create', methods=['POST'])
@admin_required
def admin_create_backup():
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.sql'
        
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'school.db')
        backup_path = os.path.join(backup_dir, filename)
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        size = os.path.getsize(backup_path)
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        
        backup = Backup(filename=filename, size=size_str)
        db.session.add(backup)
        db.session.commit()
        
        log_activity(session.get('admin_user_id'), 'create_backup', 'Backup', backup.id,
                    f'Created backup: {filename}')
        flash(f'✅ Backup created successfully: {filename}', 'success')
    except Exception as e:
        flash(f'❌ Error creating backup: {str(e)}', 'danger')
    
    return redirect(url_for('admin_backup'))


@app.route('/admin/backup/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_backup(id):
    backup = Backup.query.get_or_404(id)
    
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        filepath = os.path.join(backup_dir, backup.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass
    
    db.session.delete(backup)
    db.session.commit()
    
    log_activity(session.get('admin_user_id'), 'delete_backup', 'Backup', id,
                f'Deleted backup: {backup.filename}')
    flash('✅ Backup deleted', 'success')
    return redirect(url_for('admin_backup'))


@app.route('/admin/backup/<filename>/download')
@admin_required
def admin_download_backup(filename):
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    filepath = os.path.join(backup_dir, filename)
    
    if not os.path.exists(filepath):
        flash('❌ Backup file not found', 'danger')
        return redirect(url_for('admin_backup'))
    
    return send_file(filepath, as_attachment=True)


@app.route('/admin/backup/restore', methods=['POST'])
@admin_required
def admin_restore_backup():
    if 'backup_file' not in request.files:
        flash('❌ No file selected', 'danger')
        return redirect(url_for('admin_backup'))
    
    file = request.files['backup_file']
    if file.filename == '':
        flash('❌ No file selected', 'danger')
        return redirect(url_for('admin_backup'))
    
    if file and file.filename.endswith('.sql'):
        try:
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            filepath = os.path.join(backup_dir, file.filename)
            file.save(filepath)
            
            import shutil
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'school.db')
            shutil.copy2(filepath, db_path)
            
            log_activity(session.get('admin_user_id'), 'restore_backup', 'Backup', None,
                        f'Restored backup: {file.filename}')
            flash('✅ Database restored successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error restoring backup: {str(e)}', 'danger')
    else:
        flash('❌ Please upload a .sql file', 'danger')
    
    return redirect(url_for('admin_backup'))


# ============================================
# ADMIN - LOGS
# ============================================

@app.route('/admin/logs')
@admin_required
def admin_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs_query = ActivityLog.query.order_by(ActivityLog.created_at.desc())
    
    action = request.args.get('action')
    if action and action != 'all':
        logs_query = logs_query.filter_by(action=action)
    
    entity = request.args.get('entity')
    if entity and entity != 'all':
        logs_query = logs_query.filter_by(entity_type=entity)
    
    from_date = request.args.get('from_date')
    if from_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            logs_query = logs_query.filter(ActivityLog.created_at >= from_date)
        except:
            pass
    
    to_date = request.args.get('to_date')
    if to_date:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            logs_query = logs_query.filter(ActivityLog.created_at <= to_date)
        except:
            pass
    
    logs = logs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/logs.html',
                         logs=logs.items,
                         current_page=page,
                         total_pages=logs.pages)


# ============================================
# PARENT PORTAL ROUTES
# ============================================

@app.route('/parent/login', methods=['GET', 'POST'])
def parent_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        parent = Parent.query.filter_by(username=username, is_active=True).first()
        if parent and parent.check_password(password):
            session['parent_logged_in'] = True
            session['parent_id'] = parent.id
            session['parent_name'] = parent.full_name
            session['parent_email'] = parent.email
            session['parent_phone'] = parent.phone
            
            parent.last_login = datetime.now()
            db.session.commit()
            
            flash('✅ Welcome back, ' + parent.full_name + '!', 'success')
            return redirect(url_for('parent_dashboard'))
        else:
            flash('❌ Invalid username or password.', 'danger')
    
    return render_template('parent/login.html')


@app.route('/parent/logout')
def parent_logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('parent_login'))


@app.route('/parent/dashboard')
@parent_required
def parent_dashboard():
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    children = Student.query.filter_by(guardian_email=parent.email).all()
    
    attendance_rate = 0
    total_fees = 0
    
    for child in children:
        total_days = AttendanceRecord.query.filter_by(student_id=child.id).count()
        present_days = AttendanceRecord.query.filter_by(student_id=child.id, status='present').count()
        if total_days > 0:
            child.attendance_rate = int((present_days / total_days) * 100)
        
        fee_structure = FeeStructure.query.filter_by(grade=child.grade, is_active=True).first()
        if fee_structure:
            total_fees += fee_structure.total_fee
    
    upcoming_events = Event.query.filter(Event.event_date >= date.today(), Event.is_public == True).order_by(Event.event_date).limit(5).all()
    announcements = Announcement.query.filter_by(is_published=True).order_by(Announcement.publish_date.desc()).limit(5).all()
    
    return render_template('parent/dashboard.html',
                         parent_name=session.get('parent_name'),
                         children=children,
                         attendance_rate=attendance_rate,
                         total_fees=total_fees,
                         upcoming_events=upcoming_events,
                         announcements=announcements)


@app.route('/parent/child/<int:child_id>')
@parent_required
def parent_child_progress(child_id):
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    child = Student.query.get_or_404(child_id)
    if child.guardian_email != parent.email:
        flash('❌ You do not have access to this child.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    attendance_records = AttendanceRecord.query.filter_by(student_id=child_id).order_by(AttendanceRecord.date.desc()).limit(30).all()
    
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r.status == 'present'])
    absent_days = len([r for r in attendance_records if r.status == 'absent'])
    late_days = len([r for r in attendance_records if r.status == 'late'])
    attendance_rate = int((present_days / total_days) * 100) if total_days > 0 else 0
    
    # Get grades (using ExamResult now)
    grades = ExamResult.query.filter_by(student_id=child_id).join(Exam).order_by(Exam.exam_date.desc()).all()
    payments = FeePayment.query.filter_by(student_id=child_id).order_by(FeePayment.payment_date.desc()).all()
    
    return render_template('parent/child_progress.html',
                         child=child,
                         attendance_records=attendance_records,
                         attendance_rate=attendance_rate,
                         present_days=present_days,
                         absent_days=absent_days,
                         late_days=late_days,
                         total_days=total_days,
                         grades=grades,
                         payments=payments)


@app.route('/parent/child/<int:child_id>/results')
@parent_required
def parent_child_results(child_id):
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    child = Student.query.get_or_404(child_id)
    if child.guardian_email != parent.email:
        flash('❌ You do not have access to this child.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    results = ExamResult.query.filter_by(
        student_id=child_id,
        is_published=True
    ).join(Exam).order_by(Exam.exam_date.desc()).all()
    
    terms = {}
    term_total_marks = {}
    term_total_possible = {}
    term_averages = {}
    term_grades = {}
    subject_summary = {}
    
    for result in results:
        term = result.exam.term
        if term not in terms:
            terms[term] = []
            term_total_marks[term] = 0
            term_total_possible[term] = 0
        
        terms[term].append(result)
        term_total_marks[term] += result.marks_obtained
        term_total_possible[term] += result.total_marks
        
        subject = result.exam.subject
        if subject not in subject_summary:
            subject_summary[subject] = {'scores': [], 'avg': 0, 'grade': '-'}
        percentage = (result.marks_obtained / result.total_marks * 100) if result.total_marks > 0 else 0
        subject_summary[subject]['scores'].append(percentage)
    
    for term in terms:
        if term_total_possible[term] > 0:
            term_averages[term] = (term_total_marks[term] / term_total_possible[term]) * 100
            avg = term_averages[term]
            if avg >= 80:
                term_grades[term] = 'A'
            elif avg >= 70:
                term_grades[term] = 'B'
            elif avg >= 60:
                term_grades[term] = 'C'
            elif avg >= 50:
                term_grades[term] = 'D'
            else:
                term_grades[term] = 'E'
        else:
            term_averages[term] = 0
            term_grades[term] = '-'
    
    for subject, data in subject_summary.items():
        if data['scores']:
            data['avg'] = sum(data['scores']) / len(data['scores'])
            avg = data['avg']
            if avg >= 80:
                data['grade'] = 'A'
            elif avg >= 70:
                data['grade'] = 'B'
            elif avg >= 60:
                data['grade'] = 'C'
            elif avg >= 50:
                data['grade'] = 'D'
            else:
                data['grade'] = 'E'
    
    total_marks = sum(r.marks_obtained for r in results)
    total_possible = sum(r.total_marks for r in results)
    average = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    best_subject = '-'
    best_score = 0
    for subject, data in subject_summary.items():
        if data['avg'] > best_score:
            best_score = data['avg']
            best_subject = subject
    
    if average >= 80:
        overall_grade = 'A'
    elif average >= 70:
        overall_grade = 'B'
    elif average >= 60:
        overall_grade = 'C'
    elif average >= 50:
        overall_grade = 'D'
    else:
        overall_grade = 'E'
    
    return render_template('parent/child_results.html',
                         child=child,
                         results=results,
                         terms=terms,
                         term_total_marks=term_total_marks,
                         term_total_possible=term_total_possible,
                         term_averages=term_averages,
                         term_grades=term_grades,
                         subject_summary=subject_summary,
                         average=average,
                         best_subject=best_subject,
                         overall_grade=overall_grade)


@app.route('/parent/child/<int:child_id>/download-report/<term>')
@parent_required
def parent_download_report(child_id, term):
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    child = Student.query.get_or_404(child_id)
    if child.guardian_email != parent.email:
        flash('❌ You do not have access to this child.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    results = ExamResult.query.filter_by(
        student_id=child_id,
        is_published=True
    ).join(Exam).filter(Exam.term == term).all()
    
    if not results:
        flash(f'No published results found for {child.full_name} in {term}', 'warning')
        return redirect(url_for('parent_child_results', child_id=child_id))
    
    total_marks = sum(r.marks_obtained for r in results)
    total_possible = sum(r.total_marks for r in results)
    average = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    grade_points = [r.grade_point for r in results if r.grade_point]
    avg_grade_point = sum(grade_points) / len(grade_points) if grade_points else 0
    
    return render_template('parent/report_card.html',
                         child=child,
                         results=results,
                         term=term,
                         total_marks=total_marks,
                         total_possible=total_possible,
                         average=average,
                         avg_grade_point=avg_grade_point)


@app.route('/parent/fees')
@parent_required
def parent_fees():
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    children = Student.query.filter_by(guardian_email=parent.email).all()
    
    total_fees = 0
    total_paid = 0
    outstanding = 0
    all_payments = []
    
    for child in children:
        fee_structure = FeeStructure.query.filter_by(grade=child.grade, is_active=True).first()
        if fee_structure:
            total_fees += fee_structure.total_fee
            child.fee_structure = fee_structure
        
        payments = FeePayment.query.filter_by(student_id=child.id).all()
        child_paid = sum(p.amount for p in payments)
        total_paid += child_paid
        all_payments.extend(payments)
    
    outstanding = total_fees - total_paid
    
    return render_template('parent/fees.html',
                         children=children,
                         total_fees=total_fees,
                         total_paid=total_paid,
                         outstanding=outstanding,
                         payments=all_payments)


@app.route('/parent/profile')
@parent_required
def parent_profile():
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    children = Student.query.filter_by(guardian_email=parent.email).all()
    
    return render_template('parent/profile.html',
                         parent_name=parent.full_name,
                         parent_email=parent.email,
                         parent_phone=parent.phone,
                         parent_address=parent.address,
                         children=children,
                         children_count=len(children),
                         member_since=parent.created_at.strftime('%d %B %Y') if parent.created_at else 'N/A')


@app.route('/parent/profile/update', methods=['POST'])
@parent_required
def parent_update_profile():
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    try:
        parent.full_name = request.form.get('full_name')
        parent.phone = request.form.get('phone')
        parent.address = request.form.get('address')
        
        session['parent_name'] = parent.full_name
        session['parent_phone'] = parent.phone
        
        db.session.commit()
        flash('✅ Profile updated successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    
    return redirect(url_for('parent_profile'))


@app.route('/parent/change-password', methods=['POST'])
@parent_required
def parent_change_password():
    parent_id = session.get('parent_id')
    parent = Parent.query.get(parent_id)
    
    current = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not parent.check_password(current):
        flash('❌ Current password is incorrect.', 'danger')
        return redirect(url_for('parent_profile'))
    
    if new_password != confirm_password:
        flash('❌ Passwords do not match.', 'danger')
        return redirect(url_for('parent_profile'))
    
    if len(new_password) < 6:
        flash('❌ Password must be at least 6 characters.', 'danger')
        return redirect(url_for('parent_profile'))
    
    try:
        parent.set_password(new_password)
        db.session.commit()
        flash('✅ Password changed successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    
    return redirect(url_for('parent_profile'))


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ============================================
# RUN THE APPLICATION
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 BRIGHT MINDS ACADEMY - SCHOOL MANAGEMENT SYSTEM")
    print("=" * 60)
    print("✅ Database: SQLite (school.db)")
    print(f"✅ Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("✅ Default Admin: admin / admin123")
    print("✅ Default Parent: parent / parent123")
    print("=" * 60)
    print("📍 Website: http://localhost:5001")
    print("📍 Admin:   http://localhost:5001/admin/login")
    print("📍 Parent:  http://localhost:5001/parent/login")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)