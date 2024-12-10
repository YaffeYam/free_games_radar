import os
from flask import Flask, config, redirect, request, session
from flask_session import Session
from flask_migrate import Migrate
from backend import config, models, routes
from backend.models import User, db, Store
from backend.routes import register_routes
from flask_login import LoginManager
from werkzeug.utils import secure_filename


# Sample list of game names and prices (you may want to move this to a separate file)
GAMES = [
    {"game_name": "Breakout", "price": 30, "thumbnail": "breakout_thumbnail.jpg"},
    {"game_name": "Frogger", "price": 55, "thumbnail": "frogger_thumbnail.jpg"},
    {"game_name": "Pong", "price": 100, "thumbnail": "pong_thumbnail.jpg"},
    {"game_name": "Snake", "price": 60, "thumbnail": "snake_thumbnail.jpg"},
    {"game_name": "Tic-Tac-Toe", "price": 40, "thumbnail": "tic_tac_toe_thumbnail.jpg"}
]

def init_store(app):
    if Store.query.count() == 0:
        games_to_add = [
            Store(game_name=game['game_name'], price=game['price'], thumbnail=game['thumbnail'])
            for game in GAMES
        ]
        db.session.bulk_save_objects(games_to_add)
        db.session.commit()
        app.logger.info("Store initialized with games.")
    else:
        app.logger.info("Store already contains games.")

def create_app():
    app = Flask(__name__, template_folder='frontend')
    app.config.from_object(config.Config)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)

    # Set the login view for users who are not logged in
    login_manager.login_view = "index"  # Replace with your login route if different
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Use environment variables for sensitive data
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')  # Change to a real secret key in prod
    app.config['SESSION_TYPE'] = 'filesystem'

    # Database URI should also come from environment variables for flexibility
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///free_games_radar.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Additional session settings for security
    app.config['SESSION_PERMANENT'] = False  # Sessions are not permanent by default
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # Enable secure cookies in production
    app.config['SESSION_USE_SIGNER'] = True  # Adds an extra layer of security to cookies

    # Initialize extensions
    Session(app)
    db.init_app(app)
    migrate = Migrate(app, db)  # Flask-Migrate setup for database migrations

    with app.app_context():
        try:
            db.create_all()  # Create tables if they don't exist
            init_store(app)  # Initialize store with games
        except Exception as e:
            app.logger.error(f"Error initializing the app: {e}")  # Log errors in initialization
    
    # Define the user_loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Query your database to return the user

    register_routes(app)  # Register routes

    # Flask logging setup
    import logging
    logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)  # Remove debug=True in production
