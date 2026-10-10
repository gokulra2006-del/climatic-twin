from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api import deps
from app.models.sensor import SensorReading, Sensor
from app.schemas.sensor import SensorReadingCreate, SensorReading as SensorReadingSchema
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.post("/", response_model=SensorReadingSchema, status_code=201)
def create_sensor_reading(
    reading_in: SensorReadingCreate, 
    db: Session = Depends(deps.get_db)
):
    # Validate sensor exists
    sensor = db.query(Sensor).filter(Sensor.id == reading_in.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=400, detail="Invalid sensor_id")
        
    db_reading = SensorReading(
        sensor_id=reading_in.sensor_id,
        timestamp=reading_in.timestamp,
        value=reading_in.value,
        unit=reading_in.unit,
        status=reading_in.status,
        data_source_id=reading_in.data_source_id
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading

@router.get("/", response_model=PaginatedResponse[SensorReadingSchema])
def read_sensor_readings(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sensor_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    query = db.query(SensorReading)
    
    if sensor_id:
        query = query.filter(SensorReading.sensor_id == sensor_id)
    if start_time:
        query = query.filter(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.filter(SensorReading.timestamp <= end_time)
        
    total = query.count()
    readings = query.order_by(SensorReading.timestamp.desc()).offset(skip).limit(limit).all()
    
    return {
        "data": readings,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 0
    }
