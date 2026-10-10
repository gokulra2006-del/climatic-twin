from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

# Weather
class WeatherBase(BaseModel):
    location_id: int
    temperature: Optional[float] = None
    precipitation: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None

class WeatherResponse(WeatherBase):
    id: int
    timestamp: datetime
    class Config: from_attributes = True

class WeatherForecastResponse(WeatherBase):
    id: int
    timestamp: datetime
    forecast_time: datetime
    class Config: from_attributes = True

# Hazard
class HazardTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    implementation_status: Optional[str] = "PLANNED"

class HazardTypeResponse(HazardTypeBase):
    id: int
    class Config: from_attributes = True

class HazardEventBase(BaseModel):
    hazard_type_id: int
    name: Optional[str] = None
    severity: Optional[str] = None
    geom: Optional[str] = None

class HazardEventCreate(HazardEventBase):
    start_time: datetime
    end_time: Optional[datetime] = None

class HazardEventResponse(HazardEventCreate):
    id: int
    class Config: from_attributes = True

# Digital Twin
class TwinBase(BaseModel):
    asset_id: int
    state_data: Dict[str, Any]

class TwinResponse(TwinBase):
    id: int
    timestamp: datetime
    class Config: from_attributes = True

# Prediction
class PredictionBase(BaseModel):
    model_id: int
    asset_id: Optional[int] = None
    forecast_horizon: Optional[int] = None
    predicted_value: Optional[float] = None
    probability: Optional[float] = None

class PredictionResponse(PredictionBase):
    id: int
    prediction_time: datetime
    class Config: from_attributes = True

# Risk
class RiskBase(BaseModel):
    twin_state_id: int
    risk_score: float
    details: Optional[Dict[str, Any]] = None

class RiskResponse(RiskBase):
    id: int
    timestamp: datetime
    class Config: from_attributes = True

# Alert
class AlertBase(BaseModel):
    warning_level_id: int
    risk_assessment_id: Optional[int] = None
    message: str
    is_active: bool = True

class AlertCreate(AlertBase): pass
class AlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    resolved_at: Optional[datetime] = None

class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    class Config: from_attributes = True

# Historical
class HistoricalEventBase(BaseModel):
    hazard_event_id: int
    description: Optional[str] = None
    impact_summary: Optional[str] = None

class HistoricalEventCreate(HistoricalEventBase): pass
class HistoricalEventResponse(HistoricalEventBase):
    id: int
    class Config: from_attributes = True
