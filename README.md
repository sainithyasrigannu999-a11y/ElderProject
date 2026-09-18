# ElderGuard AI

## Problem statement
Many elderly people live alone and may face accidents, dizziness, chest pain, breathing problems, or sudden weakness without immediate support. Traditional SOS buttons are often too simple because they do not assess the situation or confirm whether the person needs help.

## Existing solutions
Most current systems rely on basic SOS alarms, manual calls, or wearable devices. These may help during a crisis, but they often do not provide a structured workflow to assess risk, confirm the person's condition, or escalate support when there is no response.

## Our innovation
ElderGuard AI does not just send an SOS. It analyzes the emergency, confirms the elderly person's condition, and escalates the alert when help is needed.

Main flow: Detect → Confirm → Assess → Alert → Assist

## Features
- Elderly user registration and login
- Secure password hashing
- Large emergency SOS buttons designed for accessibility
- Voice input with browser speech recognition
- Lightweight Python NLP emergency classifier
- Confirmation workflow with timeout escalation
- Caregiver dashboard and emergency details
- Emergency history and notifications
- Optional location capture using browser geolocation
- Role-based access control

## Future scope
- Automatic fall detection using smart watches, motion sensors, or cameras
- Heart-rate monitoring
- GPS tracking
- Multilingual AI voice
- SMS integration
- Hospital and ambulance coordination
- Advanced ML/NLP models

## System flow
1. Elderly person presses SOS or uses voice input.
2. Emergency text is processed by the AI classifier.
3. Severity is estimated.
4. System asks, "Are you okay?"
5. If the user says they are okay, the event is cancelled.
6. If they need help or ignore the prompt, a caregiver alert is sent.
7. Caregiver views emergency details, acknowledges it, and resolves it.

## Technology stack
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Backend: Flask, Python
- Database: MySQL (with SQLite fallback for local development)
- AI: lightweight rule-based classification module for MVP

## Folder structure
- app.py
- config.py
- requirements.txt
- README.md
- .env.example
- .gitignore
- database/
- ai/
- routes/
- services/
- templates/
- static/
- tests/

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## MySQL setup
1. Create a MySQL database named elderguard_ai.
2. Update .env with your database values.
3. Run the SQL schema using your preferred MySQL client.

Example:
```sql
CREATE DATABASE elderguard_ai;
USE elderguard_ai;
```

## Environment variables
Create a .env file based on .env.example.

```env
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=elderguard_ai
DB_URI=sqlite:///elderguard_ai.db
SECRET_KEY=your_secret_key
SMTP_USER=
SMTP_PASSWORD=
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
CONFIRMATION_TIMEOUT=30
```

## How to run
```bash
python app.py
```
Then open:
http://127.0.0.1:5001/

## How to test
```bash
pytest
```

## Demo credentials
- Elderly user: elder@example.com / password123
- Caregiver: caregiver@example.com / password123

## Limitations
The current MVP uses SOS and voice input for emergency initiation. Automatic fall detection using hardware, sensors, wearables, or cameras is future scope.

## Disclaimer
The current MVP is designed for demonstration and safety assistance workflows. It should not be treated as a medical device or real-time automated fall detection system.
