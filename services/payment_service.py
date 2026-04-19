from models import db
from models.wallet import Wallet
from models.wallet_transaction import WalletTransaction

class PaymentService:
    @staticmethod
    def add_funds(user_id, amount, description=None):
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            wallet = Wallet(user_id=user_id, balance=0)
            db.session.add(wallet)
            db.session.flush()
        wallet.balance += amount
        tx = WalletTransaction(
            wallet_id=wallet.wallet_id,
            amount=amount,
            transaction_type='credit',
            description=description or f"Added ${amount}"
        )
        db.session.add(tx)
        db.session.commit()
        return wallet.balance
    
    @staticmethod
    def deduct_funds(user_id, amount, description=None):
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet or wallet.balance < amount:
            raise ValueError("Insufficient balance")
        wallet.balance -= amount
        tx = WalletTransaction(
            wallet_id=wallet.wallet_id,
            amount=amount,
            transaction_type='debit',
            description=description or f"Deducted ${amount}"
        )
        db.session.add(tx)
        db.session.commit()
        return wallet.balance