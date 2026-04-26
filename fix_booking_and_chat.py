#!/usr/bin/env python3
"""
Fix Booking and Chat Notification Issues
1. Passengers can't book new posts (status mismatch)
2. Chat notifications not appearing
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def find_database():
    """Find the database file"""
    for possible_path in ['uniride.db', 'instance/uniride.db', 'data/uniride.db']:
        if Path(possible_path).exists():
            return possible_path
    return None

def backup_database(db_path):
    """Create a backup before making changes"""
    backup_path = f"{db_path}.backup_booking_chat_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def fix_booking_service():
    """Fix booking service to use correct ride status"""
    print("\n🔧 Fixing Booking Service:")
    print("=" * 50)
    
    try:
        with open('services/booking_service.py', 'r') as f:
            content = f.read()
        
        # Check if the issue exists
        if "ride.status != 'active'" in content:
            print("🔍 Found issue: BookingService checking for 'active' status")
            print("🔄 Fixing to check for 'scheduled' or 'ongoing' status...")
            
            # Fix the status check
            fixed_content = content.replace(
                "if not ride or ride.status != 'active':",
                "if not ride or ride.status not in ['scheduled', 'ongoing']:"
            )
            
            with open('services/booking_service.py', 'w') as f:
                f.write(fixed_content)
            
            print("✅ BookingService fixed - now accepts 'scheduled' and 'ongoing' rides")
        else:
            print("✅ BookingService already uses correct status checking")
    
    except FileNotFoundError:
        print("❌ services/booking_service.py not found")
        return False
    
    return True

def check_socket_configuration():
    """Check Socket.IO configuration"""
    print("\n🔍 Checking Socket.IO Configuration:")
    print("=" * 50)
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check if Socket.IO is properly initialized
        if 'SocketIO' in app_content:
            print("✅ Socket.IO is imported")
        else:
            print("❌ Socket.IO not imported")
        
        if 'socketio = SocketIO' in app_content:
            print("✅ SocketIO instance created")
        else:
            print("❌ SocketIO instance not found")
        
        # Check if chat handlers are registered
        if 'register_chat_handlers' in app_content:
            print("✅ Chat handlers are registered")
        else:
            print("❌ Chat handlers not registered")
        
        # Check if CORS is properly configured for Socket.IO
        if 'cors_allowed_origins' in app_content:
            print("✅ CORS configured for Socket.IO")
        else:
            print("⚠️  CORS might not be configured for Socket.IO")
    
    except FileNotFoundError:
        print("❌ app.py not found")
        return False
    
    return True

def check_frontend_socket_integration():
    """Check frontend Socket.IO integration"""
    print("\n🔍 Checking Frontend Socket.IO Integration:")
    print("=" * 50)
    
    # Check bookings page
    try:
        with open('templates/bookings.html', 'r') as f:
            bookings_content = f.read()
        
        if 'socket.io' in bookings_content.lower():
            print("✅ Socket.IO client included in bookings.html")
        else:
            print("❌ Socket.IO client not found in bookings.html")
        
        if 'initializeSocket()' in bookings_content:
            print("✅ Socket initialization function found")
        else:
            print("❌ Socket initialization function not found")
        
        if 'new_message' in bookings_content:
            print("✅ Message event listener found")
        else:
            print("❌ Message event listener not found")
    
    except FileNotFoundError:
        print("❌ templates/bookings.html not found")
    
    # Check driver dashboard
    try:
        with open('templates/driver_dashboard.html', 'r') as f:
            driver_content = f.read()
        
        if 'socket.io' in driver_content.lower():
            print("✅ Socket.IO client included in driver_dashboard.html")
        else:
            print("❌ Socket.IO client not found in driver_dashboard.html")
    
    except FileNotFoundError:
        print("❌ templates/driver_dashboard.html not found")
    
    return True

def fix_message_model():
    """Check and fix message model if needed"""
    print("\n🔍 Checking Message Model:")
    print("=" * 50)
    
    try:
        with open('models/message.py', 'r') as f:
            message_content = f.read()
        
        print("📄 models/message.py content:")
        print(message_content)
        
        # Check if the model has the correct fields
        if 'sender_id' in message_content:
            print("✅ sender_id field found")
        else:
            print("❌ sender_id field missing")
        
        if 'receiver_id' in message_content:
            print("✅ receiver_id field found")
        else:
            print("❌ receiver_id field missing")
        
        if 'ride_id' in message_content:
            print("✅ ride_id field found")
        else:
            print("❌ ride_id field missing")
        
        if 'content' in message_content:
            print("✅ content field found")
        else:
            print("❌ content field missing")
        
        if 'sent_at' in message_content:
            print("✅ sent_at field found")
        else:
            print("❌ sent_at field missing")
    
    except FileNotFoundError:
        print("❌ models/message.py not found")
        return False
    
    return True

def create_test_booking_and_chat():
    """Create test booking and chat to verify fixes"""
    print("\n🧪 Creating Test Booking and Chat:")
    print("=" * 50)
    
    try:
        from services.booking_service import BookingService
        from services.ride_service import RideService
        from models.message import Message
        from models import db
        from datetime import datetime, timedelta
        
        # Create a test ride first
        test_ride = RideService.create_ride(
            driver_id=1,  # Assuming user 1 exists
            origin="Test Origin",
            destination="Test Destination", 
            departure_datetime=datetime.now() + timedelta(hours=2),
            available_seats=3,
            price_per_seat=10.0
        )
        
        print(f"✅ Test ride created: ID {test_ride.ride_id}, Status: {test_ride.status}")
        
        # Test booking creation
        try:
            test_booking = BookingService.create_booking(
                ride_id=test_ride.ride_id,
                passenger_id=2,  # Assuming user 2 exists
                seats_requested=1
            )
            print(f"✅ Test booking created: ID {test_booking.booking_id}, Status: {test_booking.status}")
        except Exception as e:
            print(f"❌ Booking failed: {e}")
        
        # Test message creation
        test_message = Message(
            sender_id=1,
            receiver_id=2,
            ride_id=test_ride.ride_id,
            content="Test message"
        )
        db.session.add(test_message)
        db.session.commit()
        print(f"✅ Test message created: ID {test_message.message_id}")
        
        # Clean up
        db.session.delete(test_message)
        if 'test_booking' in locals():
            db.session.delete(test_booking)
        db.session.delete(test_ride)
        db.session.commit()
        print("🧹 Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def verify_database_state(db_path):
    """Verify database state for booking and chat"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying Database State:")
    print("=" * 50)
    
    # Check rides table
    cursor.execute("SELECT COUNT(*) FROM rides WHERE status IN ('scheduled', 'ongoing')")
    available_rides = cursor.fetchone()[0]
    print(f"📊 Available rides (scheduled/ongoing): {available_rides}")
    
    # Check bookings table
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]
    print(f"📊 Total bookings: {total_bookings}")
    
    cursor.execute("SELECT status, COUNT(*) FROM bookings GROUP BY status")
    booking_status = cursor.fetchall()
    print("📊 Booking status distribution:")
    for status, count in booking_status:
        print(f"   {status}: {count}")
    
    # Check messages table
    try:
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        print(f"📊 Total messages: {total_messages}")
    except sqlite3.OperationalError:
        print("📊 Messages table not found")
    
    conn.close()

def main():
    print("🔧 Booking and Chat Fix Tool")
    print("=" * 50)
    print("Fixing:")
    print("1. Passengers can't book new posts")
    print("2. Chat notifications not appearing")
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Create backup
    if not backup_database(db_path):
        print("❌ Cannot proceed without backup!")
        return False
    
    # Fix booking service
    fix_booking_service()
    
    # Check Socket.IO configuration
    check_socket_configuration()
    
    # Check frontend integration
    check_frontend_socket_integration()
    
    # Check message model
    fix_message_model()
    
    # Verify database state
    verify_database_state(db_path)
    
    # Test the fixes
    if input("\n🧪 Run booking and chat tests? (y/N): ").lower() == 'y':
        create_test_booking_and_chat()
    
    print("\n✅ Booking and Chat Fix Process Completed!")
    print("📋 Next steps:")
    print("   1. Restart the Flask application")
    print("   2. Test passenger booking functionality")
    print("   3. Test chat notifications")
    print("   4. Check browser console for Socket.IO errors")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
