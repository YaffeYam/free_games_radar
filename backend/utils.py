import re
from werkzeug.security import check_password_hash
from .models import User
from datetime import timedelta

def authenticate_user(username, password):
    """
    Authenticate a user based on their username and password.

    Parameters:
        username (str): The username of the user attempting to log in.
        password (str): The plaintext password provided by the user.

    Returns:
        User: The authenticated User object if credentials are valid.
        None: If authentication fails.
    """
    # Query the database for a user with the given username
    user = User.query.filter_by(username=username).first()

    # Verify the password against the hashed password in the database
    if user and check_password_hash(user.password, password):
        return user

    # Return None if authentication fails
    return None

# Predefined time ranges for filtering data
TIME_RANGES = {
    '1m': timedelta(minutes=1),    # 1 minute
    '15m': timedelta(minutes=15),  # 15 minutes
    '1h': timedelta(hours=1),      # 1 hour
    '1d': timedelta(days=1),       # 1 day
    '1w': timedelta(weeks=1)       # 1 week
}

def normalize_game_name(game_name):
    """
    Normalize a game name for consistent formatting.

    Parameters:
        game_name (str): The original name of the game.

    Returns:
        str: A normalized game name with spaces replaced by underscores 
             and only lowercase alphanumeric characters and underscores retained.
    """
    # Replace spaces with underscores
    game_name = re.sub(r'\s+', '_', game_name)

    # Remove any non-alphanumeric characters (except underscores) and convert to lowercase
    return re.sub(r'[^a-z0-9_]', '', game_name.lower())
