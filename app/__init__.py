from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_session import Session
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from app.config import Config
# Initialize extensions
db = SQLAlchemy()  # Single instance of SQLAlchemy
bcrypt = Bcrypt()
migrate = Migrate()
mail = Mail()
session = Session()

def create_app():
    # Create the Flask app
    application = Flask(__name__, instance_relative_config=True, template_folder='templates')

    # Load configuration
    application.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(application)  # Initialize SQLAlchemy with the app
    bcrypt.init_app(application)
    migrate.init_app(application, db)
    mail.init_app(application)
    session.init_app(application)

    # Serializer for token generation
    serializer = URLSafeTimedSerializer(application.config['SECRET_KEY'])

    # Register blueprints
    with application.app_context():
        from .routes import auth, admin, main  # Import blueprints
        application.register_blueprint(auth)
        application.register_blueprint(admin)
        application.register_blueprint(main)

        # Create database tables (only if they don't exist)
        db.create_all()



    return application
