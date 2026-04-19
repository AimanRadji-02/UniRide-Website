from flask_socketio import emit, join_room
from flask_login import current_user
from functools import wraps

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            emit('error', {'message': 'Auth required'})
            return
        return f(*args, **kwargs)
    return wrapped

def register_tracking_handlers(socketio):
    @socketio.on('join_ride_tracking')
    @authenticated_only
    def handle_join(data):
        ride_id = data.get('ride_id')
        if ride_id:
            join_room(f'ride_tracking_{ride_id}')
            emit('tracking_joined', {'ride_id': ride_id})
    
    @socketio.on('update_location')
    @authenticated_only
    def handle_location(data):
        ride_id = data.get('ride_id')
        lat = data.get('latitude')
        lng = data.get('longitude')
        if ride_id and lat and lng:
            emit('location_updated', {'latitude': lat, 'longitude': lng}, 
                 room=f'ride_tracking_{ride_id}', include_self=False)