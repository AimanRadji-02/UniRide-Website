# controllers/booking_controller.py
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.booking_service import BookingService
from models.booking import Booking
from datetime import datetime, timedelta

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/my-bookings', methods=['GET'])
@login_required
def my_bookings_page():
    return render_template('bookings.html')

@booking_bp.route('/api/request', methods=['POST'])
@login_required
def request_booking():
    data = request.get_json()
    try:
        booking = BookingService.create_booking(
            ride_id=data['ride_id'],
            passenger_id=current_user.user_id,
            seats_requested=int(data['seats_requested'])
        )
        return jsonify({'message': 'Booking confirmed', 'booking_id': booking.booking_id, 'total_price': booking.total_price}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@booking_bp.route('/api/cancel', methods=['POST'])
@login_required
def cancel_booking():
    data = request.get_json()
    booking_id = data['booking_id']
    try:
        BookingService.cancel_booking(booking_id, current_user.user_id)
        return jsonify({'message': 'Booking cancelled'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@booking_bp.route('/api/my-bookings', methods=['GET'])
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(passenger_id=current_user.user_id).all()
    result = []
    for b in bookings:
        can_cancel = (b.status == 'confirmed' and 
                      b.ride.departure_datetime > datetime.utcnow() + timedelta(minutes=30))
        result.append({
            'booking_id': b.booking_id,
            'ride': {
                'origin': b.ride.origin,
                'destination': b.ride.destination,
                'departure_datetime': b.ride.departure_datetime.isoformat()
            },
            'seats_requested': b.seats_requested,
            'status': b.status,
            'total_price': b.total_price,
            'can_cancel': can_cancel
        })
    return jsonify(result), 200