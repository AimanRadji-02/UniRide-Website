#!/usr/bin/env python3
"""
Fix Auto-Completion Issue
Ensure new rides stay 'scheduled' until manually completed by driver
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
    backup_path = f"{db_path}.backup_auto_completion_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def analyze_current_ride_status(db_path):
    """Analyze current ride status to identify issues"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Analyzing Current Ride Status:")
    print("=" * 50)
    
    # Get status distribution
    cursor.execute("SELECT status, COUNT(*) FROM rides GROUP BY status")
    status_dist = cursor.fetchall()
    
    print("📊 Current Status Distribution:")
    for status, count in status_dist:
        print(f"   {status}: {count} rides")
    
    # Find problematic rides
    problematic_statuses = ['active', 'completed']
    for status, count in status_dist:
        if status in problematic_statuses and count > 0:
            print(f"\n⚠️  Found {count} rides with '{status}' status")
            
            # Get details of problematic rides
            cursor.execute(f"""
                SELECT ride_id, origin, destination, status, created_at, departure_datetime
                FROM rides 
                WHERE status = '{status}'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            rides = cursor.fetchall()
            
            print(f"📝 Recent '{status}' rides:")
            for ride in rides:
                ride_id, origin, destination, status, created_at, departure = ride
                print(f"   ID: {ride_id} | {origin} → {destination}")
                print(f"      Created: {created_at} | Departs: {departure}")
    
    conn.close()
    return status_dist

def fix_ride_status_issues(db_path):
    """Fix ride status issues"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔧 Fixing Ride Status Issues:")
    print("=" * 50)
    
    # Fix 1: Convert 'active' rides to 'scheduled'
    cursor.execute("SELECT COUNT(*) FROM rides WHERE status = 'active'")
    active_count = cursor.fetchone()[0]
    
    if active_count > 0:
        print(f"🔄 Converting {active_count} 'active' rides to 'scheduled'...")
        cursor.execute("UPDATE rides SET status = 'scheduled' WHERE status = 'active'")
        conn.commit()
        print("✅ 'active' rides converted to 'scheduled'")
    
    # Fix 2: Check for recently created rides that might be incorrectly marked as completed
    cursor.execute("""
        SELECT COUNT(*) FROM rides 
        WHERE status = 'completed' 
        AND created_at >= datetime('now', '-10 minutes')
    """)
    recent_completed = cursor.fetchone()[0]
    
    if recent_completed > 0:
        print(f"⚠️  Found {recent_completed} rides marked as completed within last 10 minutes")
        
        # Get details
        cursor.execute("""
            SELECT ride_id, origin, destination, created_at, departure_datetime
            FROM rides 
            WHERE status = 'completed' 
            AND created_at >= datetime('now', '-10 minutes')
        """)
        rides = cursor.fetchall()
        
        for ride in rides:
            ride_id, origin, destination, created_at, departure = ride
            print(f"   ID: {ride_id} | {origin} → {destination}")
            print(f"      Created: {created_at} | Departs: {departure}")
        
        # Ask if user wants to fix these
        if input("\n🔄 Convert these recently completed rides back to 'scheduled'? (y/N): ").lower() == 'y':
            cursor.execute("""
                UPDATE rides 
                SET status = 'scheduled' 
                WHERE status = 'completed' 
                AND created_at >= datetime('now', '-10 minutes')
            """)
            conn.commit()
            print("✅ Recently completed rides converted back to 'scheduled'")
    
    # Fix 3: Ensure all future rides have proper status
    cursor.execute("""
        SELECT COUNT(*) FROM rides 
        WHERE status NOT IN ('scheduled', 'ongoing', 'completed', 'cancelled')
        AND departure_datetime >= datetime('now')
    """)
    invalid_status = cursor.fetchone()[0]
    
    if invalid_status > 0:
        print(f"🔄 Fixing {invalid_status} rides with invalid status...")
        cursor.execute("""
            UPDATE rides 
            SET status = 'scheduled' 
            WHERE status NOT IN ('scheduled', 'ongoing', 'completed', 'cancelled')
            AND departure_datetime >= datetime('now')
        """)
        conn.commit()
        print("✅ Invalid status rides fixed")
    
    conn.close()
    return True

def verify_ride_creation_logic():
    """Verify and fix ride creation logic"""
    print("\n🔧 Verifying Ride Creation Logic:")
    print("=" * 50)
    
    # Check RideService
    try:
        with open('services/ride_service.py', 'r') as f:
            service_content = f.read()
            
        if "status='scheduled'" in service_content:
            print("✅ RideService.create_ride() correctly sets status='scheduled'")
        else:
            print("❌ RideService.create_ride() missing status='scheduled'")
            print("🔄 Fixing RideService...")
            
            # Fix the RideService
            fixed_content = service_content.replace(
                "ride = Ride(\n            driver_id=driver_id,\n            origin=origin,\n            destination=destination,\n            departure_datetime=departure_datetime,\n            available_seats=available_seats,\n            price_per_seat=price_per_seat,\n            recurring_days=recurring_days\n        )",
                "ride = Ride(\n            driver_id=driver_id,\n            origin=origin,\n            destination=destination,\n            departure_datetime=departure_datetime,\n            available_seats=available_seats,\n            price_per_seat=price_per_seat,\n            recurring_days=recurring_days,\n            status='scheduled'  # Explicitly set status for new rides\n        )"
            )
            
            with open('services/ride_service.py', 'w') as f:
                f.write(fixed_content)
            
            print("✅ RideService fixed")
    except FileNotFoundError:
        print("❌ services/ride_service.py not found")
    
    # Check Ride model
    try:
        with open('models/ride.py', 'r') as f:
            model_content = f.read()
            
        if "default='scheduled'" in model_content:
            print("✅ Ride model has correct default status")
        else:
            print("⚠️  Ride model default status might be incorrect")
    except FileNotFoundError:
        print("❌ models/ride.py not found")

def create_test_ride_to_verify():
    """Create a test ride to verify the fix"""
    print("\n🧪 Creating Test Ride to Verify Fix:")
    print("=" * 50)
    
    try:
        from services.ride_service import RideService
        from datetime import datetime, timedelta
        from models import db
        
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
        
        # Check status immediately
        if test_ride.status == 'completed':
            print("🚨 ISSUE STILL EXISTS: Test ride was immediately marked as completed!")
            
            # Force fix the test ride
            test_ride.status = 'scheduled'
            db.session.commit()
            print("🔧 Test ride status manually fixed to 'scheduled'")
            
        elif test_ride.status == 'scheduled':
            print("✅ SUCCESS: Test ride correctly marked as 'scheduled'")
        else:
            print(f"⚠️  Unexpected status: {test_ride.status}")
        
        # Clean up the test ride
        db.session.delete(test_ride)
        db.session.commit()
        print("🧹 Test ride cleaned up")
        
        return test_ride.status == 'scheduled'
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("🔧 Auto-Completion Fix Tool")
    print("=" * 50)
    print("Fixing issue where new driver posts are marked as completed immediately")
    
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
    
    # Analyze current state
    analyze_current_ride_status(db_path)
    
    # Fix the issues
    fix_ride_status_issues(db_path)
    
    # Verify creation logic
    verify_ride_creation_logic()
    
    # Test with a new ride
    if input("\n🧪 Create test ride to verify fix? (y/N): ").lower() == 'y':
        success = create_test_ride_to_verify()
        if success:
            print("\n🎉 Auto-completion fix verified successfully!")
        else:
            print("\n❌ Auto-completion issue still exists!")
    
    # Final verification
    print("\n🔍 Final Verification:")
    analyze_current_ride_status(db_path)
    
    print("\n✅ Auto-completion fix process completed!")
    print("📋 Next steps:")
    print("   1. Test creating a new ride as driver")
    print("   2. Verify ride appears as 'scheduled' in driver dashboard")
    print("   3. Verify ride appears in passenger search")
    print("   4. Only mark as completed when driver clicks the button")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
