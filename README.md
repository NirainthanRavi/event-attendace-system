# College Event Attendance Management System

A Flask-based web application designed to streamline student attendance and visitor tracking during college events, orientations, or academic functions. The system allows students to verify their details using their mobile number, date of birth, and department, while administrators can monitor attendance statistics through a dashboard.

## Features

### Student Portal
- Search student records using:
  - Mobile Number
  - Date of Birth
  - Department
- View assigned:
  - Room Number
  - Seat Number
- Record accompanying family members/parents.
- Automatically mark attendance upon successful verification.

### Admin Dashboard
- Secure admin login.
- View real-time analytics:
  - Total registered students
  - Students present
  - Total accompanying parents/visitors
  - Overall attendance percentage

### Database Integration
- MongoDB backend for storing and retrieving student records.
- Automatic attendance updates.
- Parent/visitor count tracking.

---

## Tech Stack

### Backend
- Python
- Flask
- PyMongo

### Database
- MongoDB

### Frontend
- HTML
- CSS
- JavaScript
- Jinja2 Templates

---

## Project Structure

```text
clg_app/
│
├── app.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   ├── login.html
│   └── dashboard.html
│
└── static/
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/NirainthanRavi/event-attendance-system.git
cd college-attendance-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/Mac**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install flask pymongo
```

### 4. Start MongoDB

Ensure MongoDB is running locally on:

```text
mongodb://localhost:27017/
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---

## Database Schema

Example student document:

```json
{
  "name": "John Doe",
  "mobile number": 9876543210,
  "DOB": "01-01-2005",
  "dept": "BCA",
  "room number": "A101",
  "seat number": "15",
  "status": "ABSENT",
  "parent count": 0,
  "parent status": "ABSENT"
}
```

---

## Admin Credentials

Default credentials configured in the application:

```text
Username: admin
Password: admin123
```

> For production deployment, store credentials securely using environment variables.

---

## Workflow

1. Student enters mobile number, DOB, and department.
2. System searches the MongoDB database.
3. If a matching record is found:
   - Student details are displayed.
   - Attendance is marked as PRESENT.
   - Parent count is updated.
4. Administrators can log in to view attendance statistics and visitor counts.

---

## Future Enhancements

- QR code-based attendance.
- Export attendance reports to Excel/PDF.
- Role-based authentication.
- Attendance history tracking.
- Cloud database deployment.
- Email/SMS notifications.
- Improved security using password hashing.

---

## License

This project is intended for educational and institutional use.

---

## Author

**Nirainthan Ravi**

Developed as a college event attendance and student verification system using Flask and MongoDB.