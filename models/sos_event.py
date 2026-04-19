from models import db
from datetime import datetime

class SOSEvent(db.Model):
    __tablename__ = 'sos_events'
    sos_id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.ride_id'), nullable=False)
    triggered_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    gps_location = db.Column(db.String(200), nullable=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')