from flask_socketio import emit, join_room
from flask_login import current_user
from models import db
from models.message import Message

def register_chat_handlers(socketio):
    @socketio.on('join_chat_room')
    def handle_join_chat(data):
        ride_id = data.get('ride_id')
        if ride_id and current_user.is_authenticated:
            room = f'chat_ride_{ride_id}'
            join_room(room)
            emit('joined_chat', {'ride_id': ride_id, 'user': current_user.name})
    
    @socketio.on('join_private_chat')
    def handle_join_private_chat(data):
        other_user_id = data.get('other_user_id')
        if other_user_id and current_user.is_authenticated:
            # Create a private room for two users
            room = f'private_{min(current_user.user_id, other_user_id)}_{max(current_user.user_id, other_user_id)}'
            join_room(room)
            emit('joined_private_chat', {'other_user_id': other_user_id})
    
    @socketio.on('send_chat_message')
    def handle_chat_message(data):
        if not current_user.is_authenticated:
            return
        ride_id = data.get('ride_id')
        content = data.get('content')
        if not ride_id or not content:
            return
        msg = Message(
            sender_id=current_user.user_id,
            ride_id=ride_id,
            content=content
        )
        db.session.add(msg)
        db.session.commit()
        room = f'chat_ride_{ride_id}'
        emit('new_chat_message', {
            'sender': current_user.name,
            'content': content,
            'timestamp': msg.sent_at.isoformat()
        }, room=room)
    
    @socketio.on('send_private_message')
    def handle_private_message(data):
        if not current_user.is_authenticated:
            return
        receiver_id = data.get('receiver_id')
        ride_id = data.get('ride_id')
        content = data.get('content')
        if not receiver_id or not content:
            return
        
        # Create message in database
        msg = Message(
            sender_id=current_user.user_id,
            receiver_id=receiver_id,
            ride_id=ride_id,
            content=content
        )
        db.session.add(msg)
        db.session.commit()
        
        # Create private room for two users
        room = f'private_{min(current_user.user_id, receiver_id)}_{max(current_user.user_id, receiver_id)}'
        
        # Emit to both users in the private room
        emit('new_message', {
            'sender_id': current_user.user_id,
            'receiver_id': receiver_id,
            'content': content,
            'sent_at': msg.sent_at.isoformat(),
            'is_read': False
        }, room=room)