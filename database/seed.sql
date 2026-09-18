INSERT OR IGNORE INTO users (id, name, email, phone, age, gender, password_hash, role) VALUES
    (1, 'Maya Elder', 'elder@example.com', '5551110001', 72, 'Female', '$2b$12$3kW7oSTkQ2zXC9.IGYk2FOl3kn2OIgSXy12DkJoZ3UjjaNw0uYfM2', 'elderly'),
    (2, 'Rohan Care', 'caregiver@example.com', '5552220002', 40, 'Male', '$2b$12$3kW7oSTkQ2zXC9.IGYk2FOl3kn2OIgSXy12DkJoZ3UjjaNw0uYfM2', 'caregiver');

INSERT OR IGNORE INTO caregiver_connections (id, elderly_user_id, caregiver_user_id, relationship) VALUES
    (1, 1, 2, 'Grandson');

INSERT OR IGNORE INTO emergency_contacts (id, user_id, contact_name, contact_phone, contact_email) VALUES
    (1, 1, 'Rohan Care', '5552220002', 'caregiver@example.com');

INSERT OR IGNORE INTO emergencies (id, user_id, category, description, severity, ai_confidence, input_type, confirmation_status, status, location_text, created_at) VALUES
    (1, 1, 'Fall', 'I fell down and I cannot get up.', 'CRITICAL', 0.92, 'voice', 'CONFIRMED', 'RESOLVED', 'Living room', '2026-09-18 08:30:00');

INSERT OR IGNORE INTO notifications (id, recipient_id, emergency_id, message, is_read, created_at) VALUES
    (1, 2, 1, 'New emergency alert for Maya Elder', 0, '2026-09-18 08:30:00');
