from models import db
from datetime import datetime

class Wallet(db.Model):
    __tablename__ = 'wallet'
    wallet_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = db.relationship('WalletTransaction', backref='wallet', lazy='dynamic')