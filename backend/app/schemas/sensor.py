from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
class DataSourceBase(BaseModel):
    name: str
    provider: Optional[str] = None
    dataset_name: Optional[str] = None
    version: Optional[str] = None
    url: Optional[str] = None
    license: Optional[str] = None
    description: Optional[str] = None
    hazard_applicability: Optional[str] = None
    validation_status: Optional[str] = None

class DataSourceResponse(DataSourceBase):
    id: int
    class Config: from_attributes = True

class SensorReadingBase(BaseModel):
    value: float
    unit: Optional[str] = None
    status: Optional[str] = None
    data_source_id: Optional[int] = None

class SensorReadingCreate(SensorReadingBase):
    sensor_id: int
    timestamp: datetime

class SensorReading(SensorReadingBase):
    id: int
    sensor_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class SensorBase(BaseModel):
    name: str
    sensor_type_id: int
    asset_id: Optional[int] = None
    is_active: bool = True

class SensorCreate(SensorBase):
    geom: Optional[str] = None # WKT format for creation if needed

class Sensor(SensorBase):
    id: int
    created_at: datetime    
    class Config:
        from_attributes = True
