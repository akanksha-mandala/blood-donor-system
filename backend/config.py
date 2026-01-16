import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Loads variables from the .env file into the environment
load_dotenv() 

class Config:
    """Flask and SQLAlchemy configuration settings."""
    
    # Database credentials from .env
    DB_USER = os.getenv("DB_USER")
    # Encode password to handle special characters like '@'
    DB_PASS = quote_plus(os.getenv("DB_PASS"))  
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    
    # Construct the full SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail configuration (for potential notification emails)
    MAIL_SERVER = 'smtp.example.com'  # Placeholder
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your_email@example.com' # Placeholder
    MAIL_PASSWORD = 'your_email_password' # Placeholder
    
    # Twilio/SMS configuration (for potential mobile notifications)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER") 

