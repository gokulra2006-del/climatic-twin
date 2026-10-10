from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AssetBase(BaseModel):
    name: str
    asset_type_id: int
    location_id: Optional[int] = None
    geom: Optional[str] = None # WKT format
    attributes: Optional[Dict[str, Any]] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type_id: Optional[int] = None
    location_id: Optional[int] = None
    geom: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class AssetResponse(AssetBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
