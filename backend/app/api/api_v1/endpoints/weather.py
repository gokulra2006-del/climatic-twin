from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.api import deps
from app.models.weather import WeatherObservation, WeatherForecast
from app.schemas.other import WeatherResponse, WeatherForecastResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/backup-analysis")
def get_weather_backup_analysis(days: int = Query(7, ge=2, le=30)):
    """Return locally retained provider observations and a same-time comparison."""
    from app.core.satellite_ingestion import satellite_engine
    return satellite_engine.get_weather_backup_analysis(days=days)

@router.get("/current", response_model=Optional[WeatherResponse])
def get_current_weather(
    location_id: int,
    db: Session = Depends(deps.get_db)
):
    if db is not None:
        try:
            obs = db.query(WeatherObservation).filter(
                WeatherObservation.location_id == location_id
            ).order_by(WeatherObservation.timestamp.desc()).first()
            if obs:
                return obs
        except Exception:
            pass
    return None

@router.get("/observations", response_model=PaginatedResponse[WeatherResponse])
def get_observations(
    location_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(deps.get_db)
):
    if db is not None:
        try:
            query = db.query(WeatherObservation).filter(WeatherObservation.location_id == location_id)
            if start_time: query = query.filter(WeatherObservation.timestamp >= start_time)
            if end_time: query = query.filter(WeatherObservation.timestamp <= end_time)
            
            total = query.count()
            data = query.offset(skip).limit(limit).all()
            
            return {"data": data, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}
        except Exception:
            pass
    return {"data": [], "total": 0, "page": 1, "page_size": limit, "total_pages": 0}

@router.get("/forecast", response_model=PaginatedResponse[WeatherForecastResponse])
def get_forecast(
    location_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if db is not None:
        try:
            query = db.query(WeatherForecast).filter(WeatherForecast.location_id == location_id)
            total = query.count()
            data = query.offset(skip).limit(limit).all()
            return {"data": data, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}
        except Exception:
            pass
    return {"data": [], "total": 0, "page": 1, "page_size": limit, "total_pages": 0}

