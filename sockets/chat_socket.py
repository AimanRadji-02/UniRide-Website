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