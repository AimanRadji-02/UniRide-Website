from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models import db
from models.user import User
from models.ride import Ride
from models.booking import Booking
from models.sos_event import SOSEvent
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')

# ... rest of the routes as provided earlier