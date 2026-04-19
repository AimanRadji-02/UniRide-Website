from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db
from models.rating import Rating
from models.booking import Booking
from utils.validators import validate_rating

rating_bp = Blueprint('rating', __name__)

@rating_bp.route('/rate/<int:ride_id>')
@login_required
def rate_ride_page(ride_id):
    # Verify user is passenger in that ride and ride is completed
    booking = Booking.query.filter_by(ride_id=ride_id, passenger_id=current_user.user_id, status='confirmed').first()
    if not booking:
        return "Unauthorized or ride not completed", 403
    if booking.ride.status != 'completed':
        return "Ride not completed yet", 400
    # Check if already rated
    existing = Rating.query.filter_by(ride_id=ride_id, reviewer_id=current_user.user_id).first()
    if existing:
        return "You already rated this ride", 400
    return render_template('rate_ride.html', ride_id=ride_id)

@rating_bp.route('/api/submit', methods=['POST'])
@login_required
def submit_rating():
    data = request.get_json()
    ride_id = data.get('ride_id')
    rating_value = data.get('rating_value')
    comment = data.get('comment', '')
    
    if not validate_rating(rating_value):
        return jsonify({'error': 'Rating must be 1-5'}), 400
    
    booking = Booking.query.filter_by(ride_id=ride_id, passenger_id=current_user.user_id, status='confirmed').first()
    if not booking or booking.ride.status != 'completed':
        return jsonify({'error': 'Not eligible to rate'}), 403
    
    existing = Rating.query.filter_by(ride_id=ride_id, reviewer_id=current_user.user_id).first()
    if existing:
        return jsonify({'error': 'Already rated'}), 400
    
    rating = Rating(
        ride_id=ride_id,
        reviewer_id=current_user.user_id,
        reviewee_id=booking.ride.driver_id,
        rating_value=rating_value,
        comment=comment
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({'message': 'Rating submitted'}), 201

@rating_bp.route('/api/user/<int:user_id>')
@login_required
def get_user_ratings(user_id):
    ratings = Rating.query.filter_by(reviewee_id=user_id).all()
    avg = sum(r.rating_value for r in ratings) / len(ratings) if ratings else 0
    return jsonify({
        'average_rating': round(avg, 2),
        'count': len(ratings),
        'ratings': [{'value': r.rating_value, 'comment': r.comment, 'created_at': r.created_at.isoformat()} for r in ratings]
    })