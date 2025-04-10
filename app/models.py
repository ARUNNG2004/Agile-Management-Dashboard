# from . import db  # Import the shared db instance
# from datetime import datetime
# from sqlalchemy import DateTime
# class Project(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     project_id = db.Column(db.String(50), unique=True, nullable=False)
#     project_name = db.Column(db.String(100), nullable=False)
#     project_description = db.Column(db.Text, nullable=False)
#     product_owner = db.Column(db.String(50), nullable=False)
#     development_team = db.Column(db.JSON, nullable=False)
#     start_date = db.Column(db.Date, nullable=False)
#     end_date = db.Column(db.Date, nullable=False)
#     revised_end_date = db.Column(db.Date, nullable=True)
#     # Remove the sprints JSON column since we're using the Sprint model relationship
#     status = db.Column(db.String(20), nullable=False, default='Not Started')

#     # Add relationship to sprints
#     sprints = db.relationship('Sprint', backref='project', lazy=True)

#     def to_dict(self):
#         return {
#             'project_id': self.project_id,
#             'project_name': self.project_name,
#             'project_description': self.project_description,
#             'product_owner': self.product_owner,
#             'development_team': self.development_team,
#             'start_date': self.start_date.strftime('%Y-%m-%d'),
#             'end_date': self.end_date.strftime('%Y-%m-%d'),
#             'revised_end_date': self.revised_end_date.strftime('%Y-%m-%d') if self.revised_end_date else None,
#             'status': self.status,
#             'sprints': self.sprints
#         }

#     def __repr__(self):
#         """Representation of the Project object."""
#         return f'<Project {self.project_id}: {self.project_name}>'


# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(150), nullable=False)
#     dob = db.Column(db.Date, nullable=False)
#     gender=db.Column(db.String(10),nullable=False)
#     timestamp=db.Column(DateTime,default=datetime.now)
#     logout=db.Column(DateTime,nullable=True)
#     email = db.Column(db.String(150), unique=True, nullable=False)
#     phone = db.Column(db.String(15), nullable=False)
#     password = db.Column(db.String(200), nullable=False)
#     role=db.Column(db.String(20),nullable=False)
#     status=db.Column(db.Integer,default=0, nullable=False)
#     address=db.Column(db.String(50),nullable=False)
#     mfa_secret=db.Column(db.String(16),nullable=True)
#     mfa=db.Column(db.Integer,default=0,nullable=False)
#     mfa_setup_complete = db.Column(db.Boolean, default=False)
#     def __repr__(self):
#         return f'User("{self.id}","{self.fname}","{self.lname}","{self.email}","{self.edu}","{self.username}","{self.status}","{self.address}")'


# class Admin(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(150), unique=True, nullable=False)
#     password = db.Column(db.String(255), nullable=False)

#     def __repr__(self):
#         """Representation of the Admin object."""
#         return f'<Admin {self.id}: {self.email}>'


# class UserStory(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     project_id = db.Column(db.String(50), db.ForeignKey('project.project_id'), nullable=False)
#     sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id'), nullable=True)
#     team = db.Column(db.String(50), nullable=False)
#     description = db.Column(db.Text, nullable=False)
#     story_point = db.Column(db.Integer, nullable=False)
#     status = db.Column(db.String(20), nullable=False, default='Not Started')
#     created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

#     def to_dict(self):
#         return {
#             'id': self.id,
#             'project_id': self.project_id,
#             'sprint_id': self.sprint_id,
#             'team': self.team,
#             'description': self.description,
#             'story_point': self.story_point,
#             'status': self.status
#         }


# class Sprint(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     project_id = db.Column(db.String(50), db.ForeignKey('project.project_id'), nullable=False)
#     sprint_number = db.Column(db.Integer, nullable=False)
#     scrum_master = db.Column(db.String(100), nullable=False)
#     start_date = db.Column(db.Date, nullable=False)
#     end_date = db.Column(db.Date, nullable=False)
#     velocity = db.Column(db.Integer, nullable=False, default=0)
#     status = db.Column(db.String(20), nullable=False, default='Not Started')

#     # Add relationship to user stories
#     user_stories = db.relationship('UserStory', backref='sprint', lazy=True)

#     def to_dict(self):
#         return {
#             'id': self.id,
#             'project_id': self.project_id,
#             'sprint_number': self.sprint_number,
#             'scrum_master': self.scrum_master,
#             'start_date': self.start_date.strftime('%Y-%m-%d'),
#             'end_date': self.end_date.strftime('%Y-%m-%d'),
#             'velocity': self.velocity,
#             'status': self.status
#         }

#     def __repr__(self):
#         return f'<Sprint {self.sprint_number} for Project {self.project_id}>'
from . import db  # Import the shared db instance
from datetime import datetime
from sqlalchemy import DateTime, Column, Integer, String, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import relationship

class Project(db.Model):
    __tablename__ = 'project'  # Explicit table name
    # id = Column(Integer)
    project_id = Column(String(100), primary_key=True)
    project_name = Column(String(100), nullable=False)
    project_description = Column(Text, nullable=False)
    product_owner = Column(String(50), nullable=False)
    development_team = Column(db.JSON, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    revised_end_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default='Not Started')

    # Relationships
    sprints = relationship('Sprint', back_populates='project', lazy=True)
    user_stories = relationship('UserStory', back_populates='project', lazy=True)

    def to_dict(self):
        return {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'project_description': self.project_description,
            'product_owner': self.product_owner,
            'development_team': self.development_team,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'revised_end_date': self.revised_end_date.strftime('%Y-%m-%d') if self.revised_end_date else None,
            'status': self.status
        }

    def __repr__(self):
        return f'<Project {self.project_id}: {self.project_name}>'


class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    logout = Column(DateTime, nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(15), nullable=False)
    password = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)
    status = Column(Integer, default=0, nullable=False)
    address = Column(String(50), nullable=False)
    mfa_secret = Column(String(16), nullable=True)
    mfa = Column(Integer, default=0, nullable=False)
    mfa_setup_complete = Column(Boolean, default=False)

    def __repr__(self):
        return f'User("{self.id}","{self.name}","{self.email}")'


class Admin(db.Model):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    def __repr__(self):
        return f'<Admin {self.id}: {self.email}>'


class UserStory(db.Model):
    __tablename__ = 'user_story'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.project_id'), nullable=False) # Use Project's id
    sprint_id = Column(Integer, ForeignKey('sprint.id'), nullable=True) # Use Sprint's id
    team = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    story_point = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='Not Started')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="user_stories")
    sprint = relationship("Sprint", back_populates="user_stories")

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sprint_id': self.sprint_id,
            'team': self.team,
            'description': self.description,
            'story_point': self.story_point,
            'status': self.status
        }

    def __repr__(self):
        return f'<UserStory {self.id}>'


class Sprint(db.Model):
    __tablename__ = 'sprint'
    id = Column(Integer, primary_key=True)
    project_id = Column(String(50), ForeignKey('project.project_id'), nullable=False)  #Keep String, as this is Project's project_id type
    sprint_number = Column(Integer, nullable=False)
    scrum_master = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    velocity = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default='Not Started')

    # Relationships
    project = relationship('Project', back_populates='sprints', lazy=True)
    user_stories = relationship('UserStory', back_populates='sprint', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sprint_number': self.sprint_number,
            'scrum_master': self.scrum_master,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'velocity': self.velocity,
            'status': self.status
        }

    def __repr__(self):
        return f'<Sprint {self.sprint_number} for Project {self.project_id}>'




# # Tasks Table
# class Tasks(db.Model):
#     __tablename__ = 'tasks'
#     TaskId = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     UserStoryID = db.Column(db.Integer, db.ForeignKey('user_story.id'), nullable=False)
#     TaskName = db.Column(db.String(255), nullable=False)
#     AssignedTo = db.Column(db.String(100), db.ForeignKey('project.development_team'), nullable=False)
#     TaskStatus = db.Column(db.String(100), default="Not Started")

#     # Relationships
#     user_stories = db.relationship('UserStory', backref='tasks')

#     def __repr__(self):
#         return f"<Tasks {self.TaskName}>"



class StatusChangeLog(db.Model):
    __tablename__ = 'status_change_log'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.project_id'), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    auto_calculated = db.Column(db.Boolean, default=False)

    project = db.relationship('Project', backref=db.backref('status_changes', lazy=True))



