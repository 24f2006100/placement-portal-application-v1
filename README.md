# Placement-portal-application-v1
This is a multi user web application that allows the institute administration, companies, and students to interact through a centralized system. The system manages placement drives, student applications, and recruitment status while ensuring proper role-based access and data management.

## Features

**Admin**
- Approve or reject company registrations
- Approve or reject placement drives
- View system statistics (students, companies, drives, applications)
- Manage students and companies

**Company**
- Register and create company profile
- Create placement drives
- View student applications
- Update application status (Shortlisted / Selected / Rejected)

**Student**
- Register and update profile
- Upload resume
- View available placement drives
- Apply for drives
- Track application status

## Tech Stack

- **Flask** – Backend framework  
- **SQLite** – Database  
- **SQLAlchemy** – ORM  
- **Jinja2** – Templating  
- **Bootstrap** – UI Styling  
- **Flask-Login** – Authentication  

## How to Run the Project

1. Open the project folder in your system.

2. Install the required dependencies:
`pip install -r requirements.txt`

3. Run the application:
`python app.py`
