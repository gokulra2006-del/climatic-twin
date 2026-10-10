import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import SessionLocal

def test_connection():
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("Successfully connected to the database!")
        
        # Test PostGIS
        postgis_result = db.execute(text("SELECT PostGIS_version();")).scalar()
        print(f"PostGIS version: {postgis_result}")
        print("PostGIS is installed and working!")

    except Exception as e:
        print("Failed to connect to the database.")
        print(f"Error: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_connection()
