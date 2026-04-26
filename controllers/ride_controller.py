from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from services.ride_service import RideService
from services.booking_service import BookingService
from services.notification_service import NotificationService
from utils.decorators import driver_required, passenger_required, driver_page_required, passenger_page_required, role_required
from models import db
from models.ride import Ride
from models.booking import Booking
from models.user import User
from datetime import datetime, timedelta
 
ride_bp = Blueprint('ride', __name__)
 
# HTML page routes
@ride_bp.route('/offer', methods=['GET'])
@login_required
@driver_page_required
def offer_ride_page():
    return render_template('offer_ride.html')
 
@ride_bp.route('/search', methods=['GET'])
@login_required
@passenger_page_required
def search_rides_page():
    return render_template('search_rides.html')

@ride_bp.route('/dashboard', methods=['GET'])
@login_required
@driver_page_required
def driver_dashboard():
    return render_template('driver_dashboard.html')
 
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
@ride_bp.route('/create', methods=['POST'])
@driver_required
def create_ride():
    # For JSON APIs, rely on `driver_required` to return JSON 401/403.
    # `login_required` would redirect (HTML), which breaks fetch().json().
    data = request.get_json(silent=True) or {}
    try:
        missing = [k for k in ('origin', 'destination', 'departure_datetime', 'available_seats', 'price_per_seat') if k not in data]
        if missing:
            return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400
 
        origin = current_app.config.get('PROTOTYPE_FIXED_ORIGIN') or data['origin']
        destination = current_app.config.get('PROTOTYPE_FIXED_DESTINATION') or data['destination']

        ride = RideService.create_ride(
            driver_id=current_user.user_id,
            origin=origin,
            destination=destination,
            departure_datetime=datetime.fromisoformat(data['departure_datetime']),
            available_seats=int(data['available_seats']),
            price_per_seat=float(data['price_per_seat']),
            recurring_days=data.get('recurring_days')
        )
        return jsonify({'message': 'Ride created', 'ride_id': ride.ride_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
 
@ride_bp.route('/search-results', methods=['GET'])
@login_required  # FIX: role_required excluded drivers; any logged-in user can view available rides
def search_rides():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date_str = request.args.get('date')
    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
        except ValueError:
            date = None
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
 
@ride_bp.route('/<int:ride_id>', methods=['GET'])
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
 
@ride_bp.route('/<int:ride_id>/cancel', methods=['POST'])
@driver_required
def cancel_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    if ride.status not in ['scheduled', 'ongoing']:
        return jsonify({'error': 'Ride already cancelled/completed'}), 400
    # FIX: ride.bookings is a list (relationship), not a query — use a generator filter
    confirmed_bookings = [b for b in ride.bookings if b.status == 'confirmed']
    for booking in confirmed_bookings:
        BookingService.cancel_booking(booking.booking_id, current_user.user_id)
    ride.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': 'Ride cancelled'}), 200
 
@ride_bp.route('/<int:ride_id>/complete', methods=['POST'])
@driver_required
def complete_ride(ride_id):
    """Mark ride as completed - only driver can do this"""
    ride = Ride.query.get_or_404(ride_id)
    
    # Validation: Only the driver can complete the ride
    if ride.driver_id != current_user.user_id:
        return jsonify({'error': 'Only the driver can mark this ride as completed'}), 403
    
    # Validation: Ride must be in scheduled or ongoing status
    if ride.status not in ['scheduled', 'ongoing']:
        return jsonify({'error': 'Ride cannot be completed in current status'}), 400
    
    # Update ride status to completed
    ride.status = 'completed'
    
    # Get confirmed bookings for notifications
    confirmed_bookings = [b for b in ride.bookings if b.status == 'confirmed']
    
    # Commit the status change
    db.session.commit()
    
    # Send notifications to all confirmed passengers
    for booking in confirmed_bookings:
        NotificationService._create_notification(
            booking.passenger_id,
            "Ride Completed - Rate Your Experience",
            f"Your ride from {ride.origin} to {ride.destination} has been completed. Please rate your experience!"
        )
    
    return jsonify({
        'message': 'Ride marked as completed successfully',
        'ride_id': ride_id,
        'passengers_notified': len(confirmed_bookings)
    }), 200

@ride_bp.route('/<int:ride_id>/admin-cancel', methods=['POST'])
@role_required('admin')
def admin_cancel_ride(ride_id):
    """Admin endpoint to cancel any ride for inappropriate use"""
    ride = Ride.query.get_or_404(ride_id)
    
    if ride.status not in ['scheduled', 'ongoing']:
        return jsonify({'error': 'Ride already cancelled or completed'}), 400
    
    data = request.get_json(silent=True) or {}
    reason = data.get('reason', 'Inappropriate use - Admin action')
    
    # Get all bookings for this ride
    confirmed_bookings = [b for b in ride.bookings if b.status == 'confirmed']
    pending_bookings = [b for b in ride.bookings if b.status == 'pending']
    
    # Cancel all bookings
    all_bookings = confirmed_bookings + pending_bookings
    for booking in all_bookings:
        BookingService.cancel_booking(booking.booking_id, current_user.user_id)
    
    # Mark ride as cancelled
    ride.status = 'cancelled'
    ride.cancellation_reason = reason
    ride.cancelled_by_admin_id = current_user.user_id
    ride.cancelled_at = datetime.utcnow()
    
    db.session.commit()
    
    # Notify driver
    NotificationService._create_notification(
        ride.driver_id,
        "Ride Cancelled by Admin",
        f"Your ride from {ride.origin} to {ride.destination} has been cancelled by an administrator. Reason: {reason}"
    )
    
    # Notify all passengers
    for booking in confirmed_bookings:
        NotificationService._create_notification(
            booking.passenger_id,
            "Ride Cancelled by Admin",
            f"The ride from {ride.origin} to {ride.destination} has been cancelled by an administrator. Reason: {reason}"
        )
    
    return jsonify({
        'message': 'Ride cancelled successfully',
        'cancelled_bookings': len(all_bookings),
        'reason': reason
    }), 200

@ride_bp.route('/driver_rides', methods=['GET'])
@driver_required
def get_driver_rides():
    rides = Ride.query.filter_by(driver_id=current_user.user_id).order_by(Ride.departure_datetime).all()
    return jsonify([{
        'ride_id': r.ride_id,
        'origin': r.origin,
        'destination': r.destination,
        'departure_datetime': r.departure_datetime.isoformat(),
        'available_seats': r.available_seats,
        'price_per_seat': r.price_per_seat,
        'status': r.status
    } for r in rides]), 200

@ride_bp.route('/<int:ride_id>/passengers', methods=['GET'])
@driver_required
def get_ride_passengers(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    passengers = db.session.query(
        User.user_id.label('passenger_id'),
        User.name,
        User.phone,
        Booking.seats_requested,
        Booking.status.label('booking_status')
    ).join(Booking, User.user_id == Booking.passenger_id)\
     .filter(Booking.ride_id == ride_id)\
     .filter(Booking.status.in_(['confirmed', 'pending']))\
     .all()
    
    return jsonify([{
        'passenger_id': p.passenger_id,
        'name': p.name,
        'phone': p.phone,
        'seats_requested': p.seats_requested,
        'booking_status': p.booking_status
    } for p in passengers]), 200