import sqlite3
import os
from datetime import datetime

# Define the DB file path
DB_FILE = os.path.join(os.path.dirname(__file__), "edge_storage.db")

def get_connection():
    # Helper to get a dictionary-like cursor
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """
    Creates the 'events' table if it doesn't already exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        event_type TEXT NOT NULL,
        confidence REAL,
        severity TEXT,
        audio_class TEXT,
        audio_confidence REAL,
        vision_class TEXT,
        vision_confidence REAL,
        impact_detected BOOLEAN,
        temperature REAL,
        humidity REAL,
        smoke_level REAL,
        latitude REAL,
        longitude REAL,
        traffic_status TEXT,
        barrier_status TEXT,
        buzzer_status TEXT,
        processing_latency REAL,
        synced_to_cloud BOOLEAN DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully at:", DB_FILE)

def insert_event(event: dict) -> int:
    """
    Inserts a new event into the database and returns the generated ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use current time if none provided
    timestamp = event.get("timestamp", datetime.now().isoformat())
    
    cursor.execute("""
    INSERT INTO events (
        timestamp, event_type, confidence, severity, 
        audio_class, audio_confidence, vision_class, vision_confidence,
        impact_detected, temperature, humidity, smoke_level,
        latitude, longitude, traffic_status, barrier_status, buzzer_status, processing_latency, synced_to_cloud
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        timestamp,
        event.get("event_type", "UNKNOWN"),
        event.get("confidence", 0.0),
        event.get("severity", "LOW"),
        event.get("audio_class"),
        event.get("audio_confidence"),
        event.get("vision_class"),
        event.get("vision_confidence"),
        bool(event.get("impact_detected", False)),
        event.get("temperature"),
        event.get("humidity"),
        event.get("smoke_level"),
        event.get("latitude"),
        event.get("longitude"),
        event.get("traffic_status", "UNKNOWN"),
        event.get("barrier_status", "UNKNOWN"),
        event.get("buzzer_status", "UNKNOWN"),
        event.get("processing_latency", 0.0)
    ))
    
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id

def get_recent_events(limit: int = 10) -> list:
    """
    Retrieves the most recent events from the database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_event_by_id(event_id: int) -> dict:
    """
    Retrieves a single event by its ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def get_statistics() -> dict:
    """
    Returns high-level statistics about stored events.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total count
    cursor.execute("SELECT COUNT(*) as total FROM events")
    stats["total_events"] = cursor.fetchone()["total"]
    
    # Count by event type
    cursor.execute("SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type")
    stats["events_by_type"] = {row["event_type"]: row["count"] for row in cursor.fetchall()}
    
    # Average latency
    cursor.execute("SELECT AVG(processing_latency) as avg_latency FROM events")
    avg_latency = cursor.fetchone()["avg_latency"]
    stats["average_latency_ms"] = round(avg_latency, 2) if avg_latency else 0.0
    
    conn.close()
    return stats

def get_unsynced_events() -> list:
    """
    Retrieves all events that have not yet been synced to Firebase.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE synced_to_cloud = 0")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_event_synced(event_id: int):
    """
    Marks an event as successfully synced to Firebase.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET synced_to_cloud = 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("--- TESTING LOCAL SQLITE DATABASE ---\n")
    
    # 1. Initialize
    initialize_database()
    
    # 2. Simulate insertion of events
    event_1 = {
        "event_type": "ACCIDENT",
        "confidence": 94.5,
        "severity": "CRITICAL",
        "audio_class": "CRASH",
        "audio_confidence": 90.0,
        "vision_class": "ACCIDENT",
        "vision_confidence": 85.0,
        "impact_detected": True,
        "temperature": 32.5,
        "humidity": 65.0,
        "smoke_level": 0.1,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "traffic_status": "RED",
        "barrier_status": "CLOSED",
        "buzzer_status": "ON",
        "processing_latency": 14.2
    }
    
    event_2 = {
        "event_type": "FIRE",
        "confidence": 92.0,
        "severity": "CRITICAL",
        "audio_class": "NORMAL_TRAFFIC",
        "audio_confidence": 99.0,
        "vision_class": "FIRE",
        "vision_confidence": 91.0,
        "impact_detected": False,
        "temperature": 45.0,
        "humidity": 30.0,
        "smoke_level": 0.85,
        "latitude": 13.0830,
        "longitude": 80.2710,
        "traffic_status": "RED",
        "barrier_status": "OPEN",
        "buzzer_status": "ON",
        "processing_latency": 22.5
    }

    id_1 = insert_event(event_1)
    id_2 = insert_event(event_2)
    print(f"\nInserted Mock Event 1 (ID: {id_1})")
    print(f"Inserted Mock Event 2 (ID: {id_2})")
    
    # 3. Retrieve by ID
    retrieved = get_event_by_id(id_1)
    print(f"\nRetrieve Event {id_1}: {retrieved['event_type']} at {retrieved['timestamp']}")
    
    # 4. Get Statistics
    stats = get_statistics()
    print("\nDatabase Statistics:")
    import json
    print(json.dumps(stats, indent=2))
