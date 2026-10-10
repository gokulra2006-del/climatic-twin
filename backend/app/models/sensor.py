from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.base_class import Base

class SensorType(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    unit = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    sensors = relationship("Sensor", back_populates="sensor_type")

class DataSource(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    provider = Column(String, nullable=True)
    dataset_name = Column(String, nullable=True)
    version = Column(String, nullable=True)
    url = Column(String, nullable=True)
    license = Column(String, nullable=True)
    description = Column(String, nullable=True)
    hazard_applicability = Column(String, nullable=True)
    validation_status = Column(String, nullable=True)
    
    sensor_readings = relationship("SensorReading", back_populates="data_source")
    weather_observations = relationship("WeatherObservation", back_populates="data_source")

class Sensor(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    sensor_type_id = Column(Integer, ForeignKey("sensor_types.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("infrastructure_assets.id"), nullable=True)
    geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sensor_type = relationship("SensorType", back_populates="sensors")
    asset = relationship("InfrastructureAsset", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")

class SensorReading(Base):
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    status = Column(String, nullable=True) # e.g., 'OK', 'ERROR', 'WARNING'
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    
    sensor = relationship("Sensor", back_populates="readings")
    data_source = relationship("DataSource", back_populates="sensor_readings")
