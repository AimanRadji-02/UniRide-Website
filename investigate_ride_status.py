#!/usr/bin/env python3
"""
Investigate Ride Status Bug
Check why rides are auto-completing instead of staying 'scheduled'
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

def check_ride_table_structure(db_path):
    """Check rides table structure and default values"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Rides Table Structure:")
    print("=" * 50)
    
    # Get table schema
    cursor.execute("PRAGMA table_info(rides)")
    columns = cursor.fetchall()
    
    status_default = None
    for col in columns:
        print(f"   {col[1]} {col[2]} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        if col[1] == 'status' and col[4]:
            status_default = col[4]
    
    print(f"\n📊 Status Default Value: {status_default}")
    conn.close()
    return status_default

def check_current_ride_data(db_path):
    """Check current ride data and status distribution"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Current Ride Data:")
    print("=" * 50)
    
    # Check total rides
    cursor.execute("SELECT COUNT(*) FROM rides")
    total_rides = cursor.fetchone()[0]
    print(f"📊 Total rides: {total_rides}")
    
    # Check status distribution
    cursor.execute("""
        SELECT status, COUNT(*) as count,
               MIN(created_at) as oldest,
               MAX(created_at) as newest
        FROM rides 
        GROUP BY status
    """)
    status_dist = cursor.fetchall()
    
    print("\n📈 Status Distribution:")
    for status, count, oldest, newest in status_dist:
        print(f"   {status}: {count} rides")
        print(f"      Oldest: {oldest}")
        print(f"      Newest: {newest}")
    
    # Check recent rides
    cursor.execute("""
        SELECT ride_id, driver_id, origin, destination, status, 
               created_at, departure_datetime, available_seats
        FROM rides 
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent_rides = cursor.fetchall()
    
    print("\n🕐 Recent Rides (Last 5):")
    for ride in recent_rides:
        print(f"   ID: {ride[0]} | Driver: {ride[1]}")
        print(f"      Route: {ride[2]} → {ride[3]}")
        print(f"      Status: {ride[4]}")
        print(f"      Created: {ride[5]}")
        print(f"      Departs: {ride[6]}")
        print(f"      Seats: {ride[7]}")
        print()
    
    conn.close()
    return recent_rides

def check_for_triggers_or_constraints(db_path):
    """Check for triggers or constraints that might affect status"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Checking for Triggers:")
    print("=" * 50)
    
    # Check triggers
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
    triggers = cursor.fetchall()
    
    if triggers:
        for trigger in triggers:
            print(f"   Trigger: {trigger[0]}")
            print(f"   SQL: {trigger[1]}")
    else:
        print("   No triggers found")
    
    # Check indexes
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='rides'")
    indexes = cursor.fetchall()
    
    print("\n📊 Rides Table Indexes:")
    for index in indexes:
        print(f"   {index[0]}: {index[1]}")
    
    conn.close()

def check_ride_creation_code():
    """Check the ride creation code for issues"""
    print("\n🔍 Checking Ride Creation Code:")
    print("=" * 50)
    
    # Check Ride model
    try:
        with open('models/ride.py', 'r') as f:
            ride_model = f.read()
            print("📄 models/ride.py:")
            # Find status line
            for line in ride_model.split('\n'):
                if 'status' in line.lower() and 'column' in line.lower():
                    print(f"   {line.strip()}")
    except FileNotFoundError:
        print("   ❌ models/ride.py not found")
    
    # Check RideService
    try:
        with open('services/ride_service.py', 'r') as f:
            service_code = f.read()
            print("\n📄 services/ride_service.py:")
            # Find create_ride method
            lines = service_code.split('\n')
            in_create_ride = False
            for i, line in enumerate(lines):
                if 'def create_ride' in line:
                    in_create_ride = True
                    print(f"   Line {i+1}: {line.strip()}")
                elif in_create_ride and 'return ride' in line:
                    print(f"   Line {i+1}: {line.strip()}")
                    break
                elif in_create_ride:
                    print(f"   Line {i+1}: {line.strip()}")
    except FileNotFoundError:
        print("   ❌ services/ride_service.py not found")

def check_time_based_logic():
    """Check for any time-based auto-completion logic"""
    print("\n🔍 Checking for Time-Based Logic:")
    print("=" * 50)
    
    # Check controllers
    try:
        with open('controllers/ride_controller.py', 'r') as f:
            controller_code = f.read()
            print("📄 controllers/ride_controller.py:")
            
            # Look for status changes
            lines = controller_code.split('\n')
            for i, line in enumerate(lines):
                if 'status' in line.lower() and ('completed' in line.lower() or 'complete' in line.lower()):
                    print(f"   Line {i+1}: {line.strip()}")
                    # Show context
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if j != i:
                            print(f"   Line {j+1}: {lines[j].strip()}")
                    print()
    except FileNotFoundError:
        print("   ❌ controllers/ride_controller.py not found")

def main():
    print("🔍 Ride Status Bug Investigation")
    print("=" * 50)
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Run investigations
    status_default = check_ride_table_structure(db_path)
    recent_rides = check_current_ride_data(db_path)
    check_for_triggers_or_constraints(db_path)
    check_ride_creation_code()
    check_time_based_logic()
    
    # Summary
    print("\n📋 Investigation Summary:")
    print("=" * 50)
    print(f"✅ Status default value: {status_default}")
    print(f"✅ Recent rides checked: {len(recent_rides)}")
    
    # Check if we found the issue
    if status_default and 'completed' in status_default.lower():
        print("❌ ISSUE FOUND: Default status is 'completed'!")
        print("   Fix: Change default to 'scheduled'")
    elif recent_rides and any(ride[4] == 'completed' for ride in recent_rides):
        print("❌ ISSUE FOUND: Recent rides have 'completed' status!")
        print("   Check ride creation logic for auto-completion")
    else:
        print("✅ No obvious issues found in database structure")
        print("   Check application logs for runtime status changes")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
