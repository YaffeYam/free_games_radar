import os

class Config:
    # Secret key used for session and cookie encryption. Should be kept secret in production.
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')  # Secure secret key from environment variable
    
    # URI for the database connection, uses an environment variable for production settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///gaming_store.db')  # Database URI from environment variable
    
    # Disable the modification tracking for performance reasons
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications for performance
    
    # Session settings, to make the session non-permanent by default
    SESSION_PERMANENT = False  # Set sessions to not be permanent by default
    
    # Secure cookies in production environment only
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'  # Enable secure cookies in production
    
    # Add an additional layer of security to session cookies by signing them
    SESSION_USE_SIGNER = True  # Adds an extra layer of security to cookies
    
    # Use filesystem-based session storage
    SESSION_TYPE = 'filesystem'  # Type of session management
