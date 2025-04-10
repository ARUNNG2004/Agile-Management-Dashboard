import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive Agg
from flask import render_template, redirect, url_for, flash, request, session, Blueprint, jsonify, get_flashed_messages
from . import db, bcrypt, mail
from .models import User, Admin, Project, Sprint, UserStory
from flask_mail import Message
from app import mail
import pyotp
import logging
from sqlalchemy import text
from flask import render_template, flash, redirect, url_for
from app.models import Project, UserStory, Sprint, User  # Import your models
from datetime import datetime
from flask import request
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta,date
import random
import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import date2num
from app.emails_utils import send_project_notification
from apscheduler.schedulers.background import BackgroundScheduler
import pdfkit
import os
import io

def generate_burndown_chart(project_id):
    # Fetch sprints for the given project
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number).all()
    
    if not sprints:
        return "No sprints found for the project"

    print("Fetched Sprints:", sprints)

    # Sprint labels
    sprint_labels = [f"Sprint {s.sprint_number}" for s in sprints]

    # Calculate total work at the start (assuming sum of all sprint velocities)
    total_work = sum(s.velocity for s in sprints)  

    # Compute remaining work after each sprint
    remaining_work = [total_work - sum(s.velocity for s in sprints[:i+1]) for i in range(len(sprints))]

    # Ensure no division by zero
    num_sprints = max(1, len(sprints) - 1)
    # Ideal Burndown Line (linear decrease)
    ideal_burndown = [total_work * (1 - i / num_sprints) for i in range(len(sprints))]

    # Create burndown chart
    plt.figure(figsize=(8, 5))

    # Plot actual burndown (progress)
    plt.plot(sprint_labels, remaining_work, marker='o', color='red', linestyle='-', label='Actual Progress')

    # Plot ideal burndown
    plt.plot(sprint_labels, ideal_burndown, marker='o', color='blue', linestyle='--', label='Ideal Burndown')

    # Titles & Labels
    plt.title('Burndown Chart')
    plt.xlabel('Sprints')
    plt.ylabel('Remaining Work (Story Points)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    # Convert plot to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    image_png = buffer.getvalue()
    buffer.seek(0)
    plt.close()

    return base64.b64encode(image_png).decode('utf-8')
 
def generate_burnup_chart(project_id):
    # Fetch sprints for the given project
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number).all()
    print(sprints)
    sprint_labels = [f"Sprint {s.sprint_number}" for s in sprints]
    total_velocity = [s.velocity for s in sprints]
    completed_velocity = [s.velocity if s.status.lower() == 'completed' else 0 for s in sprints]
    # print(sprints)
 
    # Plot the chart
    plt.figure(figsize=(8, 5))
    plt.plot(sprint_labels, completed_velocity, 'g-', marker='o', label='Completed')
    plt.plot(sprint_labels, total_velocity, 'b--', label='Total Work')
   
    plt.title('Burnup Chart')
    plt.xlabel('Sprints')
    plt.ylabel('Story points')
    plt.legend()
    plt.grid(True)
 
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    return base64.b64encode(image_png).decode('utf-8')
 
def generate_velocity_chart(project_id):
    # Fetch sprints for the given project
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number).all()
    print("Fetched Sprints:", sprints)
 
    # Sprint labels
    sprint_labels = [f"Sprint {s.sprint_number}" for s in sprints]
 
    # Total velocity (story points per sprint)
    total_velocity = [s.velocity for s in sprints]
 
    # Create bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(sprint_labels, total_velocity, color='blue', alpha=0.7, label='Velocity')
 
    # Titles & Labels
    plt.title(f'Velocity Chart for Project {project_id}')
    plt.xlabel('Sprints')
    plt.ylabel('Velocity (Story Points)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
 
    # Convert plot to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
 
    return base64.b64encode(image_png).decode('utf-8')

    # Burn-Down Chart: Tracks the remaining effort throughout the sprint lifecycle, helping teams visualize if they are on track.
    # Burn-Up Chart: Illustrates cumulative work completed, ensuring the team meets projected targets.
    # Velocity Chart: Highlights story points achieved per sprint, reflecting team consistency and adaptability.

auth = Blueprint("auth", __name__, template_folder='templates/auth', static_folder='static')
admin = Blueprint("admin", __name__, template_folder='templates/admin', static_folder='static', url_prefix='/admin')
main = Blueprint('main', __name__)

INACTIVITY_TIMEOUT = timedelta(minutes=15)
otp_storage = {}
@auth.route('/extend_session', methods=['POST'])
def extend_session():
    if 'last_activity' in session:
        # Extend the session by 10 minutes
        session['last_activity'] = (datetime.now() + timedelta(minutes=10)).isoformat()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400
@auth.route('/check_inactivity')
def check_inactivity_status():
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        time_since_last_activity = datetime.now() - last_activity
        if time_since_last_activity > INACTIVITY_TIMEOUT:
            return jsonify({'inactive': True, 'time_left': 0})
        else:
            time_left = INACTIVITY_TIMEOUT - time_since_last_activity
            return jsonify({'inactive': False, 'time_left': time_left.total_seconds()})
    return jsonify({'inactive': False, 'time_left': None})

def generate_mfa_qr_code(user_email,mfa_secret):
    # Create a TOTP object
    totp = pyotp.TOTP(mfa_secret)

    # Generate the provisioning URI for the QR code
    provisioning_uri = totp.provisioning_uri(name=user_email, issuer_name="AgileApp")

    # Generate the QR code
    qr = qrcode.make(provisioning_uri)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return qr_code
def create_initial_admin():
    admin_email = 'infosysdhruv@gmail.com'
    admin_password = bcrypt.generate_password_hash('123', 10)

    # Check if an admin with the given email already exists
    admin_exists = Admin.query.filter_by(email=admin_email).first()

    if not admin_exists:
        admin = Admin(email=admin_email, password=admin_password)
        db.session.add(admin)
        db.session.commit()
        print("Initial admin created successfully.")
    else:
        print("Initial admin already exists.")
# Admin login
@admin.route('/', methods=["POST", "GET"])
def adminIndex():
    create_initial_admin()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email == "" or password == "":
            flash('Please fill all the fields', 'danger')
            return redirect(url_for('admin.adminIndex'))

        # Check if the admin exists and the password is correct
        admin = Admin.query.filter_by(email=email).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session['admin_email'] = admin.email
            session['admin_password']=admin.password
            flash('Login Successful', 'success')
            return redirect(url_for('admin.adminDashboard'))
        else:
            flash('Invalid Email or Password', 'danger')
            return redirect(url_for('admin.adminIndex'))
    else:
        return render_template('index.html', title="Admin Login")
@admin.route('/get-user-stats', methods=['GET'])
def get_user_stats():
    users = User.query.all()
    user_data = []

    active_count = 0
    logged_out_count = 0
    rejected_count = 0
    approved_count = 0
    pending_count = 0

    for user in users:
        if user.status == 3:  # Active users
            active_count += 1
        elif user.status == 4:  # Logged out users
            logged_out_count += 1
        elif user.status == 2:  # Rejected users
            rejected_count += 1
        elif user.status == 1:  # Approved users
            approved_count += 1
        else:  # Pending users
            pending_count += 1

        # Handle last_login for rejected and pending users
        if user.status == 2 or user.status == 0:  # Rejected or Pending
            last_login = "N/A"
        else:
            last_login = user.logout if user.logout else "N/A"  # Handle null values for other statuses

        user_data.append({
            "id": user.id,
            "name": user.name,
            "status": user.status,
            "last_login": last_login
        })

    return jsonify({
        "users": user_data,
        "active_count": active_count,
        "logged_out_count": logged_out_count,
        "rejected_count": rejected_count,
        "approved_count": approved_count,
        "pending_count": pending_count
    })
# Admin Dashboard
@admin.route('/dashboard')
def adminDashboard():
    if not session.get('admin_id'):
        return redirect(url_for('auth.home'))

    totalUser = User.query.count()
    totalApprove = User.query.filter_by(status=1).count()
    NotTotalApprove = User.query.filter_by(status=0).count()

    return render_template('admin/dashboard.html', title="Admin Dashboard", totalUser=totalUser, totalApprove=totalApprove, NotTotalApprove=NotTotalApprove)
# Admin get all users
@admin.route('/get-all-user', methods=["POST", "GET"])
def adminGetAllUser():
    # Clear any existing flash messages
    get_flashed_messages()
    if not session.get('admin_id'):
        return redirect(url_for('auth.home'))
    if request.method == "POST":
        search = request.form.get('search')
        users = User.query.filter(User.name.like('%' + search + '%')).all()
        return render_template('all-user.html', title='Approve User', users=users)
    else:
        users = User.query.all()
        return render_template('all-user.html', title='Approve User', users=users)

@admin.route("/reject_user/<int:id>")
def reject_user(id):
    if not session.get('admin_id'):
        return redirect(url_for('auth.home'))
    user = User.query.get(id)
    if user:
        user.status=2
        user_email = user.email
        db.session.commit()

        msg = Message(
            subject="Account Rejection Notification",
            recipients=[user_email],
        )
        msg.body = f"Dear User,\n\nWe regret to inform you that your registration request has been rejected.\n\nBest Regards,\nAdmin Team"
        mail.send(msg)

        flash("User has been rejected and notified via email.", "success")
    else:
        flash("User not found.", "warning")
    return redirect(url_for("admin.adminGetAllUser"))
# Admin approve user
@admin.route('/approve-user/<int:id>')
def adminApprove(id):
    if not session.get('admin_id'):
        return redirect(url_for('auth.home'))
    User.query.filter_by(id=id).update(dict(status=1))
    db.session.commit()
    user = User.query.get(id)
    user_email = user.email
    username = user.name
    msg = Message(
            subject="Account Approval Notification",

            recipients=[user_email]
        )
    msg.body = f"Dear User,\n\nWe kindly  inform you that your registration request has been Approved. Please you can login now \n\nBest Regards,\nAdmin Team"
    mail.send(msg)
    flash(f'{user.name}  has been approved and notified via email..', 'success')
    return redirect(url_for('admin.adminGetAllUser'))

# Admin change password
@admin.route('/change-admin-password', methods=["POST", "GET"])
def adminChangePassword():
    admin = Admin.query.get(1)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == "" or password == "":
            flash('Please fill all the fields', 'danger')
            return redirect(url_for('admin.adminChangePassword'))
        else:
            Admin.query.filter_by(email=email).update(dict(password=bcrypt.generate_password_hash(password, 10)))
            db.session.commit()
            flash('Admin Password Updated Successfully', 'success')
            return redirect(url_for('admin.adminChangePassword'))
    else:
        return render_template('admin-change-password.html', title='Admin Change Password', admin=admin)

# Admin logout
@admin.route('/logout')
def adminLogout():
    if not session.get('admin_id'):
        return redirect(url_for('auth.login'))
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    return redirect(url_for('auth.home'))

@auth.route('/')
def home():
    return render_template('homepage.html',title="Agile Management")

# Auth register login.html contain this route
@auth.route('/register')
def register():
    # Clear any existing flash messages
    get_flashed_messages()
    return render_template('register.html', title="Sign-up")

# Auth login
@auth.route('/login')
def login():
    # Clear any existing flash messages
    get_flashed_messages()
    return render_template('login.html', title='Login')

# Auth signup
@auth.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        dob_str= request.form.get('dob')
        gender=request.form.get('gender')
        address=request.form.get('address')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        role=request.form.get('role')
        mfa=request.form.get('enable_2fa')=='true'
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('auth.signup'))

        existing_user = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if existing_user:
            flash('Email or phone number already registered.', 'danger')
            return redirect(url_for('auth.signup'))

        indian_phone_regex = r'^(\+91[\-\s]?)?[6789]\d{9}$'

        if not re.match(indian_phone_regex, phone):
            flash('Please enter a valid Indian phone number.', 'danger')
            return redirect(url_for('auth.signup'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        if mfa:
            mfa_secret = pyotp.random_base32()
        else:
            mfa_secret=None
        new_user = User(name=name, email=email, phone=phone, password=hashed_password,role=role,mfa_secret=mfa_secret,dob=dob,gender=gender,address=address,mfa=int(mfa))
        # Save the user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Wait for admin approval.', 'success')
            msg = Message(
            subject="New User Registration Alert",
            recipients=['teamofadm1n123@gmail.com'],
            )
            msg.body = f"Hello Admin,\n\nA new user has just registered on the Agile Management Dashboard.\n\nBest Regards,\nAdmin Team"
            mail.send(msg)
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            print(f"Error: {e}")  # Log the error for debugging
            return redirect(url_for('auth.signup'))
    return render_template('register.html',title='Sign-up')
@auth.route('/redirect_reset_password')
def redirect_reset_password():
    return render_template('reset_password.html')

@auth.route('/reset_password',methods=['GET','POST'])
def reset_password():
    try:
        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm-password')
            if new_password != confirm_password:
                flash('Passwords do not match. Please try again.', 'danger')
                return redirect(url_for('auth.reset_password'))
            # Update the user's password
            new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')  # Hash the new password
            User.query.filter_by(email=session['reset_email']).update({'password': new_password})
            db.session.commit()

            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.login'))

        return render_template('reset_password.html')
    except:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
@auth.route('/redirect_forgot_password')
def redirect_forgot_password():
    return render_template('forgot_password.html')
@auth.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    if request.method=="POST":
        email=request.form.get('email')
        if email == "" :
            flash('Please fill the field','danger')
            return redirect(url_for('auth.forgot_password'))
        else:
            users=User.query.filter_by(email=email).first()
            if users:
                otp = random.randint(100000, 999999)
                otp_storage[email] = {'otp': otp, 'expires': datetime.now() + timedelta(minutes=5)}
                print(mail.password)
                print(mail.sender)
                # Function to Send OTP Email
                mssg = Message(subject='Password Reset OTP',  recipients=[email])
                mssg.body=f'Your OTP for password reset is: {otp}. It will expire in 5 minutes.'
                try:
                    mail.send(mssg)
                    flash('Your otp has been sent to your email.', 'success')
                    return redirect(url_for('auth.verify_otp', email=email))
                except Exception as e:
                    print(f"Error sending email: {e}")
                    flash('Failed to send email. Please try again later.', 'danger')
                    return redirect(url_for('auth.forgot_password'))
            else:
                flash('Invalid Email','danger')
                return redirect(url_for('auth.forgot_password'))
    else:
        return render_template('forgot_password.html')
@auth.route('/verifyotp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        if email in otp_storage and int(request.form['otp']) == otp_storage[email]['otp']:
            session['reset_email'] = email
            return redirect(url_for('auth.reset_password'))
        flash('Invalid OTP.', 'danger')

    return render_template('verifyotp.html', email=email)
# Auth verify
@auth.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
          # check the admin approve your account are not
            is_approve=User.query.filter_by(id=user.id).first()
            # first return the is_approve:
            if is_approve.status == 0:
                flash('Your Account is not approved by Admin','danger')
                return redirect(url_for('auth.login'))
            elif is_approve.status == 2:
                flash("Your Account is rejected by Admin",'danger')
                return redirect(url_for('auth.login'))
            else:
                if user.mfa==1:
                    session['mfa_user_id'] = user.id
                    if not user.mfa_setup_complete:
                        qr_code = generate_mfa_qr_code(email, user.mfa_secret)
                        return render_template('enable_mfa.html', qr_code=qr_code,email=email,mfa_setup_complete=user.mfa_setup_complete)
                    else:
                        return render_template('enable_mfa.html', email=user.email,mfa_setup_complete=user.mfa_setup_complete)
                session['user_id']=user.id
                user.status=3
                session['last_activity'] = datetime.now().isoformat()
                flash('Login successful!', 'success')
                return redirect(url_for('auth.dashboard'))

        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html', title='Login')
@auth.route('/verify_mfa',methods=['GET','POST'])
def verify_mfa():
    if 'mfa_user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.home'))
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        user_id = session['mfa_user_id']
        user = User.query.get(user_id)
        if user.mfa_secret:
            print(f"MFA Secret: {user.mfa_secret}")
            print(user_otp)
            totp = pyotp.TOTP(user.mfa_secret)
            if totp.verify(user_otp):
                if not user.mfa_setup_complete:
                    user.mfa_setup_complete = True
                    db.session.commit()
                session['user_id'] = user.id
                session.pop('mfa_user_id', None)
                session['last_activity'] = datetime.now().isoformat()
                flash('Succesfully Completed','success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid OTP.Please try again",'danger')
                return render_template('enable_mfa.html',title='Two-factor-authentication')
        else:
            flash('MFA is not enabled for this account.', 'warning')


    return render_template('enable_mfa.html',title='Two-factor-authentication')
@auth.route('/dash_reset_password', methods=['GET', 'POST'])
def dash_reset_password():

    if 'user_id' not in session:
        flash('Please log in to reset your password.', 'error')
        return redirect(url_for('auth.login'))

    # Fetch the user from the database
    user = User.query.get(session['user_id'])

    # Check if the user exists
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))

    # Check if the user has the required status (e.g., status 3)
    # if user.status != 3:  # Assuming 3 = "approved" or "allowed to reset"
    #     flash('You are not authorized to reset your password.', 'error')
    #     return redirect(url_for('auth.login'))  # Redirect to a relevant page

    # Handle password reset request
    if request.method == 'POST':
        password = request.form.get('password')
        if password:
            # Update password
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('auth.dash_reset_password'))  # PRG pattern
        else:
            flash('Password cannot be empty.', 'error')

    # Render the template for GET requests
    return render_template('dash_reset_password.html')
# Auth dashboard
# @auth.route('/dashboard')
# def dashboard():
#     if 'user_id' not in session:
#         flash('Please log in first.', 'warning')
#         return redirect(url_for('auth.home'))

#     # Fetch all projects from the database
#     projects = Project.query.all()

#     # Count projects by status for the chart
#     pending_count = 0
#     ongoing_count = 0
#     completed_count = 0

#     for project in projects:
#         if project.status.lower() == 'not started':
#             pending_count += 1
#         elif project.status.lower() == 'completed':
#             completed_count += 1
#         else:
#             ongoing_count += 1

#     return render_template("user_dashboard.html",
#                           title='dashboard',
#                           projects=projects,
#                           pending_count=pending_count,
#                           ongoing_count=ongoing_count,
#                           completed_count=completed_count)
# @auth.route('/dashboard')
# def dashboard():
#     if 'user_id' not in session:
#         flash('Please log in first.', 'warning')
#         return redirect(url_for('auth.home'))

#     # Fetch all projects from the database
#     projects = Project.query.all()

#     # Count projects by status for the chart
#     not_started_count = 0
#     ongoing_count = 0
#     completed_count = 0
#     delayed_count = 0 # ADD THIS

#     for project in projects:
#         if project.status.lower() == 'not started':
#             not_started_count += 1
#         elif project.status.lower() == 'completed':
#             completed_count += 1
#         elif project.status.lower() == 'ongoing': #ADD THIS
#             ongoing_count += 1
#         else:
#             delayed_count += 1 # ADD THIS
#     return render_template("user_dashboard.html",
#                           title='dashboard',
#                           projects=projects,
#                           not_started_count=not_started_count, #redefine these counts
#                           ongoing_count=ongoing_count,
#                           completed_count=completed_count,
#                           delayed_count = delayed_count) #ADDTHIS
@auth.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.home'))

    user_id = session['user_id']
    user = User.query.get(user_id)  # Assuming your User model has `id` attribute

    if user is None:
        flash('User not found.', 'error')
        return redirect(url_for('auth.home')) #or maybe logout or handle appropriately

    if user.role == 'Team member':  # or however you define 'team_member' in your User model
        projects = Project.query.all()

        # Count projects by status for the chart
        not_started_count = 0
        ongoing_count = 0
        completed_count = 0
        delayed_count = 0

        for project in projects:
            if project.status and project.status.lower() == 'not started': #added check for project.status
                not_started_count += 1
            elif project.status and project.status.lower() == 'completed': #added check for project.status
                completed_count += 1
            elif project.status and project.status.lower() == 'ongoing': #added check for project.status
                ongoing_count += 1
            elif project.status: #added check for project.status
                delayed_count += 1
            else:
                #Handle projects with no status or invalid status.  Log it or default to a count
                print(f"Project {project.id} has an invalid or missing status")
                delayed_count +=1  #Or perhaps do nothing, or log an error

        return render_template("memberdashboard.html", title='Team Member Dashboard',projects=projects,
                              not_started_count=not_started_count,
                              ongoing_count=ongoing_count,
                              completed_count=completed_count,
                              delayed_count=delayed_count)  # Pass any necessary data

    elif user.role in ['Product owner', 'Scrum master']:  # Check for multiple roles

        # Fetch all projects from the database
        projects = Project.query.all()

        # Count projects by status for the chart
        not_started_count = 0
        ongoing_count = 0
        completed_count = 0
        delayed_count = 0

        for project in projects:
            if project.status and project.status.lower() == 'not started': #added check for project.status
                not_started_count += 1
            elif project.status and project.status.lower() == 'completed': #added check for project.status
                completed_count += 1
            elif project.status and project.status.lower() == 'ongoing': #added check for project.status
                ongoing_count += 1
            elif project.status: #added check for project.status
                delayed_count += 1
            else:
                #Handle projects with no status or invalid status.  Log it or default to a count
                print(f"Project {project.id} has an invalid or missing status")
                delayed_count +=1  #Or perhaps do nothing, or log an error

        return render_template("user_dashboard.html",
                              title='dashboard',
                              projects=projects,
                              not_started_count=not_started_count,
                              ongoing_count=ongoing_count,
                              completed_count=completed_count,
                              delayed_count=delayed_count)

    return redirect(url_for('auth.home')) 
# Auth logout
@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    # Check if a user is in session (not admin)
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        if user:
            # Update the logout timestamp
            user.logout = datetime.now()
            user.status=4
            db.session.commit()

        # Clear the user session
        session.pop('user_id', None)
        flash('Logged out successfully!', 'success')
    else:
        # Handle admin logout (no timestamp update)
        session.pop('admin_id', None)
        flash('Admin logged out successfully!', 'success')
    return redirect(url_for('auth.home'))
# Main routes
@main.route('/')
def index():
    return render_template('index2.html')


@main.route('/add_project_page', methods=['GET', 'POST'])
def add_project_page():
    print("Add project page route was accessed")

    if request.method == 'POST':
        project_name = request.form['projectName']
        product_owner_id = request.form['ProductOwner']
        dev_team_ids = request.form.getlist('devTeam')
        status = request.form['status']
        start_date = request.form['startDate']
        end_date = request.form['endDate']
        revised_end_date = request.form['revisedEndDate']

        # Gather sprint details
        sprints_data = []
        sprint_numbers = request.form.getlist('sprintNumber[]')
        sprint_scrum_masters = request.form.getlist('sprintScrumMaster[]')
        sprint_start_dates = request.form.getlist('sprintStartDate[]')
        sprint_end_dates = request.form.getlist('sprintEndDate[]')
        sprint_status = request.form.getlist('sprintStatus[]')


        # Process each sprint
        for i in range(len(sprint_numbers)):
            sprint_data = {
                'sprintNumber': sprint_numbers[i],
                'scrumMaster': sprint_scrum_masters[i],
                'sprintStartDate': sprint_start_dates[i],
                'sprintEndDate': sprint_end_dates[i],
                'sprintStatus': sprint_status[i]
            }
            sprints_data.append(sprint_data)
        print('sprint status:',sprints_data)
        project_data = {
            'projectName': project_name,
            'projectDescription': request.form['projectDescription'],
            'ProductOwner': product_owner_id,
            'devTeam': dev_team_ids,
            'startDate': start_date,
            'endDate': end_date,
            'revisedEndDate': revised_end_date,
            'status': status,
            'sprints': sprints_data,
            'projectId': "PRJ-XXX", #Generate project id

        }

        print(f"Project Name: {project_name}")
        print(f"Product Owner ID: {product_owner_id}")
        print(f"Developer Team IDs: {dev_team_ids}")
        print(f"Status: {status}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        print(f"Revised End Date: {revised_end_date}")
        print(f"Sprints Data: {sprints_data}")

        # Fetch email addresses from the database
        try:
            # Function to fetch email for a user id
            def get_email(user_id):
                user = User.query.get(user_id)
                return user.email if user else None

            # Get email of product owner
            product_owner_email = get_email(product_owner_id)
            print("product_owner_email", product_owner_email)
            # Get email of scrum masters
            scrum_master_emails = [get_email(sprint['scrumMaster']) for sprint in sprints_data]
            print("scrum_master_emails", scrum_master_emails)
            # Get email of developers
            developer_emails = [get_email(dev_id) for dev_id in dev_team_ids]
            print("developer_emails", developer_emails)

            # Filter out any potential None values (users not found)
            recipients = [email for email in [product_owner_email] + scrum_master_emails + developer_emails if email]
            print("recepients", recipients)

            # Send the email notification with all of the data passed
            send_project_notification(project_data, recipients)

        except Exception as e:
            print(f"Error while fetching emails or sending email: {e}")
            # Handle error (e.g., show a message to the user)

        return redirect(url_for('main.project_list'))

    try:
        product_owners = User.query.filter_by(role='Product owner').all()
        developers = User.query.filter_by(role='Team member').all()
        scrum_masters = User.query.filter_by(role='Scrum master').all()
        print("Product Owners:", product_owners)
        print("Developers:", developers)
        print("Scrum Masters:", scrum_masters)

        scrum_masters_data = [{'id': sm.id, 'name': sm.name} for sm in scrum_masters]

        return render_template('auth/add_project.html',
                               product_owners=product_owners,
                               developers=developers,
                               scrum_masters=scrum_masters_data)
    except Exception as e:
        print(f"Error in add_project_page: {e}")
        return "An error occurred while rendering the page.", 500
def send_email_notification(data, recipients):
    subject = f"New Project Created: {data['projectName']}"
    body = f"""
    A new project has been created:
    - Project Name: {data['projectName']}
    - Description: {data['projectDescription']}
    - Product Owner: {data['ProductOwner']}
    - Scrum Masters: {[sprint['scrumMaster'] for sprint in data['sprints']]}
    - Development Team: {data['devTeam']}
    - Start Date: {data['startDate']}
    - End Date: {data['endDate']}
    - Revised End Date: {data.get('revisedEndDate', 'Not revised')}
    """

    if recipients:
        msg = Message(subject, recipients=recipients)
        msg.body = body
        try:
            mail.send(msg)
            print(f"Email sent successfully to: {', '.join(recipients)}")
        except Exception as e:
            print(f"Error sending email: {e}")
    else:
        print("No valid recipients found to send the email.")


@main.route('/add_project', methods=['POST'])
def add_project():
    try:
        data = request.get_json()

        # Create new project
        new_project = Project(

            project_id=data['projectId'],
            project_name=data['projectName'],
            project_description=data['projectDescription'],
            product_owner=data['ProductOwner'],
            development_team=data['devTeam'],
            start_date=datetime.strptime(data['startDate'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['endDate'], '%Y-%m-%d').date(),
            revised_end_date=datetime.strptime(data['revisedEndDate'], '%Y-%m-%d').date() if data['revisedEndDate'] else None,
            status=data['status']
        )

        db.session.add(new_project)
        db.session.commit()
        db.session.flush()  # Flush to get the new project's ID

        # Store sprints
        for sprint_data in data['sprints']:
            new_sprint = Sprint(
                project_id=new_project.project_id,  #Keep String here
                sprint_number=sprint_data['sprint_number'],
                scrum_master=sprint_data['scrum_master'],
                start_date=datetime.strptime(sprint_data['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(sprint_data['end_date'], '%Y-%m-%d').date(),
                velocity=0,
                status=sprint_data['status']
            )
            db.session.add(new_sprint)
        db.session.commit()
        # Store user stories
        for story_data in data['userStories']:
            sprint_id = story_data.get('sprint_id')
            new_story = UserStory(
                project_id=new_project.project_id,  # changed to id here so the key is good
                sprint_id=sprint_id,
                team=story_data['team'],
                description=story_data['description'],
                story_point=story_data['points'],  # Changed from points to story_point
                status=story_data['status']
            )
            print(f"Creating UserStory with project_id: {new_story.project_id} and sprint_id: {new_story.sprint_id}")
            db.session.add(new_story)

        db.session.commit()


        # Send email notification
        send_project_notification(data)

        return jsonify({'success': True, 'message': 'Project created successfully'})

    except Exception as e:
        db.session.rollback()
        print(f"Error creating project: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

# def send_project_notification(data):
#     try:
#         selected_members = data['devTeam']
#         product_owner = data['ProductOwner']

#         subject = f"New Project Created: {data['projectName']}"
#         body = f"""
#         A new project has been created:
#         - Project ID: {data['projectId']}
#         - Project Name: {data['projectName']}
#         - Description: {data['projectDescription']}
#         - Product Owner: {product_owner}
#         - Development Team: {', '.join(selected_members)}
#         - Start Date: {data['startDate']}
#         - End Date: {data['endDate']}
#         """

#         msg = Message(
#             subject=subject,
#             recipients=['teamofadm1n123@gmail.com'],  # Add your admin email
#             body=body
#         )
#         mail.send(msg)

#     except Exception as e:
#         print(f"Error sending email notification: {str(e)}")
@main.route('/dashboard')
def dashboard():
    # Get all projects with their sprints and stories
    projects = Project.query.all()
    project_data = []

    for project in projects:
        sprints = Sprint.query.filter_by(project_id=project.project_id).all()
        sprint_data = []

        for sprint in sprints:
            stories = UserStory.query.filter_by(sprint_id=sprint.id).all()
            sprint_data.append({
                'id': sprint.id,
                'sprint_number': sprint.sprint_number,
                'scrum_master': sprint.scrum_master,
                'start_date': sprint.start_date.strftime('%Y-%m-%d'),
                'end_date': sprint.end_date.strftime('%Y-%m-%d'),
                'status': sprint.status,
                'stories': [story.to_dict() for story in stories]
            })

        project_data.append({
            'id': project.project_id,
            'name': project.project_name,
            'status': project.status,
            'sprints': sprint_data
        })

    return render_template('dashboard.html', projects=project_data)



@main.route('/project/<project_id>/edit', methods=['GET', 'POST'])
def edit_project_page(project_id):
    project = Project.query.filter_by(project_id=project_id).first()
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        try:
            # Get data from form
            project.project_name = request.form.get('projectName')
            project.project_description = request.form.get('projectDescription')
            project.product_owner = request.form.get('ProductOwner')
            # Handle development team (assuming it's a list of user IDs)
            dev_team_ids = request.form.getlist('devTeam')
            project.development_team = dev_team_ids  # Store IDs as JSON
            project.start_date = datetime.strptime(request.form.get('startDate'), '%Y-%m-%d').date()
            project.end_date = datetime.strptime(request.form.get('endDate'), '%Y-%m-%d').date()
            revised_end_date_str = request.form.get('revisedEndDate')
            project.revised_end_date = datetime.strptime(revised_end_date_str, '%Y-%m-%d').date() if revised_end_date_str else None
            project.status = request.form.get('status')

            # Update sprints (assuming you have a way to identify and update them)
            # This is a simplified example; adapt it to your actual form structure
            sprint_numbers = request.form.getlist('sprintNumber')
            sprint_scrum_masters = request.form.getlist('sprintScrumMaster')
            sprint_start_dates = request.form.getlist('sprintStartDate')
            sprint_end_dates = request.form.getlist('sprintEndDate')
            status = request.form.getlist('sprintStatus')

            for i in range(len(sprint_numbers)):
                sprint_number = sprint_numbers[i]
                sprint = Sprint.query.filter_by(project_id=project_id, sprint_number=sprint_number).first()
                if sprint:
                    sprint.scrum_master = sprint_scrum_masters[i]
                    sprint.start_date = datetime.strptime(sprint_start_dates[i], '%Y-%m-%d').date()
                    sprint.end_date = datetime.strptime(sprint_end_dates[i], '%Y-%m-%d').date()

            # Update user stories
            story_ids = request.form.getlist('storyId')
            story_teams = request.form.getlist('userStoryTeam')
            story_descriptions = request.form.getlist('userStoryDescription')
            story_points = request.form.getlist('storyPoints')
            story_statuses = request.form.getlist('userStoryStatus')
            story_sprint_ids = request.form.getlist('userStorySprint')  # Get sprint IDs

            for i in range(len(story_ids)):
                story_id = story_ids[i]
                story = UserStory.query.get(story_id)
                if story:
                    story.team = story_teams[i]
                    story.description = story_descriptions[i]
                    story.story_point = int(story_points[i])
                    story.status = story_statuses[i]
                    story.sprint_id = story_sprint_ids[i]  # Assign sprint ID

            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('auth.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating project: {str(e)}', 'danger')
            try:
                product_owners = User.query.filter_by(role='Product owner').all()
                developers = User.query.filter_by(role='Team member').all()
                scrum_masters = User.query.filter_by(role='Scrum master').all()
                teams = [{'name': 'Team1'}, {'name': 'Team2'}, {'name': 'Team3'}, {'name': 'Team4'}]
                sprints = Sprint.query.filter_by(project_id=project_id).all()
                scrum_masters_data = [{'id': sm.id, 'name': sm.name} for sm in scrum_masters]
 # Fetch sprints for the project
                return render_template('auth/edit_project.html',
                                       project=project,
                                       product_owners=product_owners,
                                       developers=developers,
                                       scrum_masters=scrum_masters_data,
                                       teams=teams,
                                       sprints=sprints)
            except Exception as render_error:
                print(f"Error during rendering: {render_error}")
                return "An error occurred while rendering the page.", 500


    try:
        product_owners = User.query.filter_by(role='Product owner').all()
        developers = User.query.filter_by(role='Team member').all()

        scrum_masters = User.query.filter_by(role='Scrum master').all()
        print("Product Owners:", product_owners)
        print("Developers:", developers)
        print("Scrum Masters:", scrum_masters)
        scrum_masters_data = [{'id': sm.id, 'name': sm.name} for sm in scrum_masters]

        teams = [{'name': 'Team1'}, {'name': 'Team2'}, {'name': 'Team3'}, {'name': 'Team4'}]
        sprints = Sprint.query.filter_by(project_id=project_id).all()  # Fetch sprints for the project
        return render_template('auth/edit_project.html',
                               project=project,
                               product_owners=product_owners,
                               developers=developers,
                               scrum_masters=scrum_masters_data,
                               teams=teams,
                               sprints=sprints)
    except Exception as e:
        print(f"Error in edit_project_page: {e}")
        return "An error occurred while rendering the page.", 500


@main.route('/project/<string:project_id>/view')
def view_project(project_id):
    project = Project.query.filter_by(project_id=project_id).first()
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('auth.dashboard'))

    # Project stats
    user_stories = UserStory.query.filter_by(project_id=project_id).all()
    total_stories = len(user_stories)
    completed_stories = len([story for story in user_stories if story.status.lower() == 'completed'])
    completion_percentage = (completed_stories / total_stories * 100) if total_stories > 0 else 0
    total_points = sum([story.story_point for story in user_stories])

    project_stats = {
        'total_stories': total_stories,
        'completed_stories': completed_stories,
        'completion_percentage': completion_percentage,
        'total_points': total_points
    }

    # # Fetch user stories grouped by sprint
    # user_story_overview = []
    # sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number).all()

    # for sprint in sprints:
    #     # sprint_stories = UserStory.query.filter_by(sprint_id=sprint.sprint_number).all()
    #       # Filter user stories by both sprint_id and project_id
    #     sprint_stories = UserStory.query.filter_by(sprint_id=sprint.sprint_number, project_id=project_id).all()

    #     for index, story in enumerate(sprint_stories):
    #         user_story_overview.append({
    #             "s_no": len(user_story_overview) + 1,  # Auto-incrementing S.NO
    #             "description": story.description,
    #             "status": story.status.upper(),
    #             "assigned_team": story.team,
    #             "sprint": f"Sprint {sprint.sprint_number}",
    #             "story_points": story.story_point,  # Ensure story points are stored correctly
    #             "sprint_id": story.sprint_id
    #         })
    # print(user_story_overview)

    # Fetch user stories grouped by sprint
    user_story_overview = []

    # Get all user stories for the given project
    user_stories = UserStory.query.filter_by(project_id=project_id).order_by(UserStory.sprint_id).all()

    for index, story in enumerate(user_stories):
        user_story_overview.append({
            "s_no": len(user_story_overview) + 1,  # Auto-incrementing S.NO
            "description": story.description,
            "status": story.status,
            "assigned_team": story.team,
            "sprint": f"Sprint {story.sprint_id}",  # Using sprint_id directly from UserStory table
            "story_points": story.story_point,  # Ensure story points are stored correctly
            "sprint_id": story.sprint_id  # Directly from UserStory table
        })

    print(user_story_overview)

    # Sprint details with calculated completion rates and velocities
    sprint_details = []
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number).all()

    for sprint in sprints:
        # sprint_stories = UserStory.query.filter_by(sprint_id=sprint.sprint_number).all()
        sprint_stories = UserStory.query.filter_by(sprint_id=sprint.sprint_number, project_id=project_id).all()
        

        total_sprints = len(sprints)  # Total number of sprints
        completed_sprints = sum(1 for s in sprints if s.status.lower() == 'completed')  # Count completed sprints
        if sprint.status.lower() == 'completed':
            completion_rate = 100
        else:
        # Calculate completion rate (avoid division by zero)
            completion_rate = (completed_sprints / total_sprints * 100) if total_sprints > 0 else 0

        # Calculate sprint velocity (sum of story points from completed stories)
        # velocity = sum([story.story_point for story in sprint_stories ])
        # print('*******',velocity)
        velocity = sum([story.story_point for story in sprint_stories ])
        # velocity = sum(story.story_point for story in sprint_stories)
        print('*******',velocity)

         #  Update the Sprint table with the new velocity value
        sprint.velocity = velocity
        db.session.add(sprint)
        # Commit all sprint updates at once
        db.session.commit()

        sprint_details.append({
            'sprint_no': sprint.sprint_number,
            'start_date': sprint.start_date.strftime('%Y-%m-%d'),
            'end_date': sprint.end_date.strftime('%Y-%m-%d'),
            'velocity': sprint.velocity,
            'completion_rate': completion_rate,
            'status': sprint.status,
        })
    print("pink")
    for entry in sprint_details:
        print(entry)

    # db.session.commit()


    # Generate charts
    burndown_chart_url = generate_burndown_chart(project_id)
    burnup_chart_url = generate_burnup_chart(project_id)
    sprint_velocity_graph_url = generate_velocity_chart(project_id)





    # Team leaderboard
    from collections import defaultdict

# Dictionary to store team-wise progress
    team_progress = defaultdict(lambda: {"total_points": 0, "completed_points": 0, "total_stories": 0, "completed_stories": 0})

# Get all user stories for the given project_id
    project_stories = UserStory.query.filter_by(project_id=project_id).all()
    leaderboard = []
    for story in project_stories:
        team = story.team  # Get the team name
        team_progress[team]["total_points"] += story.story_point
        team_progress[team]["total_stories"] += 1

        if story.status.lower() == "completed":
            team_progress[team]["completed_points"] += story.story_point
            team_progress[team]["completed_stories"] += 1

    # Calculate progress percentage for each team

    for team, data in team_progress.items():
        progress = (data["completed_points"] / data["total_points"]) * 100 if data["total_points"] > 0 else 0
        leaderboard.append({
            "team": team,
            "total_points": data["total_points"],
            "completed_points": data["completed_points"],
            "total_stories": data["total_stories"],
            "completed_stories": data["completed_stories"],
            "progress": round(progress, 2)  # Percentage completed
        })

    # Sort leaderboard by highest completed story points
    leaderboard = sorted(leaderboard, key=lambda x: x["completed_points"], reverse=True)

    return render_template('auth/view_project.html',
                         project=project,
                         project_stats=project_stats,
                         sprint_details=sprint_details,
                         leaderboard=leaderboard,
                         user_story_overview=user_story_overview,
                         burnup_chart_url=burnup_chart_url,
                         burndown_chart_url=burndown_chart_url,
                         sprint_velocity_graph_url=sprint_velocity_graph_url)

@main.route('/project/<string:project_id>/summary')
def summary(project_id):
    project = Project.query.filter_by(project_id=project_id).first()
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('auth.dashboard'))

    # Get all user stories for this project
    user_stories = UserStory.query.filter_by(project_id=project_id).all()

    # Calculate project statistics
    total_stories = len(user_stories)
    completed_stories = len([story for story in user_stories if story.status.lower() == 'completed'])
    completion_percentage = (completed_stories / total_stories * 100) if total_stories > 0 else 0

    # Calculate story points
    total_points = sum(story.story_point for story in user_stories)
    completed_points = sum(story.story_point for story in user_stories if story.status.lower() == 'completed')

    # Get sprint statistics
    sprints = Sprint.query.filter_by(project_id=project_id).all()
    total_sprints = len(sprints)
    current_sprint = next((sprint.sprint_number for sprint in sprints
                         if sprint.status.lower() == 'ongoing'), 'None')

    # Calculate average velocity
    completed_sprints = [sprint for sprint in sprints if sprint.status.lower() == 'completed']
    average_velocity = sum(sprint.velocity for sprint in completed_sprints) / len(completed_sprints) if completed_sprints else 0

    project_stats = {
        'total_stories': total_stories,
        'completed_stories': completed_stories,
        'completion_percentage': completion_percentage,
        'total_points': total_points,
        'completed_points': completed_points
    }

    return render_template('auth/project_summary.html',
                         project=project,
                         project_stats=project_stats,
                         user_stories=user_stories,  # Pass user_stories to template
                         total_sprints=total_sprints,
                         current_sprint=current_sprint,
                         average_velocity=average_velocity)
@main.route('/test-email')
def test_email():
    try:
        msg = Message(
            subject="Test Email from Flask",
            recipients=['uppalapatipranavnag@gmail.com'],  # Replace with a valid email
            body="This is a test email from your Flask application."
        )
        mail.send(msg)
        return "Test email sent successfully!"
    except Exception as e:
        return f"Error sending test email: {str(e)}"

@main.route('/api/project/<project_id>/sprints/status', methods=['PUT'])
def update_sprints_status(project_id):
    try:
        data = request.get_json()
        new_status = data.get('status')

        # Update sprints status using SQLite
        update_query = text("""
            UPDATE sprint
            SET status = :new_status,
                last_updated = CURRENT_TIMESTAMP
            WHERE project_id = :project_id
        """)

        db.session.execute(update_query, {
            'new_status': new_status,
            'project_id': project_id
        })
        db.session.commit()

        return jsonify({'success': True, 'message': 'Sprint statuses updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/api/project/<project_id>/stories/status', methods=['PUT'])
def update_stories_status(project_id):
    try:
        data = request.get_json()
        new_status = data.get('status')

        # Update user stories status using SQLite
        update_query = text("""
            UPDATE user_story
            SET status = :new_status,
                last_updated = CURRENT_TIMESTAMP
            WHERE project_id = :project_id
        """)

        db.session.execute(update_query, {
            'new_status': new_status,
            'project_id': project_id
        })
        db.session.commit()

        return jsonify({'success': True, 'message': 'User story statuses updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
@main.route('/send-summary-mails', methods=['GET', 'POST'])
def send_summary():
    generate_and_send_summary_email()
    return "Summary report sent!"

@main.route('/send-deadline-reminders', methods=['GET', 'POST'])
def send_deadline_reminders_route():
    send_deadline_reminders()
    return "Deadline reminders sent!"
def generate_and_send_summary_email():
    projects = Project.query.all()
    for project in projects:
        # Fetch project statistics
        user_stories = UserStory.query.filter_by(project_id=project.project_id).all()
        total_stories = len(user_stories)
        completed_stories = len([story for story in user_stories if story.status and story.status.lower() == 'completed'])
        completion_percentage = (completed_stories / total_stories * 100) if total_stories > 0 else 0
        total_points = sum([story.story_point for story in user_stories])

        project_stats = {
            'total_stories': total_stories,
            'completed_stories': completed_stories,
            'completion_percentage': completion_percentage,
            'total_points': total_points
        }

        # Generate the HTML for the PDF using the existing template
        html = render_template('auth/project_summary.html',
                               project=project,
                               project_stats=project_stats,
                               is_pdf=True)

        pdf_filename = f'summary_report_{project.project_id}.pdf'

        config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")  # Update path

        # PDFKit options for a professional 1-page layout
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'encoding': 'UTF-8',
            'disable-smart-shrinking': '',
            'zoom': '1.0',  # Proper scaling
            'dpi': 300,
            'no-outline': None,
            'enable-local-file-access': '',  # Ensure local assets (CSS, images) load correctly
        }

        try:
            # Generate PDF from HTML
            pdfkit.from_string(html, pdf_filename, configuration=config, options=pdf_options)
            print(f"Generated PDF: {pdf_filename}")  # Debugging line
        except Exception as e:
            print(f"❌ Failed to generate PDF for project '{project.project_name}': {e}")
            continue  # Skip to the next project if PDF generation fails

        subject = f"Summary Report for {project.project_name} - {datetime.now().strftime('%Y-%m-%d')}"

        # Get the product owner's email based on their role
        product_owner = User.query.filter_by(role='Product owner').first()  # Fetch the first user with the role of Product owner
        product_owner_email = product_owner.email if product_owner else None

        # Prepare the list of emails for the development team
        development_team_names = project.development_team  # Assuming this is a list of names
        team_members = User.query.filter(User.name.in_(development_team_names)).all()  # Fetch team members by names

        # Fetch scrum masters
        scrum_masters = User.query.filter_by(role='Scrum master').all()  # Fetch all scrum masters

        # Prepare the list of emails
        recipients = [product_owner_email] + [member.email for member in team_members if member.email] + \
                     [master.email for master in scrum_masters if master.email]
        print(f"📧 Sending summary report to: {recipients}")

        # Notify all assigned team members, product owner, and scrum masters
        for recipient in recipients:
            if recipient:  # Ensure recipient is not None
                body = f"Dear Team,\n\nPlease find attached the summary report for the project '{project.project_name}'.\n\nBest regards,\nInfosys Project Management Team"

                msg = Message(subject, recipients=[recipient])
                msg.body = body

                try:
                    with open(pdf_filename, 'rb') as pdf_file:
                        msg.attach(pdf_filename, 'application/pdf', pdf_file.read())

                    mail.send(msg)
                    print(f"✅ Summary report sent to {recipient} for project '{project.project_name}'.")

                except Exception as e:
                    print(f"❌ Failed to send email to {recipient}: {e}")

        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
def send_deadline_reminders():
    today = date.today()
    upcoming_projects = Project.query.filter(
        (Project.end_date >= today) &
        (Project.end_date <= today + timedelta(days=3))
    ).all()

    print(f"Today's date: {today}")
    print(f"Upcoming projects: {upcoming_projects}")

    for project in upcoming_projects:
        subject = f"Deadline Reminder: {project.project_name}"

        # Fetch team members by names
        development_team_names = project.development_team
        team_members = User.query.filter(User.name.in_(development_team_names)).all()

        # Fetch the product owner's email based on their role
        product_owner = User.query.filter_by(role='Product owner').first()  # Fetch the first user with the role of Product owner
        product_owner_email = product_owner.email if product_owner else None

        # Fetch scrum masters
        scrum_masters = User.query.filter_by(role='Scrum master').all()  # Fetch all scrum masters

        # Prepare the list of emails
        recipients = [product_owner_email] + [member.email for member in team_members if member.email] + \
                     [master.email for master in scrum_masters if master.email]

        # Notify all team members, product owner, and scrum masters
        for recipient in recipients:
            if recipient:  # Ensure recipient is not None
                body = f"Dear {recipient}\n\nThis is a reminder that the project '{project.project_name}' is due on {project.end_date}.\n\nPlease ensure all tasks are completed before the deadline.\n\nBest regards,\nInfosys Project Management Team"
                msg = Message(subject, recipients=[recipient])
                msg.body = body
                try:
                    mail.send(msg)
                    print(f"✅Deadline reminder sent to {recipient} for project '{project.project_name}'.")
                except Exception as e:
                    print(f"❌Failed to send email to {recipient}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(generate_and_send_summary_email, 'cron', day_of_week='mon', hour=9, minute=0)  # Every Monday at 9 AM
scheduler.add_job(generate_and_send_summary_email, 'cron', day=1, hour=9, minute=0)  # First day of the month at 9 AM
scheduler.add_job(send_deadline_reminders, 'cron', hour=9,minute=0)  # Check daily for deadline reminders
scheduler.start()
print("Scheduler started for deadline reminders and summary reports.")
