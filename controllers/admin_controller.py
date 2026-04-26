from flask import Blueprint, render_template, jsonify, request
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

@admin_bp.route('/api/users')
@login_required
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'user_id': u.user_id,
        'name': u.name,
        'email': u.email,
        'phone': u.phone,
        'role': u.role,
        'created_at': u.created_at.isoformat()
    } for u in users])

@admin_bp.route('/api/sos-alerts')
@login_required
@admin_required
def get_sos_alerts():
    alerts = SOSEvent.query.filter_by(status='active').order_by(SOSEvent.triggered_at.desc()).all()
    return jsonify([{
        'sos_id': s.sos_id,
        'ride_id': s.ride_id,
        'triggered_by': s.triggered_by,
        'gps_location': s.gps_location,
        'triggered_at': s.triggered_at.isoformat(),
        'status': s.status
    } for s in alerts])

@admin_bp.route('/api/resolve-sos/<int:sos_id>', methods=['POST'])
@login_required
@admin_required
def resolve_sos(sos_id):
    sos = SOSEvent.query.get_or_404(sos_id)
    sos.status = 'resolved'
    db.session.commit()
    return jsonify({'message': 'SOS resolved'})

@admin_bp.route('/api/stats')
@login_required
@admin_required
def get_stats():
    return jsonify({
        'total_users': User.query.count(),
        'total_rides': Ride.query.count(),
        'active_rides': Ride.query.filter_by(status='active').count(),
        'total_bookings': Booking.query.count(),
        'active_sos': SOSEvent.query.filter_by(status='active').count()
    })

@admin_bp.route('/api/rides')
@login_required
@admin_required
def get_all_rides():
    """Get all rides for admin management"""
    rides = Ride.query.order_by(Ride.created_at.desc()).all()
    return jsonify([{
        'ride_id': r.ride_id,
        'driver_id': r.driver_id,
        'driver_name': r.driver.name,
        'driver_email': r.driver.email,
        'origin': r.origin,
        'destination': r.destination,
        'departure_datetime': r.departure_datetime.isoformat(),
        'available_seats': r.available_seats,
        'price_per_seat': r.price_per_seat,
        'status': r.status,
        'recurring_days': r.recurring_days,
        'created_at': r.created_at.isoformat(),
        'cancellation_reason': r.cancellation_reason,
        'cancelled_by_admin_id': r.cancelled_by_admin_id,
        'cancelled_at': r.cancelled_at.isoformat() if r.cancelled_at else None,
        'cancelled_by_admin_name': r.cancelled_by_admin.name if r.cancelled_by_admin else None,
        'bookings_count': r.bookings.count(),
        'confirmed_bookings_count': r.bookings.filter_by(status='confirmed').count(),
        'pending_bookings_count': r.bookings.filter_by(status='pending').count()
    } for r in rides])
