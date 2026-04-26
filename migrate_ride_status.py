#!/usr/bin/env python3
"""
Migration script to add status column to rides table and create ratings table
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Add status column to rides table and create ratings table"""
    
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
        
        # Check if status column exists in rides table
        cursor.execute("PRAGMA table_info(rides)")
        ride_columns = [row[1] for row in cursor.fetchall()]
        
        # Add status column if it doesn't exist
        if 'status' not in ride_columns:
            print("Adding status column to rides table")
            cursor.execute("ALTER TABLE rides ADD COLUMN status VARCHAR(20) DEFAULT 'scheduled'")
            
            # Update existing rides to have 'scheduled' status
            cursor.execute("UPDATE rides SET status = 'scheduled' WHERE status IS NULL")
        else:
            print("Status column already exists in rides table")
        
        # Create ratings table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ratings'")
        if not cursor.fetchone():
            print("Creating ratings table")
            cursor.execute("""
                CREATE TABLE ratings (
                    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ride_id INTEGER NOT NULL,
                    rater_id INTEGER NOT NULL,
                    rated_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ride_id) REFERENCES rides (ride_id),
                    FOREIGN KEY (rater_id) REFERENCES users (user_id),
                    FOREIGN KEY (rated_id) REFERENCES users (user_id),
                    UNIQUE(ride_id, rater_id, rated_id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX idx_ratings_ride_id ON ratings (ride_id)")
            cursor.execute("CREATE INDEX idx_ratings_rater_id ON ratings (rater_id)")
            cursor.execute("CREATE INDEX idx_ratings_rated_id ON ratings (rated_id)")
        else:
            print("Ratings table already exists")
        
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
