from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.message import Message

message_bp = Blueprint('message', __name__)

@message_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    ride_id = data.get('ride_id')
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Message content required'}), 400
    msg = Message(
        sender_id=current_user.user_id,
        receiver_id=receiver_id,
        ride_id=ride_id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'message': 'Sent', 'message_id': msg.message_id}), 201

@message_bp.route('/conversation/<int:other_user_id>')
@login_required
def get_conversation(other_user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.user_id))
    ).order_by(Message.sent_at).all()
    return jsonify([{
        'id': m.message_id,
        'sender_id': m.sender_id,
        'content': m.content,
        'sent_at': m.sent_at.isoformat(),
        'is_read': m.is_read
    } for m in messages])
