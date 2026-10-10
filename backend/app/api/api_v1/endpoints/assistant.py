from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api import deps
from app.services.ai_assistant import generate_assistant_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    mode: str = Field(..., pattern="^(research|operator|citizen|evaluator)$")

class ChatResponse(BaseModel):
    answer: str
    mode: str
    sources: list[str]
    context_timestamp: str
    confidence: str

@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    request: ChatRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Endpoint for the Digital Twin AI Assistant.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    response_data = generate_assistant_response(
        db=db,
        message=request.message,
        mode=request.mode
    )
    
    return response_data
