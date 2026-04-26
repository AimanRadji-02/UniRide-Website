#!/usr/bin/env python3
"""
Migration script to add admin cancellation fields to rides table
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Add admin cancellation fields to rides table"""
    
    # Find the database file
    db_path = None
    for possible_path in ['uniride.db', 'instance/uniride.db', 'data/uniride.db']:
        if Path(possible_path).exists():
            db_path = possible_path
            break
    
    if not db_path:
        print("Error: Could not find database file")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(rides)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ('cancellation_reason', 'TEXT'),
            ('cancelled_by_admin_id', 'INTEGER'),
            ('cancelled_at', 'DATETIME')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE rides ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists")
        
        # Add foreign key constraint for cancelled_by_admin_id if it doesn't exist
        # Note: SQLite doesn't support adding foreign key constraints to existing tables
        # This will be handled at the application level
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
