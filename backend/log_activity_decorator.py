import logging
from functools import wraps
from flask import request, session
from datetime import datetime
from .models import db, ActivityLog

# Set up logging to capture errors
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

def log_activity(activity_type, success_message, failure_message=None):
    """
    Decorator function to log user activities such as login, logout, purchases, etc.
    
    Parameters:
    - activity_type: The type of activity (e.g., 'login', 'purchase').
    - success_message: The message to log upon successful activity.
    - failure_message: The message to log upon failed activity (optional).
    
    The decorator wraps the target function, logging the activity and its status.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Fetch the user_id from session or use the remote IP address as a fallback
            user_id = session.get('user_id') or request.remote_addr or "Unknown User"
            status = 'failed'  # Default status is failure
            details = failure_message  # Default failure message

            try:
                # Call the original function and capture the result
                result = f(*args, **kwargs)
                
                # Check if the result indicates a successful operation (status code 200 or 201)
                if isinstance(result, tuple) and len(result) > 1 and result[1] in {200, 201}:
                    status = 'success'  # Update status to success
                    details = success_message  # Use the success message

                # Log the activity to the database
                log_to_db(user_id, activity_type, status, details)
                return result
            
            except Exception as e:
                # Log error details if the activity fails
                error_details = f"{failure_message}: {str(e)} | Endpoint: {request.path} | Data: {request.json or request.form}"
                log_to_db(user_id, activity_type, 'failed', error_details)
                # Log the error to the logger for debugging
                logger.error(f"Activity logging failed: {error_details}")
                raise e  # Reraise the exception to handle it at a higher level

        return wrapped
    return decorator

def log_to_db(user_id, activity_type, status, details):
    """
    Logs activity details to the database.
    
    Parameters:
    - user_id: The ID of the user performing the activity.
    - activity_type: The type of activity being logged.
    - status: The status of the activity (either 'success' or 'failed').
    - details: Additional details about the activity.
    """
    try:
        # Create a new activity log entry
        log = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            status=status,
            details=details,
            timestamp=datetime.utcnow()  # Store the current timestamp
        )
        # Add the log to the session and commit it to the database
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Log database commit failure
        logger.error(f"Failed to log activity to the database: {str(e)}")
