#!/usr/bin/env python3
"""
Safe User Reset Script - Maintains Referential Integrity
This script safely resets all users while handling foreign key relationships properly.
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
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def get_database_info(db_path):
    """Get current database statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    tables = ['users', 'rides', 'bookings', 'ratings', 'messages']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats[table] = 0
    
    conn.close()
    return stats

def reset_users_approach_1_soft_reset(db_path):
    """
    APPROACH 1: Soft Reset (Recommended)
    - Keep user records but reset sensitive data
    - Maintain all foreign key relationships
    - Preserve ride history and ratings
    """
    
    print("\n🔄 APPROACH 1: Soft Reset (Recommended)")
    print("This approach keeps user records but resets sensitive information.")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Reset user passwords to a default
        default_password_hash = "pbkdf2:sha256:260000$salt$hash"  # Replace with actual hash
        
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, 
                email = CASE 
                    WHEN email LIKE '%@example.com' THEN email
                    ELSE 'user_' || user_id || '@reset.local'
                END,
                phone = CASE 
                    WHEN phone LIKE '+%' THEN phone
                    ELSE '0000000000'
                END
        """, (default_password_hash,))
        
        # Clear sessions/tokens if they exist
        cursor.execute("DELETE FROM sessions")
        
        conn.commit()
        
        print("✅ Soft reset completed successfully!")
        print("📋 Changes made:")
        print("   - All passwords reset to default")
        print("   - Emails anonymized (except @example.com)")
        print("   - Phone numbers reset")
        print("   - Sessions cleared")
        print("   - All foreign key relationships preserved")
        
        return True
        
    except Exception as e:
        print(f"❌ Soft reset failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def reset_users_approach_2_complete_reset(db_path):
    """
    APPROACH 2: Complete Reset (Use with Caution)
    - Delete all users and related data
    - Reset auto-increment IDs
    - Fresh start
    """
    
    print("\n🔄 APPROACH 2: Complete Reset (Use with Caution)")
    print("This approach deletes ALL data and starts fresh.")
    
    if not input("⚠️  This will delete ALL data! Type 'DELETE_ALL' to confirm: ") == 'DELETE_ALL':
        print("❌ Confirmation not received. Aborting.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Delete in correct order to respect foreign keys
        tables_to_delete = [
            'ratings',
            'messages', 
            'bookings',
            'rides',
            'users'
        ]
        
        for table in tables_to_delete:
            cursor.execute(f"DELETE FROM {table}")
            print(f"🗑️  Cleared {table}")
        
        # Reset auto-increment IDs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'rides', 'bookings', 'ratings', 'messages')")
        print("🔄 Reset auto-increment IDs")
        
        conn.commit()
        
        print("✅ Complete reset completed successfully!")
        print("📋 All data deleted and IDs reset")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete reset failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_sample_users(db_path):
    """Create sample users after reset"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample users: {e}")
        return False
    finally:
        conn.close()

def main():
    print("🔧 UniRide User Reset Tool")
    print("=" * 50)
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Show current stats
    print("\n📊 Current Database Statistics:")
    stats = get_database_info(db_path)
    for table, count in stats.items():
        print(f"   {table}: {count} records")
    
    # Create backup
    if not backup_database(db_path):
        print("❌ Cannot proceed without backup!")
        return False
    
    # Choose approach
    print("\n🎯 Choose Reset Approach:")
    print("1. Soft Reset (Recommended) - Reset passwords, keep data")
    print("2. Complete Reset - Delete everything, start fresh")
    print("3. Exit without changes")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        success = reset_users_approach_1_soft_reset(db_path)
        if success and input("\nCreate sample users? (y/n): ").lower() == 'y':
            create_sample_users(db_path)
            
    elif choice == '2':
        success = reset_users_approach_2_complete_reset(db_path)
        if success and input("\nCreate sample users? (y/n): ").lower() == 'y':
            create_sample_users(db_path)
            
    elif choice == '3':
        print("👋 Exiting without changes")
        return True
        
    else:
        print("❌ Invalid choice!")
        return False
    
    # Show final stats
    print("\n📊 Final Database Statistics:")
    final_stats = get_database_info(db_path)
    for table, count in final_stats.items():
        print(f"   {table}: {count} records")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
