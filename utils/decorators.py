from functools import wraps
from flask import jsonify
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Login required'}), 401
            if current_user.role not in roles:
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def driver_required(f):
    return role_required('driver', 'admin')(f)

def passenger_required(f):
    return role_required('passenger', 'admin')(f)