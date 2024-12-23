import os
import sqlite3
import time
from jinja2 import TemplateNotFound
import requests
from flask import Flask, flash, redirect, request, jsonify, session, render_template, url_for, abort, send_file, send_from_directory
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from .models import ActivityLog, db, User, Game, PurchaseHistory, Store
from .utils import TIME_RANGES
from datetime import datetime, timedelta
from .log_activity_decorator import log_activity
from backend import utils
from flask_login import login_user, logout_user, current_user

# List of valid avatars for users to select
VALID_AVATARS = ['avatar1.jpg', 'avatar2.jpg', 'avatar3.jpg', 'avatar4.jpg', 'avatar5.jpg', 'avatar6.jpg']
# Default avatar if none is selected
DEFAULT_AVATAR = 'placeholder.jpg'

def register_routes(app):
    # Route for the homepage
    @app.route('/')
    def index():
        print("Accessed the homepage route.")
        return render_template('index.html')
    
    # Route for handling user login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            print(f"Login attempt with email: {email}")

            # Query the user from the database
            user = User.query.filter_by(email=email).first()
            if not user:
                print("No user found with that email.")
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

            # Validate password (password should be hashed in a production system)
            if not check_password_hash(user.password, password):
                print(f"Password mismatch for user: {email}")
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

            # Log the user in
            login_user(user)
            print(f"User logged in successfully: ID={user.id}, Email={user.email}")
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))

        print("Rendering login page.")
        return render_template('login.html')

    # Route for user registration page
    @app.route('/register')
    def register():
        print("Accessed the registration page.")
        return render_template('register.html')
    
    # Route for logging out the user and clearing session data
    @app.route('/user_logout', methods=['POST'])
    @log_activity('logout', 'User logged out successfully')  # Log the logout action
    def user_logout():
        print("Logging out user. Clearing session data.")
        session.pop('user_id', None)
        session.pop('first_name', None)
        session.pop('last_name', None)
        session.pop('is_admin', None)
        return jsonify({'message': 'Logout Succeeded, redirecting...', 'redirect_url': '/login'}), 200
    
    # Route for viewing free games, accessible only to logged-in users
    @app.route('/free_games')
    def free_games():
        if 'user_id' not in session:
            print("User not logged in. Redirecting to login.")
            return redirect('/login')
        
        user = User.query.get(session['user_id'])
        print(f"Rendering free games for user: {user.first_name} (Admin={user.is_admin})")
        return render_template('free_games.html', username=user.first_name, is_admin=user.is_admin)
    
    # Route for viewing the store, accessible only to logged-in users
    @app.route('/games_store')
    def games_store():
        if 'user_id' not in session:
            print("User not logged in. Redirecting to login.")
            return redirect('/login')
        user = User.query.get(session['user_id'])
        print(f"Rendering game store for user: {user.first_name} (Admin={user.is_admin})")
        return render_template('games_store.html', username=user.first_name, is_admin=user.is_admin)
    
    # Route for viewing the purchase history, accessible only to logged-in users
    @app.route('/purchase_history')
    def purchase_history():
        if 'user_id' not in session:
            print("User not logged in. Redirecting to login.")
            return redirect('/login')
        user = User.query.get(session['user_id'])
        print(f"Rendering purchase history for user: {user.first_name}")
        return render_template('purchase_history.html', username=user.first_name, is_admin=user.is_admin)

   # Route for handling user registration through a POST request
    @app.route('/user_register', methods=['POST'])
    @log_activity('register', 'User registered successfully', 'Registration failed')  # Log registration activity
    def user_register():
        print("User registration attempt.")
        data = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "username": request.form['username'],
            "email": request.form['email'],
            "password": request.form['password'],
            "is_admin": False  # Ensure is_admin is always False for regular users
        }

        # Hash the password before storing
        hashed_password = generate_password_hash(data['password'])
        print(f"Hashed password generated for user: {data['username']}")

        try:
            # Check if the Super Admin exists and create one if necessary
            super_admin_exists = User.query.filter_by(email='superadmin@example.com').first() is not None
            
            if not super_admin_exists:
                print("Creating Super Admin user.")
                super_admin = User(
                    first_name='Super',
                    last_name='Admin',
                    email='superadmin@example.com',
                    password=generate_password_hash('superpassword'),
                    is_admin=True
                )
                db.session.add(super_admin)

            # Check if the username already exists in the database
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                print(f"Username already taken: {data['username']}")
                return jsonify({"message": "Username is already taken", "status": "error"}), 400
            
            # Check if the email is already registered
            existing_email = User.query.filter_by(email=data['email']).first()
            if existing_email:
                print(f"Email already registered: {data['email']}")
                return jsonify({"message": "Email is already registered", "status": "error"}), 400

            # Create a new user and add them to the database
            new_user = User(
                first_name=data['first_name'], 
                last_name=data['last_name'], 
                username=data['username'], 
                email=data['email'], 
                password=hashed_password, 
                is_admin=data['is_admin']
            )
            db.session.add(new_user)
            db.session.commit()
            print(f"User registered successfully: {data['username']}")
            return jsonify({"message": "User registered successfully", "status": "success"}), 201
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred during registration: {e}")
            return jsonify({"message": "An unexpected error has occurred", "status": "error"}), 500

    # Route for handling user login via POST
    @app.route('/user_login', methods=['POST'])
    @log_activity('user_login', 'User logged in successfully', 'User log in failed')  # Log login activity
    def user_login():
        email = request.form['email']
        password = request.form['password']

        print(f"Attempting login with email: {email}")  # Debug print

        # Allow Super Admin login without prior registration check
        super_admin_email = 'superadmin@example.com'
        if email == super_admin_email and password == 'superpassword':
            print("Super Admin login detected.")  # Debug print
            session['user_id'] = 1  # Assuming Super Admin has ID 1
            session['first_name'] = 'Super'
            session['last_name'] = 'Admin'
            session['is_admin'] = True
            print("Super Admin logged in successfully.")  # Debug print
            return jsonify({'message': 'Super Admin login succeeded', "isAdmin": True}), 200

        # Normal user login
        user = User.query.filter_by(email=email).first()

        if user:
            print(f"User found: {user.email}, ID: {user.id}")  # Debug print
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                session['is_admin'] = user.is_admin
                print("User logged in successfully.")  # Debug print

    # Route for the user dashboard
    @app.route('/user_dashboard')
    def user_dashboard():
        if 'user_id' not in session:
            print("User not logged in. Redirecting to login.")
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user:
            print("Invalid user session. Redirecting to login.")
            return redirect(url_for('login'))

        print(f"Rendering dashboard for user: {user.first_name} (Admin={user.is_admin})")
        # Add timestamp to prevent caching
        timestamp = int(time.time())
        avatars = ['avatar1.jpg', 'avatar2.jpg', 'avatar3.jpg', 'avatar4.jpg', 'avatar5.jpg', 'avatar6.jpg']
        return render_template(
            'user_dashboard.html',
            username=user.first_name,
            is_admin=user.is_admin,
            current_avatar=user.user_avatar,
            avatars=avatars,
            timestamp=timestamp  # Pass timestamp to template to prevent caching
        )

    # Route for the admin dashboard
    @app.route('/admin_dashboard')
    def admin_dashboard():
        # Ensure the user is logged in
        if 'user_id' not in session:
            print("Admin dashboard access attempted without login.")  # Debug print
            return redirect(url_for('login'))

        # Ensure the user is an admin
        if not session.get('is_admin'):
            print(f"User ID {session['user_id']} attempted to access the admin dashboard without admin rights.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        user = User.query.get(session['user_id'])
        print(f"Admin dashboard accessed by user ID {user.id}, name: {user.first_name} {user.last_name}.")  # Debug print
        return render_template('admin_dashboard.html', username=user.first_name, is_admin=user.is_admin)

    # Route to view all users (admin only)
    @app.route('/admin/users', methods=['GET'])
    def view_users():
        if 'user_id' not in session or not session.get('is_admin', False):
            print("Unauthorized attempt to view users.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        users = User.query.all()
        print(f"{len(users)} users fetched for admin view.")  # Debug print
        users_data = [
            {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_admin': user.is_admin
            }
            for user in users
        ]
        return jsonify({'users': users_data})
    
    # Route to view the store and available games
    @app.route('/store', methods=['GET'])
    def view_store():
        if 'user_id' not in session:
            print("Unauthorized store access attempted.")  # Debug print
            return redirect('/login')

        available_games = Store.query.all()
        print(f"Fetched {len(available_games)} games from the store.")  # Debug print

        purchased_games = PurchaseHistory.query.filter_by(user_id=session['user_id']).all()
        purchased_game_ids = [purchase.game_id for purchase in purchased_games]
        print(f"User ID {session['user_id']} has purchased {len(purchased_game_ids)} games.")  # Debug print

        games_data = [
            {
                "id": game.id,
                "game_name": game.game_name,
                "price": game.price,
                "thumbnail": game.thumbnail,
                "purchased": game.id in purchased_game_ids
            }
            for game in available_games
        ]
        return jsonify({"games": games_data}), 200
 
    # Route to render a specific game (after verifying purchase)
    @app.route('/play/<string:game_name>')
    def render_game(game_name):
        if 'user_id' not in session:
            print(f"Unauthorized attempt to play {game_name}.")  # Debug print
            return redirect('/login')

        user_id = session['user_id']
        normalized_game_name = utils.normalize_game_name(game_name)
        print(f"Normalized game name: {normalized_game_name}")  # Debug print

        game = Game.query.filter_by(game_name=game_name).first()
        if not game:
            print(f"Game {game_name} not found in the database.")  # Debug print
            return render_template('game_not_found.html'), 404

        purchase_record = PurchaseHistory.query.filter_by(user_id=user_id, game_id=game.id).first()
        if not purchase_record:
            print(f"User ID {user_id} attempted to play {game_name} without purchasing.")  # Debug print
            return render_template('game_not_purchased.html'), 403

        template_path = f"/games/{normalized_game_name}.html"
        print(f"Attempting to render game template: {template_path}.")  # Debug print

        try:
            return render_template(template_path)
        except TemplateNotFound:
            print(f"Template not found for game {normalized_game_name}.")  # Debug print
            return render_template('game_not_found.html', game_name=normalized_game_name), 404

    # Route to view purchase history
    @app.route('/purchase_history_data', methods=['GET'])
    def view_purchase_history_data():
        if 'user_id' not in session:
            print("Unauthorized attempt to view purchase history.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        current_user = User.query.get(session['user_id'])
        if not current_user:
            print(f"Session user ID {session['user_id']} not found in the database.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        if current_user.is_admin:
            purchase_records = PurchaseHistory.query.join(
                User, PurchaseHistory.user_id == User.id
            ).join(
                Store, PurchaseHistory.game_id == Store.id
            ).add_columns(
                User.first_name, User.last_name, Store.game_name, Store.price, PurchaseHistory.timestamp
            ).all()
            print(f"Admin fetched {len(purchase_records)} purchase records.")  # Debug print

            games_data = [
                {
                    "user_name": f"{record.first_name} {record.last_name}",
                    "game_name": record.game_name,
                    "price": record.price,
                    "purchase_timestamp": record.timestamp.isoformat()
                }
                for record in purchase_records
            ]
        else:
            purchased_games = PurchaseHistory.query.filter_by(user_id=current_user.id).all()
            print(f"User {current_user.id} has {len(purchased_games)} purchases.")  # Debug print

            purchased_game_ids = [purchase.game_id for purchase in purchased_games]
            games_data = []
            for game in Store.query.all():
                if game.id in purchased_game_ids:
                    purchase = next(p for p in purchased_games if p.game_id == game.id)
                    games_data.append({
                        "game_name": game.game_name,
                        "price": game.price,
                        "purchase_timestamp": purchase.timestamp.isoformat()
                    })

        return jsonify({"games": games_data}), 200

    # Route to handle game purchases
    @app.route('/buy/<int:game_id>', methods=['POST'])
    @log_activity('purchase', 'Game purchased successfully', 'Game purchase failed')
    def buy_game(game_id):
        # Ensure the user is logged in
        if 'user_id' not in session:
            print("Unauthorized purchase attempt.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch the game from the Store table
        game = Store.query.get(game_id)
        if not game:
            print(f"Game with ID {game_id} not found in the store.")  # Debug print
            return jsonify({"error": "Game not found"}), 404

        print(f"Game fetched for purchase: {game.game_name}, ID: {game.id}.")  # Debug print

        # Check if the game already exists in the Game table, if not, add it
        existing_game = Game.query.filter_by(id=game.id).first()
        if not existing_game:
            print(f"Game {game.game_name} does not exist in the Game table. Adding it.")  # Debug print
            new_game = Game(id=game.id, game_name=game.game_name, price=game.price)
            db.session.add(new_game)
            db.session.commit()
            print(f"Game {new_game.game_name} added to the Game table.")  # Debug print
        else:
            print(f"Game {existing_game.game_name} already exists in the Game table.")  # Debug print

        # Record the purchase in the PurchaseHistory table
        purchase = PurchaseHistory(game_id=game.id, user_id=session['user_id'])
        db.session.add(purchase)
        db.session.commit()
        print(f"Purchase recorded for user ID {session['user_id']} and game ID {game.id}.")  # Debug print

        return jsonify({"message": "Game purchased successfully"}), 200

    
    # -----------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------

    # Route to view the games purchased by the logged-in user
    @app.route('/user/games', methods=['GET'])
    def view_user_games():
        # Ensure the user is logged in
        if 'user_id' not in session:
            print("Unauthorized access attempt to view purchased games.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        # Get all games purchased by the user
        purchases = PurchaseHistory.query.filter_by(user_id=session['user_id']).all()
        print(f"Fetched {len(purchases)} purchases for user ID {session['user_id']}.")  # Debug print

        # Prepare a list of game details
        games = []
        for purchase in purchases:
            game = Game.query.get(purchase.game_id)
            if game:
                games.append({"gameName": game.game_name, "id": purchase.game_id})
                print(f"Added game: {game.game_name} (ID: {purchase.game_id}) to response.")  # Debug print
            else:
                print(f"Game with ID {purchase.game_id} not found in Game table.")  # Debug print

        return jsonify({"games": games}), 200

    # Helper function to check if a user is an authorized admin
    def is_authorized_admin():
        """Helper function to check if the user is an authorized admin."""
        is_admin = 'user_id' in session and session.get('is_admin', False)
        print(f"Admin check: {'Passed' if is_admin else 'Failed'} for user ID {session.get('user_id', 'Unknown')}.")  # Debug print
        return is_admin

    # Helper function to fetch logs within a specified time range
    def fetch_logs_within_time_range(start_time):
        """Fetch activity logs within a specified time range."""
        logs = ActivityLog.query.filter(ActivityLog.timestamp >= start_time) \
                                .order_by(ActivityLog.timestamp.desc()) \
                                .all()
        print(f"Fetched {len(logs)} logs since {start_time}.")  # Debug print
        return logs

    # Helper function to fetch the latest activity logs
    def fetch_latest_logs(limit=5):
        """Fetch the most recent activity logs."""
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        print(f"Fetched {len(logs)} latest activity logs.")  # Debug print
        return logs

    # Helper function to format log data into a list of dictionaries
    def format_log_data(logs):
        """Helper function to format log data into a list of dictionaries."""
        formatted_logs = [{
            'user_id': log.user_id,
            'activity_type': log.activity_type,
            'status': log.status,
            'details': log.details,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for log in logs]
        print(f"Formatted {len(formatted_logs)} logs.")  # Debug print
        return formatted_logs

    # Route to fetch the latest 5 activity logs
    @app.route('/admin/activity-log/tail', methods=['GET'])
    def view_activity_log_tail():
        """Fetch the latest 5 activity logs."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            print("Unauthorized admin access attempt to view latest logs.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        logs = fetch_latest_logs(limit=5)  # Fetch the most recent logs
        print("Fetched and returning latest activity logs.")  # Debug print
        return jsonify({"activity_log": format_log_data(logs)}), 200  # Return the formatted logs

    # Route to fetch activity logs filtered by a specific time range or all logs
    @app.route('/admin/activity-log/filter', methods=['GET'])
    def view_filtered_activity_log():
        """Fetch activity logs filtered by a specific time range or all logs."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            print("Unauthorized admin access attempt to view filtered logs.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        time_range = request.args.get('time_range')  # Get the time range from the query parameters
        print(f"Received time range filter: {time_range}.")  # Debug print

        if time_range == 'all':  # Fetch all logs without a time filter
            logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
            print("Fetched all activity logs.")  # Debug print
        elif time_range in TIME_RANGES:  # Fetch logs within a specific time range
            start_time = datetime.utcnow() - TIME_RANGES[time_range]
            logs = fetch_logs_within_time_range(start_time)
            print(f"Fetched logs within time range: {time_range}.")  # Debug print
        else:
            print("Invalid time range filter provided.")  # Debug print
            return jsonify({"error": "Invalid time range"}), 400

        return jsonify({"activity_log": format_log_data(logs)}), 200  # Return the formatted logs

    # Route to edit the price of an existing game in the store
    @app.route('/admin/store/edit/<int:game_id>', methods=['PATCH'])
    def edit_game_price(game_id):
        """Edit the price of an existing game."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            print(f"Unauthorized admin access attempt to edit game price for game ID {game_id}.")  # Debug print
            return jsonify({"error": "Unauthorized"}), 401

        try:
            new_price = float(request.form.get('price'))  # Get the new price from the request form
        except (TypeError, ValueError):
            print("Invalid price value provided.")  # Debug print
            return jsonify({"error": "Invalid price"}), 400

        game = Store.query.get(game_id)  # Fetch the game by its ID
        if not game:  # Check if the game exists
            print(f"Game with ID {game_id} not found in the Store table.")  # Debug print
            return jsonify({"error": "Game not found"}), 404

        if new_price <= 0:  # Validate the new price
            print(f"Attempted to set an invalid price ({new_price}) for game ID {game_id}.")  # Debug print
            return jsonify({"error": "Invalid price"}), 400

        game.price = new_price  # Update the price
        db.session.commit()  # Commit the changes to the database
        print(f"Updated price of game ID {game_id} to {new_price}.")  # Debug print

        return jsonify({"message": "Game price updated successfully"}), 200

    # Route to remove a game from the store
    @app.route('/admin/store/remove/<int:game_id>', methods=['DELETE'])
    def remove_game(game_id):
        """Remove a game from the store."""
        print(f"[DEBUG] Admin requested to remove game with ID: {game_id}")
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            print("[ERROR] Unauthorized admin access attempt")
            return jsonify({"error": "Unauthorized"}), 401

        game = Store.query.get(game_id)  # Fetch the game by its ID
        print(f"[DEBUG] Fetched game: {game}")
        if not game:  # Check if the game exists
            print(f"[ERROR] Game with ID {game_id} not found")
            return jsonify({"error": "Game not found"}), 404

        db.session.delete(game)  # Remove the game from the database
        db.session.commit()  # Commit the changes to the database
        print(f"[DEBUG] Game with ID {game_id} removed successfully")

        return jsonify({"message": "Game removed successfully"}), 200


    # Route to add a new game to the store
    @app.route('/admin/store/add', methods=['POST'])
    def add_game():
        """Add a new game to the store."""
        print("[DEBUG] Admin requested to add a new game")
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            print("[ERROR] Unauthorized admin access attempt")
            return jsonify({"error": "Unauthorized"}), 401

        game_name = request.form.get('game_name')  # Get the game name from the form
        price = request.form.get('price')  # Get the price from the form

        print(f"[DEBUG] Received game_name: {game_name}, price: {price}")
        try:
            price = float(price)
        except (ValueError, TypeError):
            print("[ERROR] Invalid price input")
            return jsonify({"error": "Invalid input"}), 400

        if not game_name or price <= 0:  # Validate the input
            print("[ERROR] Invalid input: game_name or price")
            return jsonify({"error": "Invalid input"}), 400

        new_game = Store(game_name=game_name, price=price)  # Create a new game record
        db.session.add(new_game)  # Add the game to the database
        db.session.commit()  # Commit the changes to the database
        print(f"[DEBUG] Game '{game_name}' added successfully with price {price}")

        return jsonify({"message": "Game added successfully"}), 201


    # Route to serve a specific game by its ID
    @app.route('/game/<int:game_id>')
    def serve_game(game_id):
        print(f"[DEBUG] User requested to access game with ID: {game_id}")
        if 'user_id' not in session:  # Check if the user is logged in
            print("[ERROR] User not logged in, redirecting to login")
            return redirect(url_for('login'))

        # Check if the user has purchased the game
        purchase = PurchaseHistory.query.filter_by(user_id=session['user_id'], game_id=game_id).first()
        print(f"[DEBUG] Purchase record for user: {purchase}")
        if purchase:
            file_name = f'{Game.query.get(purchase.game_id).game_name}.html'  # Construct the game file name
            file_path = os.path.join('games', file_name)  # Define the file path
            print(f"[DEBUG] Game file path: {file_path}")

            # Serve the game file if it exists
            if os.path.exists(file_path):
                print(f"[DEBUG] Serving game file: {file_name}")
                return send_from_directory('games', file_name, mimetype='text/html')
            else:
                print(f"[ERROR] Game file not found: {file_path}")
                abort(404)  # File not found
        else:
            print("[ERROR] User has not purchased the game")
            return jsonify({"error": "Unauthorized"}), 403  # User has not purchased the game


    # Route to serve static files (e.g., CSS, JavaScript)
    @app.route('/frontend/<path:filename>')
    def serve_static(filename):
        print(f"[DEBUG] Serving static file: {filename}")
        return send_from_directory('frontend', filename)


    # Route to get a list of free games from the FreeToGame API
    @app.route('/free_games', methods=['GET'])
    def get_free_games():
        api_url = "https://www.freetogame.com/api/games"
        print(f"[DEBUG] Fetching free games from API: {api_url}")
        try:
            response = requests.get(api_url, timeout=10)  # Set a timeout for the request
            response.raise_for_status()  # Raise an error for bad responses
            games = response.json()  # Parse the JSON response
            print(f"[DEBUG] Successfully fetched {len(games)} games")
            return jsonify(games), 200
        except requests.exceptions.Timeout:
            print("[ERROR] Request to FreeToGame API timed out")
            return jsonify({'error': 'Request timed out'}), 504
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching games: {e}")  # Log the error for debugging
            return jsonify({'error': 'Failed to fetch games'}), 500


    # Route to update the user's avatar
    @app.route('/update_user_avatar', methods=['POST'])
    def update_user_avatar():
        print("[DEBUG] User requested to update avatar")
        if 'user_id' not in session:  # Check if the user is logged in
            print("[ERROR] User not logged in, redirecting to login")
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])  # Fetch the logged-in user
        if not user:  # Check if the user exists
            print("[ERROR] User not found, redirecting to login")
            return redirect(url_for('login'))
        
        user_avatar = request.form.get('user_avatar')  # Get the new avatar from the form
        print(f"[DEBUG] Received avatar: {user_avatar}")
        if user_avatar:
            user.user_avatar = user_avatar  # Update the user's avatar
            db.session.commit()  # Commit the changes to the database
            avatar_url = url_for('static', filename=f'avatars/{user_avatar}', _external=True)  # Build the avatar URL
            print(f"[DEBUG] Avatar updated successfully: {avatar_url}")

            return jsonify({
                'status': 'success',
                'updated_avatar_url': avatar_url  # Return the new avatar URL
            })
        print("[ERROR] Invalid avatar data")
        return jsonify({'status': 'error', 'message': 'Invalid avatar data'}), 400


    # Route to check if a username is available
    @app.route('/check_username/<username>', methods=['GET'])
    def check_username(username):
        print(f"[DEBUG] Checking availability for username: {username}")
        user = User.query.filter_by(username=username).first()  # Check if the username already exists
        if user:
            print(f"[DEBUG] Username '{username}' is already taken")
            return jsonify({'status': 'error', 'message': 'Username is already taken'})
        
        print(f"[DEBUG] Username '{username}' is available")
        return jsonify({'status': 'success', 'message': 'Username is available'})


    # Add utility functions that will be available in all templates
    @app.context_processor
    def utility_processor():
        """Add these variables to all templates"""
        timestamp = int(time.time())  # Generate a timestamp for cache-busting
        print(f"[DEBUG] Generating timestamp: {timestamp}")
        
        def get_current_avatar():
            if 'user_id' in session:  # Check if the user is logged in
                user = User.query.get(session['user_id'])  # Fetch the logged-in user
                if user and user.user_avatar:  # Check if the user has an avatar
                    print(f"[DEBUG] User avatar found: {user.user_avatar}")
                    return user.user_avatar
            print("[DEBUG] No avatar found, returning default avatar")
            return DEFAULT_AVATAR  # Return the default avatar if no avatar is set

        return dict(
            timestamp=timestamp,
            avatars=VALID_AVATARS,  # Return a list of valid avatars
            current_avatar=get_current_avatar()  # Return the current user's avatar
        )


    # Route to fetch revenue statistics for the admin
    @app.route('/admin/revenue-stats', methods=['GET'])
    def get_revenue_stats():
        print("[DEBUG] Admin requested revenue statistics")
        today = datetime.today().date()  # Get today's date

        # Query to calculate today's sales
        today_sales = db.session.query(func.sum(Game.price)).join(PurchaseHistory).filter(
            PurchaseHistory.timestamp >= datetime.combine(today, datetime.min.time())
        ).scalar() or 0
        print(f"[DEBUG] Today's sales: ${today_sales:.2f}")

        # Query to calculate total sales
        total_sales = db.session.query(func.sum(Game.price)).join(PurchaseHistory).scalar() or 0
        print(f"[DEBUG] Total sales: ${total_sales:.2f}")

        # Query to calculate today's revenue (same as sales in this case)
        today_revenue = today_sales
        print(f"[DEBUG] Today's revenue: ${today_revenue:.2f}")

        # Query to calculate total revenue
        total_revenue = total_sales
        print(f"[DEBUG] Total revenue: ${total_revenue:.2f}")
        
        return jsonify({
            'today_sales': today_sales,
            'total_sales': total_sales,
            'today_revenue': today_revenue,
            'total_revenue': total_revenue
        })


    # Route to fetch recent sales data for the admin
    @app.route('/admin/recent-sales', methods=['GET'])
    def get_recent_sales():
        print("[DEBUG] Admin requested recent sales data")
        recent_sales = db.session.query(
            PurchaseHistory,
            Game,
            User
        ).join(Game, PurchaseHistory.game_id == Game.id).join(User, PurchaseHistory.user_id == User.id).order_by(PurchaseHistory.timestamp.desc()).limit(5).all()

        if not recent_sales:
            print("[DEBUG] No recent sales data available")
            return jsonify({'message': 'No recent sales data available.'})

        sales_data = []
        for sale in recent_sales:
            print(f"[DEBUG] Sale found: {sale.PurchaseHistory.id}, Date: {sale.PurchaseHistory.timestamp}, Customer: {sale.User.username}, Amount: ${sale.Game.price:.2f}")
            sales_data.append({
                'date': sale.PurchaseHistory.timestamp.strftime('%d %b %Y'),
                'invoice': f"INV-{sale.PurchaseHistory.id}",
                'customer': sale.User.username,
                'amount': f"${sale.Game.price:.2f}",
                'status': 'Paid',
                'action': 'View Details'
            })

        return jsonify(sales_data)