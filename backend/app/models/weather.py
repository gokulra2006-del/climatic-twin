from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class WeatherObservation(Base):
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature = Column(Float, nullable=True) # Celsius
    precipitation = Column(Float, nullable=True) # mm
    humidity = Column(Float, nullable=True) # %
    wind_speed = Column(Float, nullable=True) # m/s
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    
    location = relationship("Location", back_populates="weather_observations")
    data_source = relationship("DataSource", back_populates="weather_observations")

class WeatherForecast(Base):
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True) # when forecast was made
    forecast_time = Column(DateTime(timezone=True), nullable=False, index=True) # time it predicts
    temperature = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    
    location = relationship("Location", back_populates="weather_forecasts")
