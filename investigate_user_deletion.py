#!/usr/bin/env python3
"""
Investigate User Deletion Issues
Check why users are not being fully removed from database
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

def check_foreign_key_constraints(db_path):
    """Check foreign key constraints that might block user deletion"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Foreign Key Constraints:")
    print("=" * 50)
    
    # Get all foreign key constraints
    cursor.execute("PRAGMA foreign_key_list(users)")
    fk_constraints = cursor.fetchall()
    
    if fk_constraints:
        print("📗 Foreign Key Constraints ON users table:")
        for fk in fk_constraints:
            print(f"   Table: {fk[2]} | Column: {fk[3]} -> References: {fk[4]}.{fk[5]}")
    else:
        print("   No foreign key constraints on users table")
    
    # Check which tables reference users
    cursor.execute("""
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type='table' 
        AND sql LIKE '%user_id%'
        AND name != 'users'
    """)
    referencing_tables = cursor.fetchall()
    
    print("\n📊 Tables that Reference users:")
    for table_name, sql in referencing_tables:
        print(f"   {table_name}")
        # Count records
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"      Records: {count}")
        except sqlite3.OperationalError:
            print(f"      Records: Unable to count")
    
    conn.close()
    return referencing_tables

def check_current_user_data(db_path):
    """Check current user data and relationships"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Current User Data:")
    print("=" * 50)
    
    # Count users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    print(f"📊 Total users: {total_users}")
    
    # Count users by role
    cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
    role_dist = cursor.fetchall()
    
    print("\n👥 Users by Role:")
    for role, count in role_dist:
        print(f"   {role}: {count}")
    
    # Check users with related data
    cursor.execute("""
        SELECT u.user_id, u.name, u.role,
               COUNT(DISTINCT r.ride_id) as rides_count,
               COUNT(DISTINCT b.booking_id) as bookings_count,
               COUNT(DISTINCT rat.rating_id) as ratings_given,
               COUNT(DISTINCT rat2.rating_id) as ratings_received
        FROM users u
        LEFT JOIN rides r ON u.user_id = r.driver_id
        LEFT JOIN bookings b ON u.user_id = b.passenger_id
        LEFT JOIN ratings rat ON u.user_id = rat.reviewer_id
        LEFT JOIN ratings rat2 ON u.user_id = rat2.reviewee_id
        GROUP BY u.user_id
        ORDER BY u.user_id
    """)
    users_with_data = cursor.fetchall()
    
    print(f"\n📊 Users with Related Data:")
    for user in users_with_data[:10]:  # Show first 10
        user_id, name, role, rides, bookings, ratings_given, ratings_received = user
        print(f"   ID: {user_id} | {name} ({role})")
        print(f"      Rides: {rides} | Bookings: {bookings}")
        print(f"      Ratings Given: {ratings_given} | Received: {ratings_received}")
    
    if len(users_with_data) > 10:
        print(f"   ... and {len(users_with_data) - 10} more users")
    
    conn.close()
    return users_with_data

def check_deletion_order(db_path):
    """Show the correct order for deletion"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Correct Deletion Order:")
    print("=" * 50)
    
    # Get dependency graph
    tables_to_check = ['ratings', 'bookings', 'rides', 'messages', 'users']
    
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        except sqlite3.OperationalError:
            print(f"   {table}: Table not found")
    
    print("\n📋 Recommended Deletion Order:")
    print("   1. ratings (depends on rides, users)")
    print("   2. bookings (depends on rides, users)")
    print("   3. messages (depends on users)")
    print("   4. rides (depends on users)")
    print("   5. users (no dependencies)")
    
    conn.close()

def test_user_deletion_simulation(db_path):
    """Simulate user deletion to see what blocks it"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 User Deletion Simulation:")
    print("=" * 50)
    
    # Find a user to test
    cursor.execute("SELECT user_id, name FROM users LIMIT 1")
    test_user = cursor.fetchone()
    
    if not test_user:
        print("   No users found to test")
        conn.close()
        return
    
    user_id, name = test_user
    print(f"🧪 Testing deletion of user: {name} (ID: {user_id})")
    
    # Check what would block deletion
    blocking_tables = []
    
    # Check rides
    cursor.execute("SELECT COUNT(*) FROM rides WHERE driver_id = ?", (user_id,))
    ride_count = cursor.fetchone()[0]
    if ride_count > 0:
        blocking_tables.append(f"rides ({ride_count} records)")
    
    # Check bookings
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE passenger_id = ?", (user_id,))
    booking_count = cursor.fetchone()[0]
    if booking_count > 0:
        blocking_tables.append(f"bookings ({booking_count} records)")
    
    # Check ratings as reviewer
    cursor.execute("SELECT COUNT(*) FROM ratings WHERE reviewer_id = ?", (user_id,))
    reviewer_count = cursor.fetchone()[0]
    if reviewer_count > 0:
        blocking_tables.append(f"ratings as reviewer ({reviewer_count} records)")
    
    # Check ratings as reviewee
    cursor.execute("SELECT COUNT(*) FROM ratings WHERE reviewee_id = ?", (user_id,))
    reviewee_count = cursor.fetchone()[0]
    if reviewee_count > 0:
        blocking_tables.append(f"ratings as reviewee ({reviewee_count} records)")
    
    # Check messages
    try:
        cursor.execute("SELECT COUNT(*) FROM messages WHERE sender_id = ? OR receiver_id = ?", (user_id, user_id))
        message_count = cursor.fetchone()[0]
        if message_count > 0:
            blocking_tables.append(f"messages ({message_count} records)")
    except sqlite3.OperationalError:
        pass
    
    if blocking_tables:
        print(f"❌ User deletion would be blocked by:")
        for table in blocking_tables:
            print(f"   - {table}")
    else:
        print("✅ User deletion would succeed")
    
    conn.close()

def check_soft_delete_logic():
    """Check if there's soft delete logic being used"""
    print("\n🔍 Checking for Soft Delete Logic:")
    print("=" * 50)
    
    # Check models for soft delete fields
    try:
        with open('models/user.py', 'r') as f:
            user_model = f.read()
            print("📄 models/user.py:")
            
            # Look for soft delete indicators
            soft_delete_fields = ['is_active', 'deleted_at', 'is_deleted', 'status']
            for field in soft_delete_fields:
                if field in user_model:
                    print(f"   Found potential soft delete field: {field}")
                    # Show the line
                    for line in user_model.split('\n'):
                        if field in line and 'Column' in line:
                            print(f"      {line.strip()}")
    except FileNotFoundError:
        print("   ❌ models/user.py not found")
    
    # Check controllers for soft delete logic
    try:
        with open('controllers/user_controller.py', 'r') as f:
            controller_code = f.read()
            print("\n📄 controllers/user_controller.py:")
            
            # Look for soft delete logic
            soft_delete_keywords = ['is_active', 'deleted_at', 'soft', 'deactivate']
            for keyword in soft_delete_keywords:
                if keyword in controller_code:
                    print(f"   Found soft delete keyword: {keyword}")
    except FileNotFoundError:
        print("   ❌ controllers/user_controller.py not found")

def main():
    print("🔍 User Deletion Investigation")
    print("=" * 50)
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Run investigations
    referencing_tables = check_foreign_key_constraints(db_path)
    users_with_data = check_current_user_data(db_path)
    check_deletion_order(db_path)
    test_user_deletion_simulation(db_path)
    check_soft_delete_logic()
    
    # Summary
    print("\n📋 Investigation Summary:")
    print("=" * 50)
    print(f"✅ Referencing tables found: {len(referencing_tables)}")
    print(f"✅ Users with related data: {len(users_with_data)}")
    
    if referencing_tables:
        print("❌ ISSUE FOUND: Users have foreign key relationships!")
        print("   Fix: Delete dependent records first, then delete users")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
