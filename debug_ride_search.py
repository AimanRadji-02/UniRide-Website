#!/usr/bin/env python3
"""
Ride Search Debugging Tool
Helps debug why driver rides are not appearing in passenger search
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

def find_database():
    """Find the database file"""
    for possible_path in ['uniride.db', 'instance/uniride.db', 'data/uniride.db']:
        if Path(possible_path).exists():
            return possible_path
    return None

def check_ride_data(db_path):
    """Check ride data and status distribution"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Ride Data Analysis:")
    print("=" * 50)
    
    # Check total rides
    cursor.execute("SELECT COUNT(*) FROM rides")
    total_rides = cursor.fetchone()[0]
    print(f"📊 Total rides: {total_rides}")
    
    # Check status distribution
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM rides 
        GROUP BY status
    """)
    status_dist = cursor.fetchall()
    print("\n📈 Status Distribution:")
    for status, count in status_dist:
        print(f"   {status}: {count} rides")
    
    # Check recent rides (last 24 hours)
    cursor.execute("""
        SELECT ride_id, origin, destination, status, departure_datetime, available_seats
        FROM rides 
        WHERE departure_datetime >= datetime('now', '-1 day')
        ORDER BY created_at DESC
        LIMIT 10
    """)
    recent_rides = cursor.fetchall()
    print(f"\n🕐 Recent Rides (Last 24 Hours):")
    for ride in recent_rides:
        print(f"   ID: {ride[0]} | {ride[1]} → {ride[2]} | Status: {ride[3]} | Seats: {ride[5]}")
    
    # Check rides that should be searchable
    cursor.execute("""
        SELECT ride_id, origin, destination, status, available_seats
        FROM rides 
        WHERE status IN ('scheduled', 'ongoing') 
        AND available_seats > 0
        AND departure_datetime >= datetime('now')
        ORDER BY departure_datetime
    """)
    searchable_rides = cursor.fetchall()
    print(f"\n🔍 Rides That Should Be Searchable:")
    for ride in searchable_rides:
        print(f"   ID: {ride[0]} | {ride[1]} → {ride[2]} | Status: {ride[3]} | Seats: {ride[4]}")
    
    conn.close()
    return searchable_rides

def simulate_search_query(db_path, origin=None, destination=None):
    """Simulate the search query to see what would be returned"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n🔍 Simulating Search Query:")
    print(f"   Origin: {origin or 'Any'}")
    print(f"   Destination: {destination or 'Any'}")
    
    # Current (buggy) query - looking for 'active' status
    cursor.execute("""
        SELECT ride_id, origin, destination, status, available_seats
        FROM rides 
        WHERE status = 'active' 
        AND available_seats > 0
        AND departure_datetime >= datetime('now')
    """)
    if origin:
        cursor.execute("AND origin LIKE ?", (f'%{origin}%',))
    if destination:
        cursor.execute("AND destination LIKE ?", (f'%{destination}%',))
    
    cursor.execute("ORDER BY departure_datetime")
    current_results = cursor.fetchall()
    
    print(f"\n❌ Current Query Results (status='active'): {len(current_results)} rides")
    for ride in current_results:
        print(f"   ID: {ride[0]} | {ride[1]} → {ride[2]} | Status: {ride[3]}")
    
    # Fixed query - looking for correct statuses
    query = """
        SELECT ride_id, origin, destination, status, available_seats
        FROM rides 
        WHERE status IN ('scheduled', 'ongoing') 
        AND available_seats > 0
        AND departure_datetime >= datetime('now')
    """
    params = []
    if origin:
        query += " AND origin LIKE ?"
        params.append(f'%{origin}%')
    if destination:
        query += " AND destination LIKE ?"
        params.append(f'%{destination}%')
    
    query += " ORDER BY departure_datetime"
    cursor.execute(query, params)
    fixed_results = cursor.fetchall()
    
    print(f"\n✅ Fixed Query Results (status IN ('scheduled', 'ongoing')): {len(fixed_results)} rides")
    for ride in fixed_results:
        print(f"   ID: {ride[0]} | {ride[1]} → {ride[2]} | Status: {ride[3]}")
    
    conn.close()
    return len(current_results), len(fixed_results)

def check_ride_creation_flow(db_path):
    """Check if rides are being created correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n🔧 Ride Creation Flow Check:")
    
    # Check most recent ride
    cursor.execute("""
        SELECT ride_id, driver_id, origin, destination, status, created_at, departure_datetime
        FROM rides 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    latest_ride = cursor.fetchone()
    
    if latest_ride:
        print(f"📝 Latest Ride Details:")
        print(f"   ID: {latest_ride[0]}")
        print(f"   Driver ID: {latest_ride[1]}")
        print(f"   Route: {latest_ride[2]} → {latest_ride[3]}")
        print(f"   Status: {latest_ride[4]}")
        print(f"   Created: {latest_ride[5]}")
        print(f"   Departure: {latest_ride[6]}")
        
        # Check if this ride should be visible
        if latest_ride[4] in ['scheduled', 'ongoing'] and latest_ride[6] > datetime.now().isoformat():
            print(f"   ✅ This ride SHOULD be visible in search")
        else:
            print(f"   ❌ This ride would NOT be visible in search")
            if latest_ride[4] not in ['scheduled', 'ongoing']:
                print(f"      Reason: Status is '{latest_ride[4]}' (not 'scheduled'/'ongoing')")
            if latest_ride[6] <= datetime.now().isoformat():
                print(f"      Reason: Departure time is in the past")
    else:
        print("❌ No rides found in database")
    
    conn.close()

def generate_fix_suggestions():
    """Generate fix suggestions"""
    print(f"\n🛠️  Fix Suggestions:")
    print("=" * 50)
    
    print("1️⃣ UPDATE RideService.search_rides() method:")
    print("""
    # CURRENT (Buggy):
    query = Ride.query.filter_by(status='active').filter(Ride.available_seats > 0)
    
    # FIXED:
    query = Ride.query.filter(Ride.status.in_(['scheduled', 'ongoing'])).filter(Ride.available_seats > 0)
    """)
    
    print("\n2️⃣ UPDATE Ride Creation to use correct status:")
    print("""
    # In RideService.create_ride():
    ride = Ride(
        driver_id=driver_id,
        origin=origin,
        destination=destination,
        departure_datetime=departure_datetime,
        available_seats=available_seats,
        price_per_seat=price_per_seat,
        recurring_days=recurring_days,
        status='scheduled'  # Explicitly set status
    )
    """)
    
    print("\n3️⃣ UPDATE Ride Completion flow:")
    print("""
    # When driver starts ride:
    ride.status = 'ongoing'
    
    # When ride is completed:
    ride.status = 'completed'
    """)
    
    print("\n4️⃣ UPDATE Search Logic to include:")
    print("   ✅ Status filtering: 'scheduled' or 'ongoing'")
    print("   ✅ Available seats > 0")
    print("   ✅ Future departure dates only")
    print("   ✅ Location matching (if provided)")

def main():
    print("🔍 UniRide Search Debug Tool")
    print("=" * 50)
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Run diagnostics
    searchable_rides = check_ride_data(db_path)
    check_ride_creation_flow(db_path)
    current_count, fixed_count = simulate_search_query(db_path)
    
    # Generate suggestions
    generate_fix_suggestions()
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Rides that should be searchable: {len(searchable_rides)}")
    print(f"   Current query returns: {current_count} rides")
    print(f"   Fixed query would return: {fixed_count} rides")
    
    if fixed_count > current_count:
        print(f"   ✅ Fix would show {fixed_count - current_count} more rides!")
    else:
        print(f"   ⚠️  No improvement expected - check other issues")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
