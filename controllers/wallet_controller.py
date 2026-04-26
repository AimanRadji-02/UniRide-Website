from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.payment_service import PaymentService
from models.wallet import Wallet
from models.wallet_transaction import WalletTransaction

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/', methods=['GET'])
@login_required
def wallet_page():
    return render_template('wallet.html')

@wallet_bp.route('/balance', methods=['GET'])
@login_required
def get_balance():
    wallet = Wallet.query.filter_by(user_id=current_user.user_id).first()
    balance = wallet.balance if wallet else 0.0
    return jsonify({'balance': balance}), 200

@wallet_bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    wallet = Wallet.query.filter_by(user_id=current_user.user_id).first()
    if not wallet:
        return jsonify([]), 200
    txs = WalletTransaction.query.filter_by(wallet_id=wallet.wallet_id).order_by(WalletTransaction.transaction_date.desc()).all()
    return jsonify([{
        'transaction_id': t.transaction_id,
        'amount': t.amount,
        'type': t.transaction_type,
        'description': t.description or '',
        'date': t.transaction_date.isoformat()
    } for t in txs]), 200

@wallet_bp.route('/add-funds', methods=['POST'])
@login_required
def add_funds():
    data = request.get_json()
    amount = data.get('amount', 0)
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    new_balance = PaymentService.add_funds(current_user.user_id, amount, 'Wallet top-up')
    return jsonify({'message': 'Funds added', 'balance': new_balance}), 200
