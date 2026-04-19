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

# ... rest as provided