from models import db
from datetime import datetime

class Ride(db.Model):
    __tablename__ = 'rides'
    ride_id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    origin = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    price_per_seat = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    recurring_days = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin cancellation fields
    cancellation_reason = db.Column(db.Text)
    cancelled_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    bookings = db.relationship('Booking', backref='ride', lazy='dynamic')
    cancelled_by_admin = db.relationship('User', foreign_keys=[cancelled_by_admin_id])