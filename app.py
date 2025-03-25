import io
import base64
import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, jsonify, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import datetime
import numpy as np
from sqlalchemy import case
import random
from flask_mail import Mail,Message
from apscheduler.schedulers.background import BackgroundScheduler
import pdfkit
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///dashboard.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gaddamlikhitha.cse@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'pmaw irhx heal oaco'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'gaddamlikhitha.cse@gmail.com'  # Replace with your email
app.config['SERVER_NAME'] = 'yourdomain.com'
app.config['APPLICATION_ROOT'] = '/my-app'
app.config['PREFERRED_URL_SCHEME'] = 'http'

db = SQLAlchemy(app)
mail = Mail(app)

team_members = {
    "Pranav": "uppalapatipranavnag@gmail.com",
    "Meghana": "vemulameghana9@gmail.com",
    "Suresh": "sureshmenati0@gmail.com",
    "Sania": "saniascoops505@gmail.com",
    "Edward": "ayaan.dhx@gmail.com",
    "Haritha": "haritha.chakka04@gmail.com",
    "Riya": "riyaasthana25@gmail.com",
    "Sai Likitha": "gaddamlikhitha.cse@gmail.com",
    "Dhruv": "dhruvmittal4480@gmail.com",
    "Jasna": "jasnaivi@gmail.com",
    "Janardhan": "reddyjanardhan834@gmail.com",
    "Mahak": "mahakgianchandani124@gmail.com",
    "Yashwanthi": "yashwanthimarni77@gmail.com",
    "Vinitha": "vinitha.chirtha@gmail.com",
    "Arun": "ngarun2004@gmail.com",
}

# Team 3 Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100))
    project_manager = db.Column(db.String(100))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    revised_end_date = db.Column(db.String(20))
    status = db.Column(db.String(20))

class UserStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    sprint_id = db.Column(db.Integer)
    planned_sprint = db.Column(db.Integer)
    actual_sprint = db.Column(db.Integer)
    description = db.Column(db.String(255))
    story_point = db.Column(db.Integer)
    moscow = db.Column(db.String(20))
    dependency = db.Column(db.String(100))
    assignee = db.Column(db.String(100))
    status = db.Column(db.String(20))

class ScrumMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    name = db.Column(db.String(100))
    contact_number = db.Column(db.String(15))

class SprintCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    scrum_master_id = db.Column(db.Integer, db.ForeignKey('scrum_master.id'))
    sprint_no = db.Column(db.Integer)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    velocity = db.Column(db.Integer)

# Team Leaderboard Function
def generate_team_leaderboard(project_id):
    user_stories = UserStory.query.filter_by(project_id=project_id).all()
    leaderboard = {}
    for story in user_stories:
        if story.assignee not in leaderboard:
            leaderboard[story.assignee] = 0
        if story.status == "Completed":
            leaderboard[story.assignee] += story.story_point
    return sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

# Performance Analytics Functions
def calculate_project_completion(project_id):
    try:
        total_stories = UserStory.query.filter_by(project_id=project_id).count()
        if total_stories == 0:
            return 0
        completed_stories = UserStory.query.filter_by(
            project_id=project_id,
            status="Completed"
        ).count()
        return round((completed_stories / total_stories) * 100, 2)
    except Exception:
        return 0

def calculate_team_velocity(project_id):
    sprints = SprintCalendar.query.filter_by(project_id=project_id).all()
    velocities = []
    for sprint in sprints:
        completed_points = db.session.query(db.func.sum(UserStory.story_point)).filter(
            UserStory.project_id == project_id,
            UserStory.sprint_id == sprint.sprint_no,
            UserStory.status == "Completed"
        ).scalar() or 0
        velocities.append({
            'sprint_no': sprint.sprint_no,
            'velocity': completed_points
        })
    return velocities

def generate_burnup_chart(project_id):
    # Get all sprints for the project ordered by sprint number
    sprints = SprintCalendar.query.filter_by(project_id=project_id).order_by(SprintCalendar.sprint_no).all()

    # Initialize data arrays
    sprint_labels = []
    total_points = []
    completed_points = []
    cumulative_total = 0
    cumulative_completed = 0

    for sprint in sprints:
        sprint_labels.append(f"Sprint {sprint.sprint_no}")

        # Get all stories for this sprint
        stories = UserStory.query.filter_by(
            project_id=project_id,
            sprint_id=sprint.sprint_no
        ).all()

        # Calculate total points for this sprint
        sprint_total = sum(story.story_point for story in stories)
        cumulative_total += sprint_total
        total_points.append(cumulative_total)

        # Calculate completed points for this sprint
        sprint_completed = sum(story.story_point for story in stories if story.status == "Completed")
        cumulative_completed += sprint_completed
        completed_points.append(cumulative_completed)

    # Create the burnup chart with custom styling
    plt.figure(figsize=(10, 6))
    plt.style.use('default')  # Use default style instead of seaborn

    # Set background color
    plt.gca().set_facecolor('#f8f9fa')
    plt.gcf().set_facecolor('#ffffff')

    # Plot with custom colors and styles
    plt.plot(sprint_labels, total_points, marker='o', color='#FF69B4', linewidth=2,
             label='Total Story Points', markersize=8)
    plt.plot(sprint_labels, completed_points, marker='s', color='#4CAF50', linewidth=2,
             label='Completed Points', markersize=8)

    # Customize the chart
    plt.title('Sprint Burnup Chart', fontsize=14, pad=20, color='#333333')
    plt.xlabel('Sprints', fontsize=12, color='#666666')
    plt.ylabel('Story Points', fontsize=12, color='#666666')
    plt.grid(True, linestyle='--', alpha=0.3, color='#cccccc')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.xticks(rotation=45, color='#666666')
    plt.yticks(color='#666666')

    # Add value labels on points
    for i, (total, completed) in enumerate(zip(total_points, completed_points)):
        plt.text(i, total + 1, str(total), ha='center', va='bottom', color='#FF69B4')
        plt.text(i, completed - 1, str(completed), ha='center', va='top', color='#4CAF50')

    # Adjust layout
    plt.tight_layout()

    # Convert plot to base64 image
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, facecolor='#ffffff')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def generate_burndown_chart(project_id):
    # Get all sprints for the project ordered by sprint number
    sprints = SprintCalendar.query.filter_by(project_id=project_id).order_by(SprintCalendar.sprint_no).all()

    # Get total story points for the project
    total_points = db.session.query(db.func.sum(UserStory.story_point))\
        .filter_by(project_id=project_id).scalar() or 0

    # Initialize data arrays
    sprint_labels = []
    remaining_points = []
    ideal_burndown = []
    actual_completed = []

    # Calculate points per sprint for ideal burndown
    num_sprints = len(sprints)
    points_per_sprint = total_points / num_sprints if num_sprints > 0 else 0

    current_points = total_points
    for i, sprint in enumerate(sprints):
        sprint_labels.append(f"Sprint {sprint.sprint_no}")

        # Calculate completed points up to this sprint
        completed_points = db.session.query(db.func.sum(UserStory.story_point))\
            .filter(
                UserStory.project_id == project_id,
                UserStory.sprint_id <= sprint.sprint_no,
                UserStory.status == "Completed"
            ).scalar() or 0

        # Update remaining points
        remaining = total_points - completed_points
        remaining_points.append(remaining)
        actual_completed.append(completed_points)

        # Calculate ideal burndown
        ideal_points = total_points - (points_per_sprint * (i + 1))
        ideal_burndown.append(max(0, ideal_points))

    # Create the burndown chart with custom styling
    plt.figure(figsize=(10, 6))
    plt.style.use('default')  # Use default style instead of seaborn

    # Set background color
    plt.gca().set_facecolor('#f8f9fa')
    plt.gcf().set_facecolor('#ffffff')

    # Plot with custom colors and styles
    plt.plot(sprint_labels, remaining_points, marker='o', color='#FF69B4', linewidth=2,
             label='Actual Remaining', markersize=8)
    plt.plot(sprint_labels, ideal_burndown, '--', color='#666666', linewidth=2,
             label='Ideal Burndown', alpha=0.7)

    # Fill the area between actual and ideal
    plt.fill_between(sprint_labels, remaining_points, ideal_burndown,
                     alpha=0.1, color='#FF69B4')

    # Customize the chart
    plt.title('Sprint Burndown Chart', fontsize=14, pad=20, color='#333333')
    plt.xlabel('Sprints', fontsize=12, color='#666666')
    plt.ylabel('Remaining Points', fontsize=12, color='#666666')
    plt.grid(True, linestyle='--', alpha=0.3, color='#cccccc')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.xticks(rotation=45, color='#666666')
    plt.yticks(color='#666666')

    # Add value labels on points
    for i, remaining in enumerate(remaining_points):
        plt.text(i, remaining + 1, str(remaining), ha='center', va='bottom', color='#FF69B4')

    # Adjust layout
    plt.tight_layout()

    # Convert plot to base64 image
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, facecolor='#ffffff')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def generate_velocity_chart(project_id):
    # Get all sprints for the project ordered by sprint number
    sprints = SprintCalendar.query.filter_by(project_id=project_id).order_by(SprintCalendar.sprint_no).all()

    # Initialize data arrays
    sprint_labels = []
    velocities = []

    for sprint in sprints:
        sprint_labels.append(f"Sprint {sprint.sprint_no}")

        # Calculate actual velocity (completed story points) for this sprint
        completed_points = db.session.query(db.func.sum(UserStory.story_point))\
            .filter_by(
                project_id=project_id,
                sprint_id=sprint.sprint_no,
                status="Completed"
            ).scalar() or 0

        velocities.append(completed_points)

    # Calculate average velocity
    avg_velocity = sum(velocities) / len(velocities) if velocities else 0

    # Create the velocity chart with custom styling
    plt.figure(figsize=(10, 6))
    plt.style.use('default')  # Use default style instead of seaborn

    # Set background color
    plt.gca().set_facecolor('#f8f9fa')
    plt.gcf().set_facecolor('#ffffff')

    # Plot bars with custom colors
    bars = plt.bar(sprint_labels, velocities, color='#FF69B4', alpha=0.7)
    plt.axhline(y=avg_velocity, color='#666666', linestyle='--',
                label=f'Avg: {avg_velocity:.1f}', linewidth=2)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', color='#333333')

    # Customize the chart
    plt.title('Sprint Velocity Chart', fontsize=14, pad=20, color='#333333')
    plt.xlabel('Sprints', fontsize=12, color='#666666')
    plt.ylabel('Completed Story Points', fontsize=12, color='#666666')
    plt.grid(True, axis='y', linestyle='--', alpha=0.3, color='#cccccc')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.xticks(rotation=45, color='#666666')
    plt.yticks(color='#666666')

    # Adjust layout
    plt.tight_layout()

    # Convert plot to base64 image
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, facecolor='#ffffff')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def generate_and_send_summary_email():
    with app.app_context():
        projects = Project.query.all()
        for project in projects:
            # Fetch project statistics
            total_stories = UserStory.query.filter_by(project_id=project.id).count()
            completed_stories = UserStory.query.filter_by(project_id=project.id, status="Completed").count()
            total_projects = Project.query.count()
            completed_projects = Project.query.filter_by(status="Completed").count()
            ongoing_projects = Project.query.filter_by(status="Ongoing").count()
            total_sprints = SprintCalendar.query.filter_by(project_id=project.id).count()
            completed_sprints = SprintCalendar.query.filter_by(project_id=project.id, velocity=0).count()
            pending_sprints = total_sprints - completed_sprints
            total_user_stories = UserStory.query.filter_by(project_id=project.id).count()
            completed_user_stories = UserStory.query.filter_by(project_id=project.id, status="Completed").count()
            pending_user_stories = total_user_stories - completed_user_stories
            total_tasks = sum([us.story_point for us in UserStory.query.filter_by(project_id=project.id).all()])
            completed_tasks = sum([us.story_point for us in UserStory.query.filter_by(project_id=project.id, status="Completed").all()])
            pending_tasks = total_tasks - completed_tasks

            # Generate the HTML for the PDF using the existing template
            html = render_template('summary.html',
                                   project=project,
                                   total_stories=total_stories,
                                   completed_stories=completed_stories,
                                   total_projects=total_projects,
                                   completed_projects=completed_projects,
                                   ongoing_projects=ongoing_projects,
                                   total_sprints=total_sprints,
                                   completed_sprints=completed_sprints,
                                   pending_sprints=pending_sprints,
                                   total_user_stories=total_user_stories,
                                   completed_user_stories=completed_user_stories,
                                   pending_user_stories=pending_user_stories,
                                   total_tasks=total_tasks,
                                   completed_tasks=completed_tasks,
                                   pending_tasks=pending_tasks)

            # Unique filename for each project
            pdf_filename = f'summary_report_{project.id}.pdf'

            # Configure pdfkit to use the path to wkhtmltopdf
            config = pdfkit.configuration(wkhtmltopdf=r"D:\wkhtmltopdf\bin\wkhtmltopdf.exe")  # Update path

            # PDFKit options for a professional 1-page layout
            pdf_options = {
                'page-size': 'A4',
                'margin-top': '8mm',
                'margin-right': '8mm',
                'margin-bottom': '8mm',
                'margin-left': '8mm',
                'encoding': 'UTF-8',
                'disable-smart-shrinking': '',
                'zoom': '0.8',  # Shrink slightly to fit on one page
                'dpi': 300,
                'custom-header': [
                     ('Accept-Encoding', 'gzip')
                ],
            }

            try:
                pdfkit.from_string(html, pdf_filename, configuration=config, options=pdf_options)
                print(f"Generated PDF: {pdf_filename}")  # Debugging line
            except Exception as e:
                print(f"❌ Failed to generate PDF for project '{project.project_name}': {e}")
                continue  # Skip to the next project if PDF generation fails

            subject = f"Summary Report for {project.project_name} - {datetime.datetime.now().strftime('%Y-%m-%d')}"

            # Get the team members assigned to the project (assuming a dictionary of emails)
            assigned_team_members = [(member_name, member_email) for member_name, member_email in team_members.items()]
            print(f"📧 Sending summary report to: {assigned_team_members}")

            # Notify all assigned team members
            for member_name, member_email in assigned_team_members:
                body = f"Dear {member_name},\n\nPlease find attached the summary report for the project '{project.project_name}'.\n\nBest regards,\nInfosys Project Management Team"

                msg = Message(subject, recipients=[member_email])
                msg.body = body

                try:
                    with app.open_resource(pdf_filename) as pdf_file:
                        msg.attach(pdf_filename, 'application/pdf', pdf_file.read())

                    mail.send(msg)
                    print(f"✅ Summary report sent to {member_email} for project '{project.project_name}'.")

                except Exception as e:
                    print(f"❌ Failed to send email to {member_email}: {e}")

            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)
                print(f"🗑️ Deleted PDF: {pdf_filename}")

def send_deadline_reminders():
    today = datetime.date.today()
    reminder_days = 3  # Number of days before the deadline to send reminders
    upcoming_projects = Project.query.filter(
        (Project.end_date >= today) &
        (Project.end_date <= today + datetime.timedelta(days=reminder_days))
    ).all()

    print(f"Today's date: {today}")
    print(f"Upcoming projects: {upcoming_projects}")  # Debugging line

    for project in upcoming_projects:
        subject = f"Deadline Reminder: {project.project_name}"

        # Notify all team members
        for member_name, member_email in team_members.items():
            body = f"Dear {member_name},\n\nThis is a reminder that the project '{project.project_name}' is due on {project.end_date}.\n\nPlease ensure all tasks are completed before the deadline.\n\nBest regards,\nInfosys Project Management Team"
            msg = Message(subject, recipients=[member_email])
            msg.body = body
            try:
                mail.send(msg)
                print(f"Deadline reminder sent to {member_email} for project '{project.project_name}'.")
            except Exception as e:
                print(f"Failed to send email to {member_email}: {e}")

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(generate_and_send_summary_email, 'cron', day_of_week='mon', hour=9, minute=0)  # Every Monday at 9 AM
scheduler.add_job(generate_and_send_summary_email, 'cron', day=1, hour=8, minute=0)  # First day of the month at 8 AM
scheduler.add_job(send_deadline_reminders, 'cron', hour=9,minute=30)  # Check daily for deadline reminders
scheduler.start()
print("Scheduler started for deadline reminders and summary reports.")

# Routes
@app.route('/')
def index():
    # Check if database is empty
    if Project.query.count() == 0:
        return render_template('index.html',
                            project_counts={"total": 0, "active": 0, "on_hold": 0, "ongoing": 0},
                            projects=[],
                            message="No projects found. Please initialize the database.")

    # Fetch project counts
    project_counts = {
        "total": Project.query.count(),
        "active": Project.query.filter_by(status='Active').count(),
        "on_hold": Project.query.filter_by(status='On Hold').count(),
        "ongoing": Project.query.filter_by(status='Ongoing').count()
    }

    # Fetch all projects with completion percentage
    projects = []
    for project in Project.query.all():
        total_stories = UserStory.query.filter_by(project_id=project.id).count()
        completed_stories = UserStory.query.filter_by(project_id=project.id, status="Completed").count()
        completion_percentage = (completed_stories / total_stories * 100) if total_stories > 0 else 0

        projects.append({
            "id": project.id,
            "project_name": project.project_name,
            "project_manager": project.project_manager,
            "status": project.status,
            "completion_percentage": completion_percentage
        })

    # Fetch current sprints with project names
    sprints = []
    for sprint in SprintCalendar.query.all():
        project = Project.query.get(sprint.project_id)
        sprints.append({
            "project_name": project.project_name if project else "Unknown",
            "sprint_no": sprint.sprint_no,
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "velocity": sprint.velocity
        })

    # Calculate team performance
    team_performance = []
    team_members = db.session.query(UserStory.assignee).distinct().all()

    for member in team_members:
        if not member.assignee:
            continue

        assigned_stories = UserStory.query.filter_by(assignee=member.assignee).count()
        completed_stories = UserStory.query.filter_by(assignee=member.assignee, status="Completed").count()
        story_points = db.session.query(db.func.sum(UserStory.story_point)).filter(
            UserStory.assignee == member.assignee
        ).scalar() or 0
        completion_rate = (completed_stories / assigned_stories * 100) if assigned_stories > 0 else 0

        team_performance.append({
            "name": member.assignee,
            "assigned_stories": assigned_stories,
            "completed_stories": completed_stories,
            "story_points": story_points,
            "completion_rate": completion_rate
        })

    # Sort team performance by completion rate
    team_performance.sort(key=lambda x: x['completion_rate'], reverse=True)

    return render_template('dashboard.html',
                         project_counts=project_counts,
                         projects=projects,
                         sprints=sprints,
                         team_performance=team_performance,
                         today_date=datetime.datetime.now().strftime("%Y-%m-%d"))



@app.route('/projects')
def get_projects():
    try:
        projects = Project.query.all()
        return jsonify([{
            "id": p.id,
            "project_name": p.project_name,
            "project_manager": p.project_manager,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "revised_end_date": p.revised_end_date,
            "status": p.status,
            "completion_percentage": calculate_project_completion(p.id)
        } for p in projects])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/project_counts')
def project_counts():
    try:
        total_projects = Project.query.count()
        active_projects = Project.query.filter_by(status='Active').count()
        on_hold_projects = Project.query.filter_by(status='On Hold').count()
        ongoing_projects = Project.query.filter_by(status='Ongoing').count()

        return jsonify({
            "total": total_projects,
            "active": active_projects,
            "on_hold": on_hold_projects,
            "ongoing": ongoing_projects,
            "completion_stats": {
                "completed": Project.query.filter_by(status='Completed').count(),
                "total_stories": UserStory.query.count(),
                "completed_stories": UserStory.query.filter_by(status='Completed').count()
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sprint_details')
def get_sprint_details():
    try:
        sprints = SprintCalendar.query.all()
        sprint_data = []
        for sprint in sprints:
            project = Project.query.get(sprint.project_id)
            if project:
                completed_stories = UserStory.query.filter_by(
                    project_id=sprint.project_id,
                    sprint_id=sprint.sprint_no,
                    status='Completed'
                ).count()
                total_stories = UserStory.query.filter_by(
                    project_id=sprint.project_id,
                    sprint_id=sprint.sprint_no
                ).count()

                sprint_data.append({
                    "sprint_no": sprint.sprint_no,
                    "project_name": project.project_name,
                    "start_date": sprint.start_date,
                    "end_date": sprint.end_date,
                    "velocity": sprint.velocity,
                    "completion_rate": (completed_stories / total_stories * 100) if total_stories > 0 else 0
                })
        return jsonify(sprint_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/project/<int:project_id>')
def project_details(project_id):
    try:
        # Get project details with error handling
        project = Project.query.get_or_404(project_id)
        if project is None:
            abort(404)  # Explicitly abort with 404 if project not found

        # Get sprint details with proper ordering
        sprint_details = SprintCalendar.query.filter_by(project_id=project_id)\
            .order_by(SprintCalendar.sprint_no).all()

        # Get real-time sprint statistics
        sprint_stats = []
        for sprint in sprint_details:
            stories = UserStory.query.filter_by(
                project_id=project_id,
                sprint_id=sprint.sprint_no
            ).all()

            total_points = sum(story.story_point for story in stories)
            completed_points = sum(story.story_point for story in stories if story.status == "Completed")

            sprint_stats.append({
                'sprint_no': sprint.sprint_no,
                'start_date': sprint.start_date,
                'end_date': sprint.end_date,
                'velocity': completed_points,
                'total_points': total_points,
                'completion_rate': (completed_points / total_points * 100) if total_points > 0 else 0
            })

        # Get team leaderboard with detailed statistics
        leaderboard = []
        team_members = db.session.query(UserStory.assignee)\
            .filter_by(project_id=project_id)\
            .distinct().all()

        for member in team_members:
            if not member.assignee:
                continue

            member_stories = UserStory.query.filter_by(
                project_id=project_id,
                assignee=member.assignee
            ).all()

            total_points = sum(story.story_point for story in member_stories)
            completed_points = sum(story.story_point for story in member_stories if story.status == "Completed")

            leaderboard.append({
                'name': member.assignee,
                'points': completed_points,
                'total_stories': len(member_stories),
                'completed_stories': len([s for s in member_stories if s.status == "Completed"]),
                'completion_rate': (completed_points / total_points * 100) if total_points > 0 else 0
            })

        # Sort leaderboard by points
        leaderboard.sort(key=lambda x: x['points'], reverse=True)

        # Generate project analytics charts with real-time data
        burnup_chart_url = generate_burnup_chart(project_id)
        burndown_chart_url = generate_burndown_chart(project_id)
        sprint_velocity_graph_url = generate_velocity_chart(project_id)

        # Calculate detailed project statistics
        all_stories = UserStory.query.filter_by(project_id=project_id).all()
        completed_stories = [s for s in all_stories if s.status == "Completed"]
        in_progress_stories = [s for s in all_stories if s.status == "In Progress"]
        not_started_stories = [s for s in all_stories if s.status == "Not Started"]

        total_points = sum(story.story_point for story in all_stories)
        completed_points = sum(story.story_point for story in completed_stories)

        project_stats = {
            'total_stories': len(all_stories),
            'completed_stories': len(completed_stories),
            'in_progress_stories': len(in_progress_stories),
            'not_started_stories': len(not_started_stories),
            'completion_percentage': (len(completed_stories) / len(all_stories) * 100) if all_stories else 0,
            'total_points': total_points,
            'completed_points': completed_points,
            'points_percentage': (completed_points / total_points * 100) if total_points > 0 else 0,
            'average_story_points': total_points / len(all_stories) if all_stories else 0
        }

        # Get current sprint information
        current_sprint = SprintCalendar.query.filter_by(project_id=project_id)\
            .order_by(SprintCalendar.sprint_no.desc()).first()

        if current_sprint:
            current_sprint_stories = UserStory.query.filter_by(
                project_id=project_id,
                sprint_id=current_sprint.sprint_no
            ).all()

            project_stats.update({
                'current_sprint': current_sprint.sprint_no,
                'current_sprint_total': len(current_sprint_stories),
                'current_sprint_completed': len([s for s in current_sprint_stories if s.status == "Completed"])
            })

        return render_template('project_details.html',
                            project=project,
                            sprint_details=sprint_stats,
                            leaderboard=leaderboard,
                            burnup_chart_url=burnup_chart_url,
                            burndown_chart_url=burndown_chart_url,
                            sprint_velocity_graph_url=sprint_velocity_graph_url,
                            project_stats=project_stats,
                            current_sprint=current_sprint)

    except Exception as e:
        print(f"Error in project_details: {str(e)}")
        db.session.rollback()
        abort(500)

@app.route('/init_db')
def init_db():
    try:
        with app.app_context():
            # Drop all tables to start fresh
            db.drop_all()
            # Create all tables
            db.create_all()
            # Initialize sample data
            init_sample_data()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error initializing database: {str(e)}", 500

def init_sample_data():
    # Only add sample data if the database is empty
    if Project.query.count() == 0:
        # Create sample projects
        projects = [
            Project(
                project_name="E-Commerce Platform",
                project_manager="John Smith",
                start_date="2024-01-01",
                end_date="2024-06-30",
                status="Active"
            ),
            Project(
                project_name="Mobile Banking App",
                project_manager="Sarah Johnson",
                start_date="2024-02-15",
                end_date="2024-08-15",
                status="Ongoing"
            ),
            Project(
                project_name="Healthcare Portal",
                project_manager="Mike Brown",
                start_date="2024-03-01",
                end_date="2024-09-30",
                status="On Hold"
            )
        ]
        for project in projects:
            db.session.add(project)
        db.session.commit()

        # Create sample scrum masters with real email addresses
        scrum_masters = [
            ScrumMaster(
                name="Alex Turner",
                email="gaddamlikhitha.cse@gmail.com",  # Updated to use a real email
                contact_number="123-456-7890"
            ),
            ScrumMaster(
                name="Emily Davis",
                email="uppalapatipranavnag@gmail.com",  # Updated to use a real email
                contact_number="098-765-4321"
            )
        ]
        for sm in scrum_masters:
            db.session.add(sm)
        db.session.commit()

        # Create sample sprint calendars
        for project in Project.query.all():
            for i in range(1, 5):  # 4 sprints per project
                sprint = SprintCalendar(
                    project_id=project.id,
                    scrum_master_id=scrum_masters[0].id if i % 2 == 0 else scrum_masters[1].id,
                    sprint_no=i,
                    start_date=f"2024-{(i*2)-1:02d}-01",
                    end_date=f"2024-{i*2:02d}-01",
                    velocity=random.randint(15, 30)
                )
                db.session.add(sprint)
        db.session.commit()

        # Create sample user stories
        team_members = ["Alice", "Bob", "Charlie", "Diana", "Edward"]
        story_statuses = ["Not Started", "In Progress", "Completed"]
        moscow_priorities = ["Must Have", "Should Have", "Could Have"]

        for project in Project.query.all():
            for sprint_no in range(1, 5):
                for _ in range(5):  # 5 stories per sprint
                    story = UserStory(
                        project_id=project.id,
                        sprint_id=sprint_no,
                        planned_sprint=sprint_no,
                        actual_sprint=sprint_no,
                        description=f"User Story for Sprint {sprint_no}",
                        story_point=random.randint(1, 8),
                        moscow=random.choice(moscow_priorities),
                        assignee=random.choice(team_members),
                        status=random.choice(story_statuses)
                    )
                    db.session.add(story)
        db.session.commit()

@app.route('/summary/<int:project_id>')
def summary(project_id):
    try:
        # Get project details with error handling
        project = Project.query.get_or_404(project_id)

        # Get associated scrum master info
        sprint_calendar = SprintCalendar.query.filter_by(project_id=project_id).first()
        scrum_master = None
        if sprint_calendar and sprint_calendar.scrum_master_id:
            scrum_master = ScrumMaster.query.get(sprint_calendar.scrum_master_id)
            scrum_master = {
                'name': scrum_master.name,
                'email': scrum_master.email,
                'contact_number': scrum_master.contact_number
            }
        else:
            scrum_master = {
                'name': 'Not Assigned',
                'email': 'N/A',
                'contact_number': 'N/A'
            }

        # Calculate statistics
        stories = UserStory.query.filter_by(project_id=project_id).all()
        total_stories = len(stories)
        completed_stories = len([s for s in stories if s.status == "Completed"])

        # Calculate points
        total_points = sum(story.story_point for story in stories)
        completed_points = sum(story.story_point for story in stories if story.status == "Completed")
        remaining_points = total_points - completed_points

        # Calculate sprint metrics
        sprints = SprintCalendar.query.filter_by(project_id=project_id).all()
        total_sprints = len(sprints)
        current_sprint = max([s.sprint_no for s in sprints]) if sprints else 0
        average_velocity = sum(s.velocity for s in sprints) / len(sprints) if sprints else 0

        # Get team members
        team_members = set(story.assignee for story in stories if story.assignee)

        # Get current timestamp
        last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return render_template('summary.html',
                            project=project,
                            scrum_master=scrum_master,
                            total_stories=total_stories,
                            completed_stories=completed_stories,
                            total_points=total_points,
                            completed_points=completed_points,
                            remaining_points=remaining_points,
                            total_sprints=total_sprints,
                            current_sprint=current_sprint,
                            average_velocity=average_velocity,
                            team_members=team_members,
                            last_updated=last_updated)

    except Exception as e:
        print(f"Error in summary route: {str(e)}")
        db.session.rollback()
        abort(500)

@app.route('/send-summary-mails', methods=['GET','POST'])
def send_summary():
    generate_and_send_summary_email()
    return "Summary report sent!"

@app.route('/send-deadline-reminders', methods=['GET','POST'])
def send_deadline_reminders_route():
    send_deadline_reminders()
    return  "Deadline reminders sent!"
# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error_code=500, message="Internal server error"), 500


if __name__ == '__main__':
    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
