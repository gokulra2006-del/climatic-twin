from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.hazard import HistoricalEvent
from app.schemas.other import HistoricalEventCreate, HistoricalEventResponse
from app.schemas.common import PaginatedResponse
router = APIRouter()

@router.get("/", response_model=PaginatedResponse[HistoricalEventResponse])
def get_historical_events(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if db is not None:
        try:
            query = db.query(HistoricalEvent)
            total = query.count()
            events = query.offset(skip).limit(limit).all()
            return {"data": events, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}
        except Exception:
            pass
    return {"data": [], "total": 0, "page": 1, "page_size": limit, "total_pages": 0}

@router.get("/{event_id}", response_model=HistoricalEventResponse)
def get_historical_event(event_id: int, db: Session = Depends(deps.get_db)):
    if db is not None:
        try:
            event = db.query(HistoricalEvent).filter(HistoricalEvent.id == event_id).first()
            if event:
                return event
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Historical event not found")


@router.post("/", response_model=HistoricalEventResponse, status_code=201)
def create_historical_event(event_in: HistoricalEventCreate, db: Session = Depends(deps.get_db)):
    db_event = HistoricalEvent(
        hazard_event_id=event_in.hazard_event_id,
        description=event_in.description,
        impact_summary=event_in.impact_summary
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
