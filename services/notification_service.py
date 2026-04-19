from models import db
from models.notification import Notification
from flask_socketio import emit

class NotificationService:
    @staticmethod
    def _create_notification(user_id, title, message):
        notif = Notification(user_id=user_id, title=title, message_body=message)
        db.session.add(notif)
        db.session.commit()
        # Real-time via socket
        from app import socketio
        socketio.emit('new_notification', {
            'title': title,
            'message': message,
            'created_at': notif.created_at.isoformat()
        }, room=f'user_{user_id}')
        return notif
    
    @staticmethod
    def send_booking_confirmation(booking):
        NotificationService._create_notification(
            booking.passenger_id,
            "Booking Confirmed",
            f"Your booking for ride {booking.ride_id} is confirmed."
        )
    
    @staticmethod
    def notify_driver_new_booking(booking):
        NotificationService._create_notification(
            booking.ride.driver_id,
            "New Booking",
            f"{booking.passenger.name} booked {booking.seats_requested} seat(s)."
        )
    
    @staticmethod
    def send_booking_cancellation(booking):
        NotificationService._create_notification(
            booking.passenger_id,
            "Booking Cancelled",
            f"Your booking for ride {booking.ride_id} has been cancelled."
        )
        NotificationService._create_notification(
            booking.ride.driver_id,
            "Booking Cancelled",
            f"{booking.passenger.name} cancelled their booking."
        )