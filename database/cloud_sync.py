import sys
import os
import requests
import json
from time import sleep

# Ensure we can import from database and config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.database import get_unsynced_events, mark_event_synced
from backend.app.core.config import settings

def sync_to_firebase():
    """
    Reads unsynced events from the local SQLite edge database and pushes them to Firebase.
    """
    print("\n--- INITIATING CLOUD SYNC ---")
    
    # 1. Check if Firebase URL is configured
    if not settings.FIREBASE_DB_URL:
        print("ERROR: FIREBASE_DB_URL is not set in backend/app/core/config.py")
        print("Please add your Realtime Database URL (e.g., https://your-project.firebaseio.com)")
        return
        
    # 2. Fetch unsynced events from local SQLite
    unsynced_events = get_unsynced_events()
    
    if not unsynced_events:
        print("Everything is up to date. No new events to sync.")
        return
        
    print(f"Found {len(unsynced_events)} pending events in SQLite.")
    
    # 3. Push to Firebase
    success_count = 0
    for event in unsynced_events:
        event_id = event["id"]
        
        # We push to an 'events' node in Firebase
        # Appending .json is required for Firebase Realtime Database REST API
        url = f"{settings.FIREBASE_DB_URL.rstrip('/')}/events/{event_id}.json"
        
        try:
            # Send the event dictionary (excluding the synced_to_cloud flag)
            payload = {k: v for k, v in event.items() if k != "synced_to_cloud"}
            
            response = requests.put(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                # 4. Mark as synced in local SQLite
                mark_event_synced(event_id)
                success_count += 1
                print(f"[{event_id}] Successfully synced {event['event_type']} to Firebase.")
            else:
                print(f"[{event_id}] Failed to sync. Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{event_id}] Network error syncing to Firebase: {e}")
            print("System will try again later. Data remains safely in SQLite.")
            break # Stop trying if network is completely down
            
    print(f"Cloud Sync Complete: {success_count}/{len(unsynced_events)} events uploaded.\n")

def run_continuous_sync(interval_seconds=10):
    """
    Runs continuously in the background, checking for new events every X seconds.
    """
    print(f"Starting background cloud sync daemon (checking every {interval_seconds}s)...")
    try:
        while True:
            sync_to_firebase()
            sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nStopping background sync daemon.")

if __name__ == "__main__":
    # If run directly, just execute a single sync attempt
    sync_to_firebase()
