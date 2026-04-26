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
    booking = Booking.query.filter_by(ride_id=ride_id, passenger_id=current_user.user_id, status='confirmed').first()
    if not booking:
        return "Unauthorized or ride not completed", 403
    if booking.ride.status != 'completed':
        return "Ride not completed yet", 400
    existing = Rating.query.filter_by(ride_id=ride_id, reviewer_id=current_user.user_id).first()
    if existing:
        return "You already rated this ride", 400
    return render_template('rate_ride.html', ride_id=ride_id)

@rating_bp.route('/submit', methods=['POST'])
@login_required
def submit_rating():
    """Submit rating - supports passenger->driver and driver->passenger"""
    data = request.get_json()
    ride_id = data.get('ride_id')
    reviewee_id = data.get('reviewee_id')  # Who is being rated
    rating_value = data.get('rating_value')
    comment = data.get('comment', '')

    # Validate rating value
    if not rating_value or not (1 <= rating_value <= 5):
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

    # Get the ride
    from models.ride import Ride
    ride = Ride.query.get_or_404(ride_id)
    
    # Validation: Ride must be completed
    if ride.status != 'completed':
        return jsonify({'error': 'Can only rate completed rides'}), 400
    
    # Validation: User must have participated in the ride
    if current_user.user_id != ride.driver_id:
        # User is a passenger - check if they had a confirmed booking
        booking = Booking.query.filter_by(
            ride_id=ride_id, 
            passenger_id=current_user.user_id, 
            status='confirmed'
        ).first()
        if not booking:
            return jsonify({'error': 'You did not participate in this ride'}), 403
    else:
        # User is the driver - check if the reviewee was a confirmed passenger
        passenger_booking = Booking.query.filter_by(
            ride_id=ride_id, 
            passenger_id=reviewee_id, 
            status='confirmed'
        ).first()
        if not passenger_booking:
            return jsonify({'error': 'This person was not a passenger in your ride'}), 403

    # Validation: Cannot rate yourself
    if current_user.user_id == reviewee_id:
        return jsonify({'error': 'Cannot rate yourself'}), 400
    
    # Validation: Check if already rated this person for this ride
    existing = Rating.query.filter_by(
        ride_id=ride_id, 
        reviewer_id=current_user.user_id, 
        reviewee_id=reviewee_id
    ).first()
    if existing:
        return jsonify({'error': 'You have already rated this person for this ride'}), 400

    # Create the rating
    rating = Rating(
        ride_id=ride_id,
        reviewer_id=current_user.user_id,
        reviewee_id=reviewee_id,
        rating_value=rating_value,
        comment=comment
    )
    db.session.add(rating)
    db.session.commit()
    
    return jsonify({
        'message': 'Rating submitted successfully',
        'rating_id': rating.rating_id
    }), 201

@rating_bp.route('/check-eligibility/<int:ride_id>')
@login_required
def check_rating_eligibility(ride_id):
    """Check if current user can rate and who they can rate for this ride"""
    from models.ride import Ride
    ride = Ride.query.get_or_404(ride_id)
    
    # Ride must be completed
    if ride.status != 'completed':
        return jsonify({
            'eligible': False,
            'reason': 'Ride not completed yet'
        }), 400
    
    eligible_to_rate = []
    
    if current_user.user_id == ride.driver_id:
        # Driver can rate confirmed passengers
        confirmed_bookings = Booking.query.filter_by(
            ride_id=ride_id, 
            status='confirmed'
        ).all()
        
        for booking in confirmed_bookings:
            # Check if already rated this passenger
            existing = Rating.query.filter_by(
                ride_id=ride_id,
                reviewer_id=current_user.user_id,
                reviewee_id=booking.passenger_id
            ).first()
            
            if not existing:
                eligible_to_rate.append({
                    'user_id': booking.passenger_id,
                    'name': booking.passenger.name,
                    'role': 'passenger'
                })
    else:
        # Passenger can rate driver
        booking = Booking.query.filter_by(
            ride_id=ride_id, 
            passenger_id=current_user.user_id, 
            status='confirmed'
        ).first()
        
        if booking:
            # Check if already rated driver
            existing = Rating.query.filter_by(
                ride_id=ride_id,
                reviewer_id=current_user.user_id,
                reviewee_id=ride.driver_id
            ).first()
            
            if not existing:
                eligible_to_rate.append({
                    'user_id': ride.driver_id,
                    'name': ride.driver.name,
                    'role': 'driver'
                })
    
    return jsonify({
        'eligible': len(eligible_to_rate) > 0,
        'can_rate': eligible_to_rate
    })

@rating_bp.route('/user-ratings/<int:user_id>', methods=['GET'])
@login_required
def get_user_ratings(user_id):
    """Get all ratings for a specific user (what others rated them)"""
    try:
        from models.user import User
        
        # Check if user exists
        user = User.query.get_or_404(user_id)
        
        # Get ratings where this user is the reviewee (what others rated them)
        ratings = Rating.query.filter_by(reviewee_id=user_id).order_by(Rating.created_at.desc()).all()
        
        ratings_list = []
        for rating in ratings:
            ratings_list.append({
                'rating_id': rating.rating_id,
                'rating_value': rating.rating_value,
                'comment': rating.comment,
                'created_at': rating.created_at.isoformat(),
                'reviewer_name': rating.reviewer.name if rating.reviewer else 'Anonymous',
                'ride_origin': rating.ride.origin,
                'ride_destination': rating.ride.destination,
                'ride_date': rating.ride.departure_datetime.isoformat()
            })
        
        # Calculate average rating
        total_ratings = len(ratings_list)
        avg_rating = sum(r['rating_value'] for r in ratings_list) / total_ratings if total_ratings > 0 else 0
        
        return jsonify({
            'user_id': user_id,
            'user_name': user.name,
            'total_ratings': total_ratings,
            'average_rating': round(avg_rating, 2),
            'ratings': ratings_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
