#!/usr/bin/env python3
"""
Debug Auto-Completion Issue
Investigate why new driver posts are being marked as completed immediately
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

def check_recent_ride_creation(db_path):
    """Check recent rides to see their status and creation pattern"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Recent Ride Creation Analysis:")
    print("=" * 50)
    
    # Get very recent rides (last few minutes)
    cursor.execute("""
        SELECT ride_id, driver_id, origin, destination, status, 
               created_at, departure_datetime, available_seats
        FROM rides 
        WHERE created_at >= datetime('now', '-1 hour')
        ORDER BY created_at DESC
    """)
    recent_rides = cursor.fetchall()
    
    if not recent_rides:
        print("   No rides created in the last hour")
        
        # Get last 5 rides regardless of time
        cursor.execute("""
            SELECT ride_id, driver_id, origin, destination, status, 
                   created_at, departure_datetime, available_seats
            FROM rides 
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_rides = cursor.fetchall()
        print("   Showing last 5 rides instead:")
    
    for ride in recent_rides:
        ride_id, driver_id, origin, destination, status, created_at, departure_datetime, seats = ride
        print(f"\n📝 Ride ID: {ride_id}")
        print(f"   Driver: {driver_id}")
        print(f"   Route: {origin} → {destination}")
        print(f"   Status: {status}")
        print(f"   Created: {created_at}")
        print(f"   Departs: {departure_datetime}")
        print(f"   Seats: {seats}")
        
        # Check if this looks like an auto-completion
        if status == 'completed':
            time_diff = datetime.strptime(departure_datetime, '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
            print(f"   ⚠️  RIDE MARKED COMPLETED!")
            print(f"   ⏰ Time between creation and completion: {time_diff}")
            
            if time_diff.total_seconds() < 60:  # Less than 1 minute
                print(f"   🚨 SUSPICIOUS: Completed within {time_diff.total_seconds():.1f} seconds of creation!")
    
    conn.close()
    return recent_rides

def check_for_auto_completion_triggers():
    """Check for any code that might auto-complete rides"""
    print("\n🔍 Checking for Auto-Completion Triggers:")
    print("=" * 50)
    
    # Check ride controller for completion logic
    try:
        with open('controllers/ride_controller.py', 'r') as f:
            controller_code = f.read()
            
        print("📄 controllers/ride_controller.py:")
        lines = controller_code.split('\n')
        for i, line in enumerate(lines):
            if 'status' in line.lower() and 'complete' in line.lower():
                print(f"   Line {i+1}: {line.strip()}")
                # Show context
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    if j != i:
                        print(f"   Line {j+1}: {lines[j].strip()}")
                print()
    except FileNotFoundError:
        print("   ❌ controllers/ride_controller.py not found")
    
    # Check for any scheduled tasks or cron jobs
    print("📄 Checking for scheduled tasks:")
    scheduled_files = ['cron.py', 'scheduler.py', 'tasks.py', 'background.py']
    for file in scheduled_files:
        if Path(file).exists():
            print(f"   Found: {file}")
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if 'complete' in content.lower() or 'status' in content.lower():
                        print(f"      Contains completion logic")
            except:
                pass

def check_ride_model_defaults():
    """Check ride model for any default value issues"""
    print("\n🔍 Checking Ride Model:")
    print("=" * 50)
    
    try:
        with open('models/ride.py', 'r') as f:
            model_code = f.read()
            
        print("📄 models/ride.py:")
        lines = model_code.split('\n')
        for line in lines:
            if 'status' in line.lower() and 'default' in line.lower():
                print(f"   {line.strip()}")
            elif 'status' in line.lower() and 'column' in line.lower():
                print(f"   {line.strip()}")
    except FileNotFoundError:
        print("   ❌ models/ride.py not found")

def check_database_triggers(db_path):
    """Check for database triggers that might auto-complete rides"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Checking Database Triggers:")
    print("=" * 50)
    
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
    triggers = cursor.fetchall()
    
    if triggers:
        for trigger in triggers:
            print(f"🔫 Trigger: {trigger[0]}")
            print(f"   SQL: {trigger[1]}")
            if 'complete' in trigger[1].lower() or 'status' in trigger[1].lower():
                print(f"   ⚠️  This trigger might affect ride status!")
    else:
        print("   ✅ No triggers found")
    
    conn.close()

def check_frontend_ride_creation():
    """Check frontend ride creation for any auto-completion logic"""
    print("\n🔍 Checking Frontend Ride Creation:")
    print("=" * 50)
    
    # Check offer ride template
    try:
        with open('templates/offer_ride.html', 'r') as f:
            template_content = f.read()
            
        print("📄 templates/offer_ride.html:")
        lines = template_content.split('\n')
        for i, line in enumerate(lines):
            if 'complete' in line.lower() or 'status' in line.lower():
                print(f"   Line {i+1}: {line.strip()}")
    except FileNotFoundError:
        print("   ❌ templates/offer_ride.html not found")
    
    # Check JavaScript files
    js_files = ['static/js/app.js', 'static/js/rides.js']
    for js_file in js_files:
        if Path(js_file).exists():
            print(f"\n📄 {js_file}:")
            try:
                with open(js_file, 'r') as f:
                    js_content = f.read()
                    if 'complete' in js_content.lower() or 'status' in js_content.lower():
                        print(f"   Contains completion/status logic")
            except:
                pass

def simulate_ride_creation():
    """Simulate creating a ride to see what happens"""
    print("\n🧪 Simulating Ride Creation:")
    print("=" * 50)
    
    try:
        # Import the RideService
        from services.ride_service import RideService
        from datetime import datetime, timedelta
        
        # Create a test ride
        test_ride = RideService.create_ride(
            driver_id=1,  # Assuming user 1 exists
            origin="Test Origin",
            destination="Test Destination", 
            departure_datetime=datetime.now() + timedelta(hours=2),
            available_seats=3,
            price_per_seat=10.0
        )
        
        print(f"✅ Test ride created:")
        print(f"   ID: {test_ride.ride_id}")
        print(f"   Status: {test_ride.status}")
        print(f"   Origin: {test_ride.origin}")
        print(f"   Destination: {test_ride.destination}")
        
        if test_ride.status == 'completed':
            print("🚨 ISSUE FOUND: Test ride was immediately marked as completed!")
        elif test_ride.status == 'scheduled':
            print("✅ Test ride correctly marked as scheduled")
        else:
            print(f"⚠️  Unexpected status: {test_ride.status}")
        
        # Clean up the test ride
        from models import db
        db.session.delete(test_ride)
        db.session.commit()
        print("🧹 Test ride cleaned up")
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")

def main():
    print("🔍 Auto-Completion Debug Tool")
    print("=" * 50)
    print("Investigating why new driver posts are marked as completed immediately")
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Run all checks
    recent_rides = check_recent_ride_creation(db_path)
    check_for_auto_completion_triggers()
    check_ride_model_defaults()
    check_database_triggers(db_path)
    check_frontend_ride_creation()
    
    # Try simulation
    if input("\n🧪 Run ride creation simulation? (y/N): ").lower() == 'y':
        simulate_ride_creation()
    
    # Summary
    print("\n📋 Investigation Summary:")
    print("=" * 50)
    
    # Check if we found the issue
    suspicious_rides = [ride for ride in recent_rides if ride[4] == 'completed']  # status == 'completed'
    
    if suspicious_rides:
        print(f"🚨 ISSUE FOUND: {len(suspicious_rides)} rides were immediately marked as completed!")
        print("   Check the following:")
        print("   1. Ride creation logic in RideService")
        print("   2. Frontend JavaScript after ride creation")
        print("   3. Any background tasks or triggers")
        print("   4. Database constraints or defaults")
    else:
        print("✅ No obvious auto-completion issues found")
        print("   The issue might be:")
        print("   1. User interface showing wrong status")
        print("   2. Caching issues")
        print("   3. Timing-related completion logic")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
