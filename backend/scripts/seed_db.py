import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import Role
from app.models.asset import AssetType, Location, InfrastructureAsset
from app.models.sensor import SensorType, DataSource, Sensor, SensorReading
from app.models.hazard import HazardType
from app.models.risk import WarningLevel

def seed() -> None:
    db: Session = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Role).first():
            print("Database already seeded.")
            return

        print("Seeding database...")
        
        # Roles
        admin_role = Role(name="Admin", description="Administrator role")
        viewer_role = Role(name="Viewer", description="Read-only access")
        db.add_all([admin_role, viewer_role])

        # Asset Types
        bridge_type = AssetType(name="Bridge", description="Suspension and concrete bridges")
        power_type = AssetType(name="Power Plant", description="Energy generation facilities")
        db.add_all([bridge_type, power_type])

        # Locations (Using WKT for PostGIS Geometry)
        # Note: SRID=4326;POINT(longitude latitude)
        loc_city = Location(name="Metropolis", geom="SRID=4326;POINT(-122.4194 37.7749)", description="Main City Center")
        loc_coast = Location(name="Coastal Zone", geom="SRID=4326;POINT(-122.5000 37.7500)", description="Vulnerable coast")
        db.add_all([loc_city, loc_coast])
        db.commit() # Commit to get IDs

        # Infrastructure Assets
        golden_gate = InfrastructureAsset(
            name="Golden Gate Bridge", 
            asset_type_id=bridge_type.id,
            location_id=loc_city.id,
            geom="SRID=4326;POINT(-122.4783 37.8199)",
            attributes={"material": "steel", "length_m": 2737}
        )
        db.add(golden_gate)
        db.commit()

        # Sensor Types
        temp_sensor = SensorType(name="Temperature Sensor", unit="C")
        strain_sensor = SensorType(name="Strain Gauge", unit="µε")
        db.add_all([temp_sensor, strain_sensor])
        db.commit()

        # Data Sources
        internal_ds = DataSource(name="Internal IoT Network", url="http://internal.iot")
        db.add(internal_ds)
        db.commit()

        # Sensors
        bridge_temp = Sensor(
            name="Bridge Deck Temp",
            sensor_type_id=temp_sensor.id,
            asset_id=golden_gate.id,
            geom="SRID=4326;POINT(-122.4783 37.8199)"
        )
        db.add(bridge_temp)
        db.commit()

        # Sensor Readings
        reading = SensorReading(
            sensor_id=bridge_temp.id,
            timestamp=datetime.now(timezone.utc),
            value=18.5,
            unit="C",
            status="OK",
            data_source_id=internal_ds.id
        )
        db.add(reading)

        # Hazard Types & Warning Levels
        flood_hazard = HazardType(name="Flood", description="Coastal and river flooding")
        earthquake_hazard = HazardType(name="Earthquake", description="Seismic events")
        db.add_all([flood_hazard, earthquake_hazard])

        warn_info = WarningLevel(name="Information", severity_level=1, color="#00FF00")
        warn_critical = WarningLevel(name="Critical", severity_level=5, color="#FF0000")
        db.add_all([warn_info, warn_critical])

        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
