from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import ChatRequest, ChatResponse
from backend.services.chat_service import answer_question

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    answer = answer_question(db, request.dataset_id, request.question)
    return ChatResponse(answer=answer)
