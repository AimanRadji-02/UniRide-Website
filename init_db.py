import sqlite3
import os

DB_PATH = 'uniride.db'

def init_db():
    if os.path.exists(DB_PATH):
        confirm = input(f"Database {DB_PATH} exists. Overwrite? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # === PASTE YOUR COMPLETE CREATE TABLE, INDEX, TRIGGER SQL HERE ===
    create_sql = """
    -- Your full schema from the first answer
    """
    # === PASTE YOUR SAMPLE INSERT SQL HERE ===
    insert_sql = """
    -- Your sample data from the first answer
    """
    cursor.executescript(create_sql)
    cursor.executescript(insert_sql)
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()