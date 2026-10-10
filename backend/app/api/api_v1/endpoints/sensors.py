from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from geoalchemy2.elements import WKTElement

from app.api import deps
from app.models.sensor import Sensor, SensorReading
from app.schemas.sensor import SensorCreate, Sensor as SensorSchema, SensorReading as SensorReadingSchema
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=PaginatedResponse[SensorSchema])
def read_sensors(
    db: Session = Depends(deps.get_db_optional),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    asset_id: Optional[int] = None
):
    if db:
        try:
            query = db.query(Sensor)
            if asset_id:
                query = query.filter(Sensor.asset_id == asset_id)
                
            total = query.count()
            sensors = query.offset(skip).limit(limit).all()
            
            return {
                "data": sensors,
                "total": total,
                "page": skip // limit + 1 if limit > 0 else 1,
                "page_size": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0
            }
        except Exception as e:
            logger.warning(f"DB error fetching sensors: {e}")
            
    # Check Firebase for Raspberry Pi connection
    from app.core.firebase_client import get_firebase_telemetry
    firebase_data = get_firebase_telemetry()
    
    now = datetime.now(timezone.utc)
    if firebase_data:
        # If Raspberry Pi is connected, return real hardware status
        return {
            "data": [
                {"id": 1, "name": "RASPBERRY_PI_SENSOR", "sensor_type_id": 1, "asset_id": 1, "is_active": True, "created_at": now}
            ],
            "total": 1,
            "page": 1,
            "page_size": limit,
            "total_pages": 1
        }
            
    # Mock fallback (ONLY runs if DB is offline AND Raspberry Pi is not connected)
    return {
        "data": [
            {"id": 1, "name": "POONDI_INFLOW_STATION", "sensor_type_id": 1, "asset_id": 1, "is_active": True, "created_at": now},
            {"id": 2, "name": "REDHILLS_LEVEL_SENSOR", "sensor_type_id": 1, "asset_id": 2, "is_active": True, "created_at": now},
            {"id": 3, "name": "ADYAR_RIVER_GAUGE", "sensor_type_id": 2, "asset_id": 3, "is_active": True, "created_at": now}
        ],
        "total": 3,
        "page": 1,
        "page_size": limit,
        "total_pages": 1
    }


@router.get("/{sensor_id}", response_model=SensorSchema)
def read_sensor(
    sensor_id: int, 
    db: Session = Depends(deps.get_db)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@router.post("/", response_model=SensorSchema, status_code=201)
def create_sensor(
    sensor_in: SensorCreate, 
    db: Session = Depends(deps.get_db)
):
    db_sensor = Sensor(
        name=sensor_in.name,
        sensor_type_id=sensor_in.sensor_type_id,
        asset_id=sensor_in.asset_id,
        is_active=sensor_in.is_active
    )
    if sensor_in.geom:
        db_sensor.geom = WKTElement(sensor_in.geom, srid=4326)
        
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor

@router.delete("/{sensor_id}")
def delete_sensor(
    sensor_id: int, 
    db: Session = Depends(deps.get_db)
):
    db_sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not db_sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    db.delete(db_sensor)
    db.commit()
    return {"message": "Sensor deleted successfully"}

@router.get("/{sensor_id}/readings", response_model=PaginatedResponse[SensorReadingSchema])
def read_sensor_readings_for_sensor(
    sensor_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    query = db.query(SensorReading).filter(SensorReading.sensor_id == sensor_id)
    total = query.count()
    readings = query.order_by(SensorReading.timestamp.desc()).offset(skip).limit(limit).all()
    
    return {
        "data": readings,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 0
    }
