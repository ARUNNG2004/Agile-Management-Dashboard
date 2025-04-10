# import os
# from dotenv import load_dotenv
# load_dotenv() 
# class Config:
#     # Don't share or commit .env file
#     SECRET_KEY = os.getenv('SECRET_KEY', "4a8f3111fb4a9de6a6d050dd2b6ef98e")
    
#     # Database Configuration
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    
    
#     # Mail Configuration
#     MAIL_SERVER = 'smtp.gmail.com'
#     MAIL_PORT = 587
#     MAIL_USE_TLS = True
#     MAIL_USE_SSL =False
#     MAIL_USERNAME =os.getenv('MAIL_USERNAME','teamofadm1n123@gmail.com')
#     MAIL_PASSWORD =os.getenv('MAIL_PASSWORD','wkmk oxaj rhov peup')
#     MAIL_DEFAULT_SENDER =os.getenv('MAIL_USERNAME','teamofadm1n123@gmail.com')
    
#     # Session Configuration
#     SESSION_PERMANENT = False
#     SESSION_TYPE = 'filesystem'
# import os
# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables from .env file

# class Config:
#     # General Configuration
#     SECRET_KEY = os.environ.get('SECRET_KEY', "4a8f3111fb4a9de6a6d050dd2b6ef98e")  # Fallback value for local testing

#     # Database Configuration
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'

#     # Mail Configuration
#     MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')  # Fallback if not in .env
#     MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))  # Use int() for safety
#     MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'  # Boolean from string
#     MAIL_USE_SSL = False  # Explicitly set SSL to False (TLS is preferred)
#     MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'teamofadm1n123@gmail.com')  # Fallback email
#     MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'wkmk oxaj rhov peup') #App Password (replace)
#     MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'teamofadm1n123@gmail.com')  # Sender Email

#     # Session Configuration
#     SESSION_PERMANENT = False
#     SESSION_TYPE = 'filesystem'


import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    # General Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', "4a8f3111fb4a9de6a6d050dd2b6ef98e")  # Fallback for local testing

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')

    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))  # Default to 587 if not set
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'  # Convert string to boolean
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'  # Explicitly handle SSL
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # No fallback here for security
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # No fallback here for security
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)  # Use username if not set

    # Session Configuration
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'

    # Debug Configuration (optional, for troubleshooting)
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    MAIL_DEBUG = DEBUG  # Enable mail debug output when in debug mode

# Verify critical email settings
if not os.environ.get('MAIL_USERNAME') or not os.environ.get('MAIL_PASSWORD'):
    raise ValueError("MAIL_USERNAME and MAIL_PASSWORD must be set in the .env file")