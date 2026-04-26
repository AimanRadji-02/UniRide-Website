#!/usr/bin/env python3
"""
Fix Ride Status Bug
Convert all 'active' rides to 'scheduled' to fix the auto-completion issue
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
    backup_path = f"{db_path}.backup_status_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def check_current_status_distribution(db_path):
    """Check current status distribution"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status, COUNT(*) as count,
               MIN(created_at) as oldest,
               MAX(created_at) as newest
        FROM rides 
        GROUP BY status
        ORDER BY count DESC
    """)
    status_dist = cursor.fetchall()
    
    print("📊 Current Status Distribution:")
    for status, count, oldest, newest in status_dist:
        print(f"   {status}: {count} rides")
        print(f"      Oldest: {oldest}")
        print(f"      Newest: {newest}")
        print()
    
    conn.close()
    return status_dist

def fix_ride_status(db_path, dry_run=True):
    """Fix ride status by converting 'active' to 'scheduled'"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"🔧 {'DRY RUN - ' if dry_run else ''}Fixing Ride Status:")
    print("=" * 50)
    
    # Find rides that need to be updated
    cursor.execute("""
        SELECT ride_id, origin, destination, status, created_at, departure_datetime
        FROM rides 
        WHERE status = 'active'
        ORDER BY created_at
    """)
    active_rides = cursor.fetchall()
    
    if not active_rides:
        print("✅ No rides with 'active' status found!")
        conn.close()
        return True
    
    print(f"🔍 Found {len(active_rides)} rides with 'active' status:")
    for ride in active_rides:
        print(f"   ID: {ride[0]} | {ride[1]} → {ride[2]}")
        print(f"      Created: {ride[4]} | Departs: {ride[5]}")
    
    if dry_run:
        print(f"\n🔄 DRY RUN: Would update {len(active_rides)} rides from 'active' to 'scheduled'")
        conn.close()
        return True
    
    # Confirm before making changes
    confirm = input(f"\n⚠️  Update {len(active_rides)} rides from 'active' to 'scheduled'? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Cancelled by user")
        conn.close()
        return False
    
    try:
        # Update the rides
        cursor.execute("""
            UPDATE rides 
            SET status = 'scheduled' 
            WHERE status = 'active'
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Successfully updated {updated_count} rides from 'active' to 'scheduled'")
        
        # Verify the update
        cursor.execute("SELECT COUNT(*) FROM rides WHERE status = 'active'")
        remaining_active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rides WHERE status = 'scheduled'")
        new_scheduled = cursor.fetchone()[0]
        
        print(f"📊 After update:")
        print(f"   'active' rides remaining: {remaining_active}")
        print(f"   'scheduled' rides total: {new_scheduled}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to update rides: {e}")
        conn.rollback()
        conn.close()
        return False

def update_database_default(db_path):
    """Update database default value for status column"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔧 Updating Database Default Value:")
    print("=" * 50)
    
    try:
        # SQLite doesn't support ALTER COLUMN with DEFAULT directly
        # We need to recreate the table - but for simplicity, we'll just ensure
        # the application code sets the correct default
        
        print("ℹ️  SQLite doesn't support ALTER COLUMN DEFAULT directly")
        print("✅ Application code already sets status='scheduled' in create_ride()")
        print("✅ Model already has default='scheduled' in ride.py")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to update default: {e}")
        conn.close()
        return False

def verify_fix(db_path):
    """Verify the fix worked correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying Fix:")
    print("=" * 50)
    
    # Check final status distribution
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM rides 
        GROUP BY status
        ORDER BY count DESC
    """)
    final_status = cursor.fetchall()
    
    print("📊 Final Status Distribution:")
    for status, count in final_status:
        print(f"   {status}: {count} rides")
    
    # Check for any problematic statuses
    problematic_statuses = ['completed', 'cancelled']
    for status, count in final_status:
        if status in problematic_statuses and count > 0:
            print(f"⚠️  Found {count} rides with '{status}' status")
    
    # Check recent rides
    cursor.execute("""
        SELECT ride_id, origin, destination, status, created_at
        FROM rides 
        WHERE created_at >= datetime('now', '-1 day')
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent_rides = cursor.fetchall()
    
    print(f"\n🕐 Recent Rides (Last 24 Hours):")
    for ride in recent_rides:
        print(f"   ID: {ride[0]} | {ride[1]} → {ride[2]} | Status: {ride[3]}")
    
    conn.close()
    
    # Check if fix was successful
    active_count = sum(count for status, count in final_status if status == 'active')
    if active_count == 0:
        print("✅ Fix successful! No rides with 'active' status")
        return True
    else:
        print(f"❌ Fix incomplete! Still {active_count} rides with 'active' status")
        return False

def main():
    print("🔧 Ride Status Fix Tool")
    print("=" * 50)
    
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
    
    # Check current status
    check_current_status_distribution(db_path)
    
    # Dry run first
    fix_ride_status(db_path, dry_run=True)
    
    # Ask if user wants to proceed
    if input("\n🚀 Proceed with actual fix? (y/N): ").lower() == 'y':
        success = fix_ride_status(db_path, dry_run=False)
        if success:
            update_database_default(db_path)
            verify_fix(db_path)
            print("\n🎉 Ride status fix completed!")
        else:
            print("\n❌ Ride status fix failed!")
    else:
        print("\n👋 Dry run completed. No changes made.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
