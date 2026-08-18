# This script handles creating your local database and gives you functions to log your daily sleep, activities, and check-ins.

import sqlite3
from datetime import datetime

DB_NAME = "habit_tracker.db"

def init_db():
    """Initializes the SQLite database and creates necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table for daily check-ins & general logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT, -- e.g., 'sleep', 'workout', 'work', 'mood'
            value REAL,    -- e.g., hours slept, minutes run
            notes TEXT     -- conversational details
        )
    """)
    
    conn.commit()
    conn.close()

def log_habit(category: str, value: float, notes: str = ""):
    """Logs a new habit entry with the current date."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO daily_logs (date, category, value, notes)
        VALUES (?, ?, ?, ?)
    """, (today, category, value, notes))
    
    conn.commit()
    conn.close()

def get_recent_logs(days: int = 7):
    """Retrieves logs from the past N days."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, category, value, notes 
        FROM daily_logs 
        WHERE date >= date('now', '-' || ? || ' day')
        ORDER BY date DESC
    """, (days,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

# Initialize the database immediately when imported/run
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")