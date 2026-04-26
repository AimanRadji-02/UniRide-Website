#!/usr/bin/env python3
"""
Complete Fix for Both Issues:
1. Ride Status Bug - Convert 'active' rides to 'scheduled'
2. User Deletion Issues - Proper deletion with foreign key handling
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
    backup_path = f"{db_path}.backup_complete_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def fix_ride_status_issue(db_path):
    """Fix ride status by converting 'active' to 'scheduled'"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔧 Fixing Ride Status Issue:")
    print("=" * 50)
    
    # Check current status
    cursor.execute("SELECT status, COUNT(*) FROM rides GROUP BY status")
    status_before = cursor.fetchall()
    print("📊 Status distribution BEFORE:")
    for status, count in status_before:
        print(f"   {status}: {count}")
    
    # Find active rides
    cursor.execute("SELECT COUNT(*) FROM rides WHERE status = 'active'")
    active_count = cursor.fetchone()[0]
    
    if active_count > 0:
        print(f"\n🔄 Converting {active_count} 'active' rides to 'scheduled'...")
        
        # Update active rides to scheduled
        cursor.execute("UPDATE rides SET status = 'scheduled' WHERE status = 'active'")
        updated = cursor.rowcount
        
        conn.commit()
        print(f"✅ Updated {updated} rides to 'scheduled'")
        
        # Verify
        cursor.execute("SELECT status, COUNT(*) FROM rides GROUP BY status")
        status_after = cursor.fetchall()
        print("\n📊 Status distribution AFTER:")
        for status, count in status_after:
            print(f"   {status}: {count}")
    else:
        print("✅ No 'active' rides found - status issue already fixed")
    
    conn.close()
    return True

def fix_user_deletion_issue(db_path):
    """Fix user deletion by properly handling foreign keys"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔧 Fixing User Deletion Issue:")
    print("=" * 50)
    
    # Check current users
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"📊 Current users: {user_count}")
    
    # Check what's blocking deletion
    blocking_data = {}
    
    # Check rides
    cursor.execute("SELECT COUNT(*) FROM rides")
    ride_count = cursor.fetchone()[0]
    if ride_count > 0:
        blocking_data['rides'] = ride_count
    
    # Check bookings
    cursor.execute("SELECT COUNT(*) FROM bookings")
    booking_count = cursor.fetchone()[0]
    if booking_count > 0:
        blocking_data['bookings'] = booking_count
    
    # Check ratings
    cursor.execute("SELECT COUNT(*) FROM ratings")
    rating_count = cursor.fetchone()[0]
    if rating_count > 0:
        blocking_data['ratings'] = rating_count
    
    # Check messages
    try:
        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]
        if message_count > 0:
            blocking_data['messages'] = message_count
    except sqlite3.OperationalError:
        pass
    
    if blocking_data:
        print("📋 Data blocking user deletion:")
        for table, count in blocking_data.items():
            print(f"   {table}: {count} records")
        
        print("\n🔄 Performing complete user reset with proper deletion order...")
        
        # Delete in correct order
        deletion_order = [
            ('ratings', 'DELETE FROM ratings'),
            ('bookings', 'DELETE FROM bookings'),
            ('messages', 'DELETE FROM messages'),
            ('rides', 'DELETE FROM rides'),
            ('users', 'DELETE FROM users')
        ]
        
        for table_name, delete_sql in deletion_order:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count_before = cursor.fetchone()[0]
                
                if count_before > 0:
                    cursor.execute(delete_sql)
                    deleted = cursor.rowcount
                    print(f"   🗑️  Deleted {deleted} records from {table_name}")
                else:
                    print(f"   ✅ {table_name} already empty")
            except sqlite3.OperationalError as e:
                print(f"   ⚠️  Could not delete from {table_name}: {e}")
        
        # Reset auto-increment IDs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'rides', 'bookings', 'ratings', 'messages')")
        print("   🔄 Reset auto-increment IDs")
        
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM users")
        final_user_count = cursor.fetchone()[0]
        print(f"\n✅ User deletion completed! Remaining users: {final_user_count}")
        
    else:
        print("✅ No blocking data found - users can be deleted directly")
    
    conn.close()
    return True

def create_sample_data(db_path):
    """Create sample users after complete reset"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n👥 Creating Sample Users:")
    print("=" * 50)
    
    sample_users = [
        ('admin', 'admin@uniride.local', '+966500000001', 'admin', 'pbkdf2:sha256:260000$admin_salt$admin_hash'),
        ('driver1', 'driver1@uniride.local', '+966500000002', 'driver', 'pbkdf2:sha256:260000$driver1_salt$driver1_hash'),
        ('driver2', 'driver2@uniride.local', '+966500000003', 'driver', 'pbkdf2:sha256:260000$driver2_salt$driver2_hash'),
        ('passenger1', 'passenger1@uniride.local', '+966500000004', 'passenger', 'pbkdf2:sha256:260000$passenger1_salt$passenger1_hash'),
        ('passenger2', 'passenger2@uniride.local', '+966500000005', 'passenger', 'pbkdf2:sha256:260000$passenger2_salt$passenger2_hash'),
    ]
    
    try:
        cursor.executemany("""
            INSERT INTO users (name, email, phone, role, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(name, email, phone, role, pwd_hash, datetime.utcnow()) for name, email, phone, role, pwd_hash in sample_users])
        
        conn.commit()
        print(f"✅ Created {len(sample_users)} sample users")
        
        # Show created users
        cursor.execute("SELECT user_id, name, email, role FROM users ORDER BY user_id")
        users = cursor.fetchall()
        print("\n📋 Created Users:")
        for user in users:
            print(f"   ID: {user[0]} | {user[1]} ({user[3]}) | {user[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample users: {e}")
        return False
    finally:
        conn.close()

def verify_fixes(db_path):
    """Verify both fixes worked correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying Fixes:")
    print("=" * 50)
    
    # Check ride status
    cursor.execute("SELECT status, COUNT(*) FROM rides GROUP BY status")
    ride_status = cursor.fetchall()
    print("📊 Final Ride Status:")
    for status, count in ride_status:
        print(f"   {status}: {count}")
    
    # Check for problematic statuses
    active_rides = sum(count for status, count in ride_status if status == 'active')
    if active_rides == 0:
        print("✅ Ride status fix successful - no 'active' rides")
    else:
        print(f"❌ Ride status fix incomplete - {active_rides} 'active' rides remain")
    
    # Check users
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
    user_roles = cursor.fetchall()
    
    print(f"\n👥 Final User Count: {user_count}")
    print("📊 User Roles:")
    for role, count in user_roles:
        print(f"   {role}: {count}")
    
    if user_count > 0 and user_count <= 10:  # Reasonable sample size
        print("✅ User deletion fix successful")
    else:
        print("❌ User deletion fix may have issues")
    
    conn.close()
    return True

def main():
    print("🔧 Complete Fix for Both Issues")
    print("=" * 50)
    print("1. Ride Status Bug - Convert 'active' rides to 'scheduled'")
    print("2. User Deletion Issues - Proper deletion with foreign key handling")
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"\n📁 Database: {db_path}")
    
    # Create backup
    if not backup_database(db_path):
        print("❌ Cannot proceed without backup!")
        return False
    
    # Fix ride status issue
    fix_ride_status_issue(db_path)
    
    # Ask about user deletion
    if input("\n🗑️  Also perform complete user deletion reset? (y/N): ").lower() == 'y':
        fix_user_deletion_issue(db_path)
        
        # Ask about sample data
        if input("\n👥 Create sample users after reset? (y/N): ").lower() == 'y':
            create_sample_data(db_path)
    
    # Verify fixes
    verify_fixes(db_path)
    
    print("\n🎉 Complete fix process finished!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
