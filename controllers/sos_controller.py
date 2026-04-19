from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db
from models.sos_event import SOSEvent

sos_bp = Blueprint('sos', __name__)

@sos_bp.route('/alerts')
@login_required
def alerts_page():
    return render_template('sos_alerts.html')

@sos_bp.route('/api/my-alerts')
@login_required
def my_alerts():
    sos_events = SOSEvent.query.filter_by(triggered_by=current_user.user_id).order_by(SOSEvent.triggered_at.desc()).all()
    return jsonify([{
        'sos_id': s.sos_id,
        'ride_id': s.ride_id,
        'gps_location': s.gps_location,
        'triggered_at': s.triggered_at.isoformat(),
        'status': s.status
    } for s in sos_events])

@sos_bp.route('/api/active-for-ride/<int:ride_id>')
@login_required
def active_for_ride(ride_id):
    active = SOSEvent.query.filter_by(ride_id=ride_id, status='active').first()
    if active:
        return jsonify({'active': True, 'sos_id': active.sos_id, 'location': active.gps_location})
    return jsonify({'active': False})