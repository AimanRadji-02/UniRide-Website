from models import db
from datetime import datetime

class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'
    transaction_id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.wallet_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # credit / debit
    description = db.Column(db.String(200))
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    related_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=True)