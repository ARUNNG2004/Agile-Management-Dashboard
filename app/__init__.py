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
    app = Flask(__name__, instance_relative_config=True, template_folder='templates')
    
    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)  # Initialize SQLAlchemy with the app
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    session.init_app(app)

    # Serializer for token generation
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    # Register blueprints
    with app.app_context():
        from .routes import auth, admin, main  # Import blueprints
        app.register_blueprint(auth)
        app.register_blueprint(admin)
        app.register_blueprint(main)

        # Create database tables (only if they don't exist)
        db.create_all()
        
        

    return app