from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename 
import os
from datetime import datetime
from models import db, Admin, Student, Company, Drive, Application
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    role = session.get("role")
    if role == "admin":
        return Admin.query.get(int(user_id))
    if role == "student":
        return Student.query.get(int(user_id))
    if role == "company":
        return Company.query.get(int(user_id))

    return None

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register_student", methods=["GET","POST"])
def register_student():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        education = request.form["education"]
        skills = request.form["skills"]

        resume_file = request.files["resume"]

        filename = None

        if resume_file:
            filename = secure_filename(resume_file.filename)
            resume_file.save(os.path.join("static/resumes", filename))

        student = Student(
            name=name,
            email=email,
            password=password,
            education=education,
            skills=skills,
            resume=filename
        )

        db.session.add(student)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register_student.html")


@app.route("/register_company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        hr_contact = request.form["hr_contact"]
        website = request.form["website"]
        password = generate_password_hash(request.form["password"])

        company = Company(name=name, email=email, password=password, hr_contact=hr_contact, website=website)
        db.session.add(company)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register_company.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = None

        if role == "admin":
            user = Admin.query.filter_by(email=email).first()

        elif role == "student":
            user = Student.query.filter_by(email=email).first()

        elif role == "company":
            user = Company.query.filter_by(email=email).first()
            if user:
                if user.status == "Pending":
                    return "Company not approved yet"
                if user.status == "Rejected":
                    return "Your company registration was rejected by admin"

        if user and check_password_hash(user.password, password):
            session["role"] = role
            login_user(user)

            if role == "admin":
                return redirect(url_for("admin_dashboard"))
            if role == "student":
                return redirect(url_for("student_dashboard"))
            if role == "company":
                return redirect(url_for("company_dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for("login"))


@app.route("/admin_dashboard")
def admin_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    companies = Company.query.all()
    students = Student.query.all()
    drives = Drive.query.all()
    applications = Application.query.all()

    total_companies = Company.query.count()
    total_students = Student.query.count()
    total_drives = Drive.query.count()
    total_applications = Application.query.count()

    return render_template(
        "admin_dashboard.html",
        companies=companies,
        students=students,
        drives=drives,
        total_companies=total_companies,
        total_students=total_students,
        total_drives=total_drives,
        total_applications=total_applications
    )


@app.route("/approve_company/<int:id>")
def approve_company(id):
    company = Company.query.get_or_404(id)
    company.status = "Approved"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/reject_company/<int:id>")
def reject_company(id):
    company = Company.query.get_or_404(id)
    company.status = "Rejected"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/approve_drive/<int:id>")
def approve_drive(id):
    drive = Drive.query.get(id)
    drive.status = "Approved"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/reject_drive/<int:id>")
def reject_drive(id):
    drive = Drive.query.get_or_404(id)
    Application.query.filter_by(drive_id=id).delete()
    db.session.delete(drive)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/student_dashboard")
def student_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    keyword = request.args.get("keyword")

    if keyword:

        companies = Company.query.filter(
            Company.name.contains(keyword)
        ).all()

    else:

        companies = Company.query.all()

    drives = Drive.query.filter_by(status="Approved").all()

    applications = Application.query.filter_by(
        student_id=current_user.id
    ).all()

    applied_drive_ids = [app.drive_id for app in applications]

    return render_template(
        "student_dashboard.html",
        drives=drives,
        applications=applications,
        applied_drive_ids=applied_drive_ids,
        companies=companies
    )

@app.route("/apply/<int:drive_id>")
def apply(drive_id):

    existing = Application.query.filter_by(
        student_id=current_user.id,
        drive_id=drive_id
    ).first()

    if existing:
        return "Already applied"

    application = Application(
        student_id=current_user.id,
        drive_id=drive_id
    )

    db.session.add(application)
    db.session.commit()

    return redirect(url_for("student_dashboard"))


@app.route("/company_dashboard")
def company_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    upcoming_drives = Drive.query.filter_by(
        company_id=current_user.id,
        status="Approved"
    ).all()

    closed_drives = Drive.query.filter_by(
        company_id=current_user.id,
        status="Closed"
    ).all()

    return render_template(
        "company_dashboard.html",
        upcoming_drives=upcoming_drives,
        closed_drives=closed_drives
    )

@app.route("/create_drive", methods=["GET","POST"])
def create_drive():

    if session.get("role") != "company":
        return "Unauthorized Access"

    if current_user.status != "Approved":
        return "Company not approved yet"

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        eligibility = request.form["eligibility"]
        deadline = datetime.strptime(request.form["deadline"], "%Y-%m-%d")

        skills = request.form["skills"]
        experience = request.form["experience"]
        salary = request.form["salary"]

        drive = Drive(
            company_id=current_user.id,
            job_title=title,
            job_description=description,
            eligibility=eligibility,
            deadline=deadline,
            required_skills=skills,
            experience=experience,
            salary=salary
        )

        db.session.add(drive)
        db.session.commit()

        return redirect(url_for("company_dashboard"))

    return render_template("create_drive.html")

@app.route("/drive_details/<int:id>")
def drive_details(id):

    drive = Drive.query.get(id)

    applications = Application.query.filter_by(
        student_id=current_user.id
    ).all()

    applied_drive_ids = [app.drive_id for app in applications]

    return render_template(
        "drive_details.html",
        drive=drive,
        applied_drive_ids=applied_drive_ids
    )

@app.route("/drive_details_company/<int:id>")
def drive_details_company(id):

    drive = Drive.query.get_or_404(id)

    if drive.company_id != current_user.id:
        return "Unauthorized Access"

    applications = Application.query.filter_by(
        drive_id=id
    ).all()

    return render_template(
        "drive_applications.html",
        applications=applications,
        drive=drive
    )

@app.route("/application_history")
def application_history():

    applications = Application.query.filter_by(
        student_id=current_user.id
    ).all()

    return render_template(
        "application_history.html",
        applications=applications
    )

@app.route("/view_applications/<int:drive_id>")
def view_applications(drive_id):
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template("view_applications.html", applications=applications)

@app.route("/review_application/<int:id>", methods=["GET","POST"])
def review_application(id):

    application = Application.query.get_or_404(id)

    if application.drive.company_id != current_user.id:
        return "Unauthorized Access"

    if request.method == "POST":

        application.status = request.form["status"]

        db.session.commit()

        return redirect(url_for(
            "drive_details_company",
            id=application.drive_id
        ))

    return render_template(
        "review_application.html",
        application=application
    )

@app.route("/update_status/<int:app_id>/<status>")
def update_status(app_id, status):

    application = Application.query.get(app_id)
    application.status = status

    db.session.commit()

    return redirect(url_for("company_dashboard"))

@app.route("/search_student", methods=["POST"])
def search_student():

    keyword = request.form["keyword"]

    students = Student.query.filter(
        Student.name.contains(keyword) |
        Student.email.contains(keyword)
    ).all()

    companies = Company.query.all()
    drives = Drive.query.all()

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = Drive.query.count()
    total_applications = Application.query.count()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        drives=drives,
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications
    )

@app.route("/search_company", methods=["POST"])
def search_company():

    keyword = request.form["keyword"]

    companies = Company.query.filter(
        Company.name.contains(keyword)
    ).all()

    students = Student.query.all()
    drives = Drive.query.all()

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = Drive.query.count()
    total_applications = Application.query.count()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        drives=drives,
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications
    )

@app.route("/delete_student/<int:id>")
def delete_student(id):

    student = Student.query.get(id)

    Application.query.filter_by(student_id=id).delete()

    db.session.delete(student)
    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/delete_company/<int:id>")
def delete_company(id):

    company = Company.query.get(id)

    drives = Drive.query.filter_by(company_id=id).all()

    for drive in drives:
        Application.query.filter_by(drive_id=drive.id).delete()
        db.session.delete(drive)

    db.session.delete(company)

    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/company_details/<int:id>")
def company_details(id):

    company = Company.query.get(id)

    drives = Drive.query.filter_by(
        company_id=id,
        status="Approved"
    ).all()

    return render_template(
        "company_details.html",
        company=company,
        drives=drives
    )

@app.route("/student_profile/<int:id>")
def student_profile(id):

    student = Student.query.get_or_404(id)

    return render_template(
        "student_profile.html",
        student=student
    )

@app.route("/edit_profile", methods=["GET","POST"])
def edit_profile():

    if request.method == "POST":

        current_user.name = request.form["name"]
        current_user.email = request.form["email"]
        current_user.education = request.form["education"]
        current_user.skills = request.form["skills"]

        resume_file = request.files.get("resume")
        if resume_file and resume_file.filename != "":

            filename = secure_filename(resume_file.filename)

            upload_folder = os.path.join("static","resumes")

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            resume_file.save(os.path.join(upload_folder, filename))

            current_user.resume = filename

        db.session.commit()

        return redirect(url_for("student_dashboard"))

    return render_template("edit_profile.html")

@app.route("/mark_closed/<int:id>")
def mark_closed(id):

    drive = Drive.query.get_or_404(id)

    if drive.company_id != current_user.id:
        return "Unauthorized Access"

    drive.status = "Closed"

    db.session.commit()

    return redirect(url_for("company_dashboard"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        admin = Admin.query.filter_by(email="admin@portal.com").first()
        if not admin:
            admin = Admin(
                email="admin@portal.com",
                password=generate_password_hash("admin123")
            )
            db.session.add(admin)
            db.session.commit()

    app.run(host='0.0.0.0', debug=True)