from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models.message import Message
from models.user import User
from models.ride import Ride
from models import db
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/my-chat', methods=['GET'])
@login_required
def my_chat_page():
    return render_template('my_chat.html')

@chat_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get all conversations for the current user"""
    try:
        # Get all messages where user is either sender or receiver
        messages = Message.query.filter(
            (Message.sender_id == current_user.user_id) | 
            (Message.receiver_id == current_user.user_id)
        ).order_by(Message.sent_at.desc()).all()
        
        # Group by conversation partner
        conversations = {}
        for msg in messages:
            # Determine the other user in the conversation
            other_user_id = msg.receiver_id if msg.sender_id == current_user.user_id else msg.sender_id
            
            if other_user_id not in conversations:
                other_user = User.query.get(other_user_id)
                conversations[other_user_id] = {
                    'user_id': other_user_id,
                    'name': other_user.name,
                    'last_message': msg.content,
                    'last_message_time': msg.sent_at.isoformat(),
                    'unread_count': 0
                }
            
            # Count unread messages (messages sent to current user)
            if msg.receiver_id == current_user.user_id and not msg.is_read:
                conversations[other_user_id]['unread_count'] += 1
        
        # Convert to list and sort by last message time
        conversation_list = list(conversations.values())
        conversation_list.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        return jsonify(conversation_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get total unread message count for the current user"""
    try:
        unread_count = Message.query.filter(
            (Message.receiver_id == current_user.user_id) &
            (Message.is_read == False)
        ).count()
        
        return jsonify({'unread_count': unread_count}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/conversation/<int:user_id>', methods=['GET'])
@login_required
def get_conversation(user_id):
    """Get all messages between current user and specified user"""
    try:
        # Get all messages between the two users
        messages = Message.query.filter(
            ((Message.sender_id == current_user.user_id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user.user_id))
        ).order_by(Message.sent_at.asc()).all()
        
        # Mark messages as read
        Message.query.filter(
            (Message.sender_id == user_id) & 
            (Message.receiver_id == current_user.user_id) &
            (Message.is_read == False)
        ).update({'is_read': True})
        db.session.commit()
        
        # Get other user info
        other_user = User.query.get(user_id)
        
        message_list = []
        for msg in messages:
            message_list.append({
                'message_id': msg.message_id,
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'content': msg.content,
                'sent_at': msg.sent_at.isoformat(),
                'is_read': msg.is_read,
                'sender_name': msg.sender.name if msg.sender else 'Unknown',
                'ride_id': msg.ride_id
            })
        
        return jsonify({
            'messages': message_list,
            'other_user': {
                'user_id': other_user.user_id,
                'name': other_user.name,
                'email': other_user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to another user"""
    data = request.get_json(silent=True) or {}
    try:
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        ride_id = data.get('ride_id')
        
        if not receiver_id or not content:
            return jsonify({'error': 'Receiver ID and content are required'}), 400
        
        # Create message
        message = Message(
            sender_id=current_user.user_id,
            receiver_id=receiver_id,
            content=content,
            ride_id=ride_id
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent',
            'message_id': message.message_id,
            'sent_at': message.sent_at.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/mark-read/<int:user_id>', methods=['POST'])
@login_required
def mark_conversation_read(user_id):
    """Mark all messages from a specific user as read"""
    try:
        Message.query.filter(
            (Message.sender_id == user_id) & 
            (Message.receiver_id == current_user.user_id) &
            (Message.is_read == False)
        ).update({'is_read': True})
        db.session.commit()
        
        return jsonify({'message': 'Messages marked as read'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
