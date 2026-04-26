from models import db
from datetime import datetime

class Rating(db.Model):
    __tablename__ = 'ratings'
    rating_id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.ride_id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating_value = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ride = db.relationship('Ride', backref='ratings')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    reviewee = db.relationship('User', foreign_keys=[reviewee_id])
    
    __table_args__ = (db.UniqueConstraint('ride_id', 'reviewer_id', 'reviewee_id', name='unique_rating'),)