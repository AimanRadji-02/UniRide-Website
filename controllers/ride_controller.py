# controllers/ride_controller.py
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.ride_service import RideService
from services.booking_service import BookingService
from services.notification_service import NotificationService
from utils.decorators import driver_required, passenger_required
from models import db
from models.ride import Ride
from models.booking import Booking
from datetime import datetime, timedelta

# Create blueprint FIRST
ride_bp = Blueprint('ride', __name__)

# HTML page routes
@ride_bp.route('/offer', methods=['GET'])
@login_required
@driver_required
def offer_ride_page():
    return render_template('offer_ride.html')

@ride_bp.route('/search', methods=['GET'])
@login_required
@passenger_required
def search_rides_page():
    return render_template('search_rides.html')

@ride_bp.route('/track/<int:ride_id>', methods=['GET'])
@login_required
def live_tracking_page(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    is_driver = (ride.driver_id == current_user.user_id)
    is_passenger = any(b.passenger_id == current_user.user_id and b.status == 'confirmed' 
                       for b in ride.bookings)
    if not (is_driver or is_passenger):
        return "Unauthorized", 403
    return render_template('live_tracking.html', ride=ride, is_driver=is_driver)

# API routes
@ride_bp.route('/api/create', methods=['POST'])
@login_required
@driver_required
def create_ride():
    data = request.get_json()
    try:
        ride = RideService.create_ride(
            driver_id=current_user.user_id,
            origin=data['origin'],
            destination=data['destination'],
            departure_datetime=datetime.fromisoformat(data['departure_datetime']),
            available_seats=int(data['available_seats']),
            price_per_seat=float(data['price_per_seat']),
            recurring_days=data.get('recurring_days')
        )
        return jsonify({'message': 'Ride created', 'ride_id': ride.ride_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ride_bp.route('/api/search', methods=['GET'])
@login_required
def search_rides():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date_str = request.args.get('date')
    date = datetime.fromisoformat(date_str) if date_str else None
    rides = RideService.search_rides(origin, destination, date)
    return jsonify([{
        'ride_id': r.ride_id,
        'origin': r.origin,
        'destination': r.destination,
        'departure_datetime': r.departure_datetime.isoformat(),
        'available_seats': r.available_seats,
        'price_per_seat': r.price_per_seat,
        'driver_name': r.driver.name
    } for r in rides]), 200

@ride_bp.route('/api/<int:ride_id>', methods=['GET'])
@login_required
def get_ride(ride_id):
    ride = Ride.query.get(ride_id)
    if not ride:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'ride_id': ride.ride_id,
        'origin': ride.origin,
        'destination': ride.destination,
        'departure_datetime': ride.departure_datetime.isoformat(),
        'available_seats': ride.available_seats,
        'price_per_seat': ride.price_per_seat,
        'status': ride.status
    }), 200

@ride_bp.route('/api/<int:ride_id>/cancel', methods=['POST'])
@login_required
@driver_required
def cancel_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    if ride.status != 'active':
        return jsonify({'error': 'Ride already cancelled/completed'}), 400
    # Cancel all confirmed bookings and refund if applicable
    for booking in ride.bookings.filter_by(status='confirmed'):
        BookingService.cancel_booking(booking.booking_id, current_user.user_id)
    ride.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': 'Ride cancelled'}), 200

@ride_bp.route('/api/<int:ride_id>/complete', methods=['POST'])
@login_required
@driver_required
def complete_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    if ride.status != 'active':
        return jsonify({'error': 'Ride not active'}), 400
    ride.status = 'completed'
    db.session.commit()
    # Notify passengers to rate
    for booking in ride.bookings.filter_by(status='confirmed'):
        NotificationService._create_notification(
            booking.passenger_id,
            "Ride Completed",
            f"Please rate your ride from {ride.origin} to {ride.destination}"
        )
    return jsonify({'message': 'Ride marked as completed'}), 200