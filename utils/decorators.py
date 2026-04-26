from functools import wraps
from flask import jsonify, flash, redirect, url_for
from flask_login import current_user, login_required

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


def driver_page_required(f):
    """HTML pages: redirect drivers (and admin); JSON APIs should keep using driver_required."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ('driver', 'admin'):
            flash('This page is for drivers. Switch account or register as a driver to offer rides.', 'warning')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def passenger_page_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ('passenger', 'admin'):
            flash('This page is for passengers. Register as a passenger to search and book rides.', 'warning')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated