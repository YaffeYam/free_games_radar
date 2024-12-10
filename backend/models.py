from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize SQLAlchemy for database interactions
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    Represents a user in the database.
    
    Attributes:
    - id: The user's unique identifier.
    - first_name: The user's first name.
    - last_name: The user's last name.
    - username: The user's unique username.
    - email: The user's email address (unique).
    - password: The user's hashed password.
    - is_admin: A boolean indicating if the user is an admin.
    - purchases: The user's associated purchase history.
    - user_avatar: The path to the user's avatar image.
    - user_avatar_updated_at: The timestamp of when the avatar was last updated.
    """
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    purchases = db.relationship('PurchaseHistory', backref='user', lazy='select')  # Optimized lazy loading
    user_avatar = db.Column(db.String(120), default='placeholder.jpg')
    user_avatar_updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

    def get_id(self):
        # Required for Flask-Login to identify users
        return str(self.id)


class Game(db.Model):
    """
    Represents a game in the database.
    
    Attributes:
    - id: The game's unique identifier.
    - game_name: The name of the game.
    - price: The price of the game.
    - thumbnail: A URL or path to the game's thumbnail image.
    - purchase_history: A relationship to the PurchaseHistory model.
    """
    id = db.Column(db.Integer, primary_key=True)  # Changed to 'id' for consistency with relationships
    game_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    thumbnail = db.Column(db.String(255), nullable=True)
    purchase_history = db.relationship('PurchaseHistory', backref='game', lazy='select')  # Optimized lazy loading

    def __repr__(self):
        return f"<Game {self.game_name}>"


class PurchaseHistory(db.Model):
    """
    Represents a record of a user's game purchase.
    
    Attributes:
    - id: The unique purchase record identifier.
    - user_id: The ID of the user who made the purchase.
    - game_id: The ID of the purchased game.
    - timestamp: The time when the purchase was made.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PurchaseHistory User {self.user_id} Game {self.game_id}>"


class Store(db.Model):
    """
    Represents a game available for purchase in the store.
    
    Attributes:
    - id: The unique game identifier in the store.
    - game_name: The name of the game in the store.
    - price: The price of the game.
    - thumbnail: A URL or path to the game's thumbnail.
    """
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Store {self.game_name}>"


class ActivityLog(db.Model):
    """
    Represents a log of activities performed by users.
    
    Attributes:
    - id: The unique identifier of the log.
    - user_id: The ID of the user who performed the activity.
    - activity_type: The type of activity (e.g., 'login', 'purchase').
    - status: The result of the activity (e.g., 'success', 'failed').
    - details: Additional details about the activity (e.g., error messages).
    - timestamp: The timestamp of when the activity occurred.
    """
    __tablename__ = 'activity_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for unauthenticated actions
    activity_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'purchase', etc.
    status = db.Column(db.String(50), nullable=False)  # 'success', 'failed'
    details = db.Column(db.String(255), nullable=True)  # Additional info
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='activity_logs', lazy='select')  # Optimized lazy loading

    def __repr__(self):
        return f"<ActivityLog {self.activity_type} - {self.status}>"
