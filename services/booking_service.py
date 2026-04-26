# services/booking_service.py
from models import db
from models.ride import Ride
from models.booking import Booking
from models.wallet import Wallet
from services.payment_service import PaymentService
from services.notification_service import NotificationService
from datetime import datetime, timedelta

class BookingService:
    @staticmethod
    def create_booking(ride_id, passenger_id, seats_requested):
        if seats_requested is None or int(seats_requested) <= 0:
            raise ValueError("Seats requested must be at least 1")
        ride = Ride.query.get(ride_id)
        if not ride or ride.status not in ['scheduled', 'ongoing']:
            raise ValueError("Ride not available")
        if ride.departure_datetime <= datetime.now():
            raise ValueError("Ride already departed")
        if ride.available_seats < seats_requested:
            raise ValueError(f"Only {ride.available_seats} seats left")
        if ride.driver_id == passenger_id:
            raise ValueError("Driver cannot book own ride")
        
        total_price = ride.price_per_seat * seats_requested
        wallet = Wallet.query.filter_by(user_id=passenger_id).first()
        if not wallet or wallet.balance < total_price:
            raise ValueError("Insufficient balance")
        
        # Deduct payment
        PaymentService.deduct_funds(passenger_id, total_price, f"Booking for ride {ride_id}")
        
        booking = Booking(
            ride_id=ride_id,
            passenger_id=passenger_id,
            seats_requested=seats_requested,
            total_price=total_price,
            status='confirmed'
        )
        db.session.add(booking)
        ride.available_seats -= seats_requested
        db.session.commit()
        
        # Credit driver
        PaymentService.add_funds(ride.driver_id, total_price, f"Earning from ride {ride_id}")
        
        NotificationService.send_booking_confirmation(booking)
        NotificationService.notify_driver_new_booking(booking)
        return booking
    
    @staticmethod
    def cancel_booking(booking_id, user_id):
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        if booking.passenger_id != user_id and booking.ride.driver_id != user_id:
            raise PermissionError("Not authorized")
        if booking.status != 'confirmed':
            raise ValueError("Booking cannot be cancelled")
        
        now = datetime.now()
        time_left = booking.ride.departure_datetime - now
        refund_allowed = time_left > timedelta(minutes=30)
        
        if refund_allowed:
            # Refund passenger, claw back from driver
            PaymentService.add_funds(booking.passenger_id, booking.total_price, f"Refund for cancelled booking {booking_id}")
            PaymentService.deduct_funds(booking.ride.driver_id, booking.total_price, f"Clawback for cancelled booking {booking_id}")
            booking.ride.available_seats += booking.seats_requested
        else:
            # No refund, but restore seats
            booking.ride.available_seats += booking.seats_requested
        
        booking.status = 'cancelled'
        db.session.commit()
        NotificationService.send_booking_cancellation(booking)
        return booking