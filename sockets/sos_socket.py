from flask_socketio import emit
from flask_login import current_user
from models import db
from models.sos_event import SOSEvent

def register_sos_handlers(socketio):
    @socketio.on('trigger_sos')
    def handle_sos(data):
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return
        ride_id = data.get('ride_id')
        gps = data.get('gps_location', 'Unknown')
        if not ride_id:
            return
        sos = SOSEvent(
            ride_id=ride_id,
            triggered_by=current_user.user_id,
            gps_location=gps,
            status='active'
        )
        db.session.add(sos)
        db.session.commit()
        emit('sos_triggered', {
            'user': current_user.name,
            'location': gps,
            'time': sos.triggered_at.isoformat()
        }, room=f'ride_tracking_{ride_id}', broadcast=True)