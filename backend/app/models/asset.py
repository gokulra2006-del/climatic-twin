from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.base_class import Base

class AssetType(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    assets = relationship("InfrastructureAsset", back_populates="asset_type")

class Location(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    # Using SRID 4326 for standard GPS coordinates (longitude, latitude)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326), nullable=True)
    description = Column(String, nullable=True)
    
    assets = relationship("InfrastructureAsset", back_populates="location")
    weather_observations = relationship("WeatherObservation", back_populates="location")
    weather_forecasts = relationship("WeatherForecast", back_populates="location")

class InfrastructureAsset(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    asset_type_id = Column(Integer, ForeignKey("asset_types.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    asset_type = relationship("AssetType", back_populates="assets")
    location = relationship("Location", back_populates="assets")
    sensors = relationship("Sensor", back_populates="asset")
    twin_states = relationship("DigitalTwinState", back_populates="asset")
    predictions = relationship("ModelPrediction", back_populates="asset")
