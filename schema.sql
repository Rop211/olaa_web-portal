-- ============================================
-- BRIGHT MINDS ACADEMY - COMPLETE DATABASE SCHEMA
-- ============================================

-- 1. ADMIN USERS
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. APPLICATIONS
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    grade VARCHAR(20) NOT NULL,
    parent_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    additional_notes TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. TOUR BOOKINGS
CREATE TABLE tour_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    preferred_date DATE NOT NULL,
    preferred_time VARCHAR(20) NOT NULL,
    number_of_people INTEGER DEFAULT 2,
    child_age VARCHAR(20),
    status VARCHAR(20) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. NEWSLETTER SUBSCRIBERS
CREATE TABLE newsletter_subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at DATETIME
);

-- 5. TESTIMONIALS
CREATE TABLE testimonials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    child_grade VARCHAR(20),
    content TEXT NOT NULL,
    rating INTEGER DEFAULT 5,
    is_approved BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. GALLERY IMAGES
CREATE TABLE gallery_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100),
    filename VARCHAR(200) NOT NULL,
    caption VARCHAR(200),
    category VARCHAR(50),
    is_featured BOOLEAN DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. CONTACT MESSAGES
CREATE TABLE contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    subject VARCHAR(200),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    is_replied BOOLEAN DEFAULT 0,
    replied_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. STUDENTS
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10),
    grade VARCHAR(20) NOT NULL,
    guardian_name VARCHAR(100) NOT NULL,
    guardian_phone VARCHAR(20) NOT NULL,
    guardian_email VARCHAR(100),
    address TEXT,
    medical_notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    enrolled_date DATE DEFAULT CURRENT_DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 9. FEE STRUCTURES
CREATE TABLE fee_structures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade VARCHAR(20) UNIQUE NOT NULL,
    tuition_fee FLOAT DEFAULT 0,
    activity_fee FLOAT DEFAULT 0,
    lunch_fee FLOAT DEFAULT 0,
    transport_fee FLOAT DEFAULT 0,
    other_fees FLOAT DEFAULT 0,
    total_fee FLOAT DEFAULT 0,
    term VARCHAR(20),
    academic_year VARCHAR(20),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 10. FEE PAYMENTS
CREATE TABLE fee_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    application_id INTEGER,
    amount FLOAT NOT NULL,
    payment_date DATE DEFAULT CURRENT_DATE,
    payment_method VARCHAR(50),
    transaction_reference VARCHAR(100),
    receipt_number VARCHAR(50) UNIQUE,
    description VARCHAR(200),
    term VARCHAR(20),
    status VARCHAR(20) DEFAULT 'Paid',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

-- 11. EVENTS
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_time VARCHAR(20),
    end_date DATE,
    location VARCHAR(100),
    event_type VARCHAR(50),
    is_public BOOLEAN DEFAULT 1,
    is_featured BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 12. STAFF
CREATE TABLE staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    position VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    qualifications TEXT,
    experience_years INTEGER DEFAULT 0,
    bio TEXT,
    profile_image VARCHAR(200),
    is_active BOOLEAN DEFAULT 1,
    hire_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 13. ANNOUNCEMENTS
CREATE TABLE announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'Normal',
    is_published BOOLEAN DEFAULT 0,
    publish_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATETIME,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admin_users(id)
);

-- 14. SCHOOL SETTINGS
CREATE TABLE school_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_group VARCHAR(50),
    description VARCHAR(200),
    is_public BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 15. ACTIVITY LOGS
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_created_at ON applications(created_at);
CREATE INDEX idx_applications_grade ON applications(grade);

CREATE INDEX idx_tour_bookings_status ON tour_bookings(status);
CREATE INDEX idx_tour_bookings_date ON tour_bookings(preferred_date);

CREATE INDEX idx_students_grade ON students(grade);
CREATE INDEX idx_students_admission ON students(admission_number);
CREATE INDEX idx_students_guardian ON students(guardian_phone);

CREATE INDEX idx_fee_payments_student ON fee_payments(student_id);
CREATE INDEX idx_fee_payments_date ON fee_payments(payment_date);

CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_type ON events(event_type);

CREATE INDEX idx_announcements_published ON announcements(is_published);
CREATE INDEX idx_announcements_publish_date ON announcements(publish_date);

CREATE INDEX idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_created ON activity_logs(created_at);

-- ============================================
-- DEFAULT DATA
-- ============================================

-- Create default admin user (password: admin123)
INSERT INTO admin_users (username, password_hash, email, full_name, role) 
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin@brightminds.ac.ke', 'System Administrator', 'admin');

-- Create default school settings
INSERT INTO school_settings (setting_key, setting_value, setting_group, description) VALUES
('school_name', 'Bright Minds Academy', 'General', 'School name'),
('school_tagline', 'Where every child''s future begins', 'General', 'School tagline'),
('school_address', 'Nairobi, Kenya', 'Contact', 'School address'),
('school_phone', '+254 700 000 000', 'Contact', 'School phone number'),
('school_email', 'info@brightminds.ac.ke', 'Contact', 'School email'),
('school_facebook', 'https://facebook.com/brightminds', 'Social', 'Facebook URL'),
('school_twitter', 'https://twitter.com/brightminds', 'Social', 'Twitter URL'),
('school_instagram', 'https://instagram.com/brightminds', 'Social', 'Instagram URL'),
('school_youtube', 'https://youtube.com/brightminds', 'Social', 'YouTube URL');