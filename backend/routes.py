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
        return render_template('index.html')
    
    # Route for handling user login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            # Query the user from the database
            user = User.query.filter_by(email=email).first()
            if not user:
                print("No user found with that email.")
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

            # Validate password (password should be hashed in a production system)
            if user.password != password:
                print("Password mismatch.")
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

            # Log the user in
            login_user(user)
            print(f"User logged in: {user.id}, {user.email}")
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))

        return render_template('login.html')

    # Route for user registration page
    @app.route('/register')
    def register():
        return render_template('register.html')
    
    # Route for logging out the user and clearing session data
    @app.route('/user_logout', methods=['POST'])
    @log_activity('logout', 'User logged out successfully')  # Log the logout action
    def user_logout():
        # Clear the session to log out the user
        session.pop('user_id', None)
        session.pop('first_name', None)
        session.pop('last_name', None)
        session.pop('is_admin', None)
        
        return jsonify({'message': 'Logout Succeeded, redirecting...', 'redirect_url': '/login'}), 200
    
    # Route for viewing free games, accessible only to logged-in users
    @app.route('/free_games')
    def free_games():
        if 'user_id' not in session:
            return redirect('/login')
        
        user = User.query.get(session['user_id'])
        return render_template('free_games.html', username=user.first_name, is_admin=user.is_admin)
    
    # Route for viewing the store, accessible only to logged-in users
    @app.route('/games_store')
    def games_store():
        if 'user_id' not in session:
            return redirect('/login')
        user = User.query.get(session['user_id'])
        return render_template('games_store.html', username=user.first_name, is_admin=user.is_admin)
    
    # Route for viewing the purchase history, accessible only to logged-in users
    @app.route('/purchase_history')
    def purchase_history():
        if 'user_id' not in session:
            return redirect('/login')
        user = User.query.get(session['user_id'])
        return render_template('purchase_history.html', username=user.first_name, is_admin=user.is_admin)

    # Route for handling user registration through a POST request
    @app.route('/user_register', methods=['POST'])
    @log_activity('register', 'User registered successfully', 'Registration failed')  # Log registration activity
    def user_register():
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

        try:
            # Check if the Super Admin exists and create one if necessary
            super_admin_exists = User.query.filter_by(email='superadmin@example.com').first() is not None
            
            if not super_admin_exists:
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
                return jsonify({"message": "Username is already taken", "status": "error"}), 400
            
            # Check if the email is already registered
            existing_email = User.query.filter_by(email=data['email']).first()
            if existing_email:
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

            return jsonify({"message": "User registered successfully", "status": "success"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "An unexpected error has occurred", "status": "error"}), 500

    # Route for handling user login via POST
    @app.route('/user_login', methods=['POST'])
    @log_activity('user_login', 'User logged in successfully', 'User log in failed')  # Log login activity
    def user_login():
        email = request.form['email']
        password = request.form['password']

        # Allow Super Admin login without prior registration check
        super_admin_email = 'superadmin@example.com'
        if email == super_admin_email and password == 'superpassword':
            session['user_id'] = 1  # Assuming Super Admin has ID 1
            session['first_name'] = 'Super'
            session['last_name'] = 'Admin'
            session['is_admin'] = True
            return jsonify({'message': 'Super Admin login succeeded', "isAdmin": True}), 200

        # Normal user login
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['is_admin'] = user.is_admin

            return jsonify({'message': 'Login Succeeded', "isAdmin": user.is_admin}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    # Route for the user dashboard
    @app.route('/user_dashboard')
    def user_dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user:
            
            return redirect(url_for('login'))

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
            return redirect(url_for('login'))
        
        # Ensure the user is an admin
        if not session.get('is_admin'):
            return jsonify({"error": "Unauthorized"}), 401  # Admin users only
                
        user = User.query.get(session['user_id'])  # Get the logged-in user's details
        return render_template('admin_dashboard.html', username=user.first_name, is_admin=user.is_admin)

    
    # Route to view all users (admin only)
    @app.route('/admin/users', methods=['GET'])
    def view_users():
        # Ensure the user is logged in and is an admin
        if 'user_id' not in session or session.get('is_admin', False) == False:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Retrieve all users
        users = User.query.all()
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
        # Ensure the user is logged in
        if 'user_id' not in session:
            return redirect('/login')        

        # Get all available games in the store and the user's purchased games
        available_games = Store.query.all()
        purchased_games = PurchaseHistory.query.filter_by(user_id=session['user_id']).all()
        purchased_game_ids = [purchase.game_id for purchase in purchased_games]

        # Prepare the data to send back to the frontend
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
        # Ensure the user is logged in
        if 'user_id' not in session:
            return redirect('/login')
        
        user_id = session['user_id']

        # Normalize the game name for better path handling
        normalized_game_name = utils.normalize_game_name(game_name)
        print(f"Normalized game name: {normalized_game_name}")

        # Fetch the game from the database
        game = Game.query.filter_by(game_name=game_name).first()
        print(f"Game found: {game}")
        if not game:
            return render_template('game_not_found.html'), 404  # Game not found
        
        # Check if the user has purchased the game
        purchase_record = PurchaseHistory.query.filter_by(user_id=user_id, game_id=game.id).first()
        if not purchase_record:
            return render_template('game_not_purchased.html'), 403  # Game not purchased

        # Construct the path for the game template
        template_path = f"/games/{normalized_game_name}.html"

        try:
            return render_template(template_path)  # Try rendering the game template
        except TemplateNotFound:
            return render_template('game_not_found.html', game_name=normalized_game_name), 404  # Game template not found


    # Route to view the user's purchase history or all purchase records for admin
    @app.route('/purchase_history_data', methods=['GET'])
    def view_purchase_history_data():
        # Ensure the user is logged in
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401

        # Get the logged-in user's data
        current_user = User.query.get(session['user_id'])
        if not current_user:
            return jsonify({"error": "Unauthorized"}), 401

        if current_user.is_admin:
            # Admin: Fetch all users' purchase histories
            purchase_records = PurchaseHistory.query.join(
                User, PurchaseHistory.user_id == User.id
            ).join(
                Store, PurchaseHistory.game_id == Store.id
            ).add_columns(
                User.first_name, User.last_name, Store.game_name, Store.price, PurchaseHistory.timestamp
            ).all()

            # Format the purchase data to return as JSON
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
            # Regular user: Fetch only their purchased games
            purchased_games = PurchaseHistory.query.filter_by(user_id=current_user.id).all()
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
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch the game from the Store table
        game = Store.query.get(game_id)
        if not game:
            return jsonify({"error": "Game not found"}), 404
        
        # Check if the game already exists in the Game table, if not, add it
        existing_game = Game.query.filter_by(id=game.id).first()
        if not existing_game:
            # Add new game if it does not exist in the Game table
            new_game = Game(id=game.id, game_name=game.game_name, price=game.price)
            db.session.add(new_game)
            db.session.commit()

        # Record the purchase in the PurchaseHistory table
        purchase = PurchaseHistory(game_id=game.id, user_id=session['user_id'])
        db.session.add(purchase)
        db.session.commit()

        return jsonify({"message": "Game purchased successfully"}), 200

    # Route to view the games purchased by the logged-in user
    @app.route('/user/games', methods=['GET'])
    def view_user_games():
        # Ensure the user is logged in
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401

        # Get all games purchased by the user
        purchases = PurchaseHistory.query.filter_by(user_id=session['user_id']).all()

        # Prepare a list of game details
        games = [
            {"gameName": Game.query.get(purchase.game_id).game_name, "id":purchase.game_id}
            for purchase in purchases
        ]
        return jsonify({"games": games}), 200

    # Helper function to check if a user is an authorized admin
    def is_authorized_admin():
        """Helper function to check if the user is an authorized admin."""
        return 'user_id' in session and session.get('is_admin', False)

    # Helper function to fetch logs within a specified time range
    def fetch_logs_within_time_range(start_time):
        """Fetch activity logs within a specified time range."""
        return ActivityLog.query.filter(ActivityLog.timestamp >= start_time) \
                                .order_by(ActivityLog.timestamp.desc()) \
                                .all()

    # Helper function to fetch the latest activity logs
    def fetch_latest_logs(limit=5):
        """Fetch the most recent activity logs."""
        return ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()

    # Helper function to format log data into a list of dictionaries
    def format_log_data(logs):
        """Helper function to format log data into a list of dictionaries."""
        return [{
            'user_id': log.user_id,
            'activity_type': log.activity_type,
            'status': log.status,
            'details': log.details,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for log in logs]


    # Route to fetch the latest 5 activity logs
    @app.route('/admin/activity-log/tail', methods=['GET'])
    def view_activity_log_tail():
        """Fetch the latest 5 activity logs."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            return jsonify({"error": "Unauthorized"}), 401

        logs = fetch_latest_logs(limit=5)  # Fetch the most recent logs
        return jsonify({"activity_log": format_log_data(logs)}), 200  # Return the formatted logs


    # Route to fetch activity logs filtered by a specific time range or all logs
    @app.route('/admin/activity-log/filter', methods=['GET'])
    def view_filtered_activity_log():
        """Fetch activity logs filtered by a specific time range or all logs."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            return jsonify({"error": "Unauthorized"}), 401

        time_range = request.args.get('time_range')  # Get the time range from the query parameters

        if time_range == 'all':  # Fetch all logs without a time filter
            logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
        elif time_range in TIME_RANGES:  # Fetch logs within a specific time range
            start_time = datetime.utcnow() - TIME_RANGES[time_range]
            logs = fetch_logs_within_time_range(start_time)
        else:
            return jsonify({"error": "Invalid time range"}), 400  # Handle invalid time range

        return jsonify({"activity_log": format_log_data(logs)}), 200  # Return the formatted logs


    # Route to edit the price of an existing game in the store
    @app.route('/admin/store/edit/<int:game_id>', methods=['PATCH'])
    def edit_game_price(game_id):
        """Edit the price of an existing game."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            return jsonify({"error": "Unauthorized"}), 401

        new_price = float(request.form.get('price'))  # Get the new price from the request form
        game = Store.query.get(game_id)  # Fetch the game by its ID
        
        if not game:  # Check if the game exists
            return jsonify({"error": "Game not found"}), 404

        if new_price <= 0:  # Validate the new price
            return jsonify({"error": "Invalid price"}), 400

        game.price = new_price  # Update the price
        db.session.commit()  # Commit the changes to the database

        return jsonify({"message": "Game price updated successfully"}), 200


    # Route to remove a game from the store
    @app.route('/admin/store/remove/<int:game_id>', methods=['DELETE'])
    def remove_game(game_id):
        """Remove a game from the store."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            return jsonify({"error": "Unauthorized"}), 401

        game = Store.query.get(game_id)  # Fetch the game by its ID
        if not game:  # Check if the game exists
            return jsonify({"error": "Game not found"}), 404

        db.session.delete(game)  # Remove the game from the database
        db.session.commit()  # Commit the changes to the database

        return jsonify({"message": "Game removed successfully"}), 200


    # Route to add a new game to the store
    @app.route('/admin/store/add', methods=['POST'])
    def add_game():
        """Add a new game to the store."""
        if not is_authorized_admin():  # Check if the user is authorized as an admin
            return jsonify({"error": "Unauthorized"}), 401

        game_name = request.form.get('game_name')  # Get the game name from the form
        price = float(request.form.get('price'))  # Get the price from the form
        
        if not game_name or price <= 0:  # Validate the input
            return jsonify({"error": "Invalid input"}), 400

        new_game = Store(game_name=game_name, price=price)  # Create a new game record
        db.session.add(new_game)  # Add the game to the database
        db.session.commit()  # Commit the changes to the database

        return jsonify({"message": "Game added successfully"}), 201


    # Route to serve a specific game by its ID
    @app.route('/game/<int:game_id>')
    def serve_game(game_id):
        if 'user_id' not in session:  # Check if the user is logged in
            return redirect(url_for('login'))

        # Check if the user has purchased the game
        purchase = PurchaseHistory.query.filter_by(user_id=session['user_id'], game_id=game_id).first()
        if purchase:
            file_name = f'{Game.query.get(purchase.game_id).game_name}.html'  # Construct the game file name
            file_path = os.path.join('games', file_name)  # Define the file path

            # Serve the game file if it exists
            if os.path.exists(file_path):
                return send_from_directory('games', file_name, mimetype='text/html')
            else:
                abort(404)  # File not found
        else:
            return jsonify({"error": "Unauthorized"}), 403  # User has not purchased the game


    # Route to serve static files (e.g., CSS, JavaScript)
    @app.route('/frontend/<path:filename>')
    def serve_static(filename):
        return send_from_directory('frontend', filename)


    # Route to get a list of free games from the FreeToGame API
    @app.route('/free_games', methods=['GET'])
    def get_free_games():
        api_url = "https://www.freetogame.com/api/games"
        try:
            response = requests.get(api_url, timeout=10)  # Set a timeout for the request
            response.raise_for_status()  # Raise an error for bad responses
            games = response.json()  # Parse the JSON response
            return jsonify(games), 200
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Request timed out'}), 504
        except requests.exceptions.RequestException as e:
            print(f"Error fetching games: {e}")  # Log the error for debugging
            return jsonify({'error': 'Failed to fetch games'}), 500


    # Route to update the user's avatar
    @app.route('/update_user_avatar', methods=['POST'])
    def update_user_avatar():
        if 'user_id' not in session:  # Check if the user is logged in
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])  # Fetch the logged-in user
        if not user:  # Check if the user exists
            return redirect(url_for('login'))
        
        user_avatar = request.form.get('user_avatar')  # Get the new avatar from the form
        if user_avatar:
            user.user_avatar = user_avatar  # Update the user's avatar
            db.session.commit()  # Commit the changes to the database
            avatar_url = url_for('static', filename=f'avatars/{user_avatar}', _external=True)  # Build the avatar URL

            return jsonify({
                'status': 'success',
                'updated_avatar_url': avatar_url  # Return the new avatar URL
            })
        return jsonify({'status': 'error', 'message': 'Invalid avatar data'}), 400


    # Route to check if a username is available
    @app.route('/check_username/<username>', methods=['GET'])
    def check_username(username):
        user = User.query.filter_by(username=username).first()  # Check if the username already exists
        if user:
            return jsonify({'status': 'error', 'message': 'Username is already taken'})
        return jsonify({'status': 'success', 'message': 'Username is available'})


    # Add utility functions that will be available in all templates
    @app.context_processor
    def utility_processor():
        """Add these variables to all templates"""
        timestamp = int(time.time())  # Generate a timestamp for cache-busting
        
        def get_current_avatar():
            if 'user_id' in session:  # Check if the user is logged in
                user = User.query.get(session['user_id'])  # Fetch the logged-in user
                if user and user.user_avatar:  # Check if the user has an avatar
                    return user.user_avatar
            return DEFAULT_AVATAR  # Return the default avatar if no avatar is set

        return dict(
            timestamp=timestamp,
            avatars=VALID_AVATARS,  # Return a list of valid avatars
            current_avatar=get_current_avatar()  # Return the current user's avatar
        )


    # Route to fetch revenue statistics for the admin
    @app.route('/admin/revenue-stats', methods=['GET'])
    def get_revenue_stats():
        today = datetime.today().date()  # Get today's date

        # Query to calculate today's sales
        today_sales = db.session.query(func.sum(Game.price)).join(PurchaseHistory).filter(
            PurchaseHistory.timestamp >= datetime.combine(today, datetime.min.time())
        ).scalar() or 0
        
        # Query to calculate total sales
        total_sales = db.session.query(func.sum(Game.price)).join(PurchaseHistory).scalar() or 0
        
        # Query to calculate today's revenue (same as sales in this case)
        today_revenue = today_sales
        
        # Query to calculate total revenue
        total_revenue = total_sales
        
        return jsonify({
            'today_sales': today_sales,
            'total_sales': total_sales,
            'today_revenue': today_revenue,
            'total_revenue': total_revenue
        })


    # Route to fetch recent sales data for the admin
    @app.route('/admin/recent-sales', methods=['GET'])
    def get_recent_sales():
        recent_sales = db.session.query(
            PurchaseHistory,
            Game,
            User
        ).join(Game, PurchaseHistory.game_id == Game.id).join(User, PurchaseHistory.user_id == User.id).order_by(PurchaseHistory.timestamp.desc()).limit(5).all()

        if not recent_sales:
            return jsonify({'message': 'No recent sales data available.'})

        sales_data = []
        for sale in recent_sales:
            sales_data.append({
                'date': sale.PurchaseHistory.timestamp.strftime('%d %b %Y'),
                'invoice': f"INV-{sale.PurchaseHistory.id}",
                'customer': sale.User.username,
                'amount': f"${sale.Game.price:.2f}",
                'status': 'Paid',
                'action': 'View Details'
            })

        return jsonify(sales_data)
