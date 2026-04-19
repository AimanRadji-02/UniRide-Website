from models import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'
    booking_id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.ride_id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seats_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)