from models import db
from models.ride import Ride
from datetime import datetime

class RideService:
    @staticmethod
    def create_ride(driver_id, origin, destination, departure_datetime, available_seats, price_per_seat, recurring_days=None):
        if departure_datetime <= datetime.now():
            raise ValueError("Departure must be in future")
        if available_seats <= 0:
            raise ValueError("At least one seat required")
        ride = Ride(
            driver_id=driver_id,
            origin=origin,
            destination=destination,
            departure_datetime=departure_datetime,
            available_seats=available_seats,
            price_per_seat=price_per_seat,
            recurring_days=recurring_days,
            status='scheduled'  # Explicitly set status for new rides
        )
        db.session.add(ride)
        db.session.commit()
        return ride
    
    @staticmethod
    def search_rides(origin=None, destination=None, date=None):
        # FIXED: Use correct status values for searchable rides
        query = Ride.query.filter(
            Ride.status.in_(['scheduled', 'ongoing'])
        ).filter(Ride.available_seats > 0)
        
        # Only show future rides
        query = query.filter(Ride.departure_datetime >= datetime.now())
        
        if origin:
            query = query.filter(Ride.origin.ilike(f'%{origin}%'))
        if destination:
            query = query.filter(Ride.destination.ilike(f'%{destination}%'))
        if date:
            query = query.filter(db.func.date(Ride.departure_datetime) == date)
        return query.order_by(Ride.departure_datetime).all()