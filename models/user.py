from models import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    vehicle_details = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    rides_as_driver = db.relationship('Ride', backref='driver', foreign_keys='Ride.driver_id')
    bookings = db.relationship('Booking', backref='passenger', foreign_keys='Booking.passenger_id')
    wallet = db.relationship('Wallet', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def get_id(self):
        return str(self.user_id)
    def is_admin(self):
        return self.role == 'admin'
    def is_driver(self):
        return self.role == 'driver'
    def is_passenger(self):
        return self.role == 'passenger'