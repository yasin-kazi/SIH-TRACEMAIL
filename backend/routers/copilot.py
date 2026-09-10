"""AI Copilot chat endpoint."""
from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import CopilotMessageRecord
from schemas import CopilotMessageResponse, CopilotAskRequest
from services.copilot_service import get_copilot_response

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.get("/{case_id}/messages", response_model=list[CopilotMessageResponse])
async def get_messages(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CopilotMessageRecord)
        .where(CopilotMessageRecord.case_id == case_id)
        .order_by(CopilotMessageRecord.id)
    )
    msgs = result.scalars().all()
    if not msgs:
        greeting = CopilotMessageRecord(
            case_id=case_id,
            msg_id=f"msg-{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=f"I'm the TraceMail AI investigation copilot. I can help you analyze this case. Ask me about threat indicators, evidence, identity analysis, infrastructure, or attack patterns.",
            timestamp=datetime.utcnow().strftime("%H:%M:%S UTC"),
        )
        db.add(greeting)
        await db.commit()
        return [_msg_to_response(greeting)]
    return [_msg_to_response(m) for m in msgs]


@router.post("/{case_id}/ask", response_model=CopilotMessageResponse)
async def ask_copilot(
    case_id: str,
    req: CopilotAskRequest,
    db: AsyncSession = Depends(get_db),
):
    # Save user message
    user_msg = CopilotMessageRecord(
        case_id=case_id,
        msg_id=f"msg-{uuid.uuid4().hex[:8]}",
        role="user",
        content=req.question,
        timestamp=datetime.utcnow().strftime("%H:%M:%S UTC"),
    )
    db.add(user_msg)

    # Get AI response
    response_text = await get_copilot_response(db, case_id, req.question)

    assistant_msg = CopilotMessageRecord(
        case_id=case_id,
        msg_id=f"msg-{uuid.uuid4().hex[:8]}",
        role="assistant",
        content=response_text,
        timestamp=datetime.utcnow().strftime("%H:%M:%S UTC"),
    )
    db.add(assistant_msg)
    await db.commit()

    return _msg_to_response(assistant_msg)


@router.post("/{case_id}/suggested-questions")
async def get_suggested_questions(case_id: str):
    return {
        "questions": [
            "Why is this email high risk?",
            "What is the strongest evidence?",
            "Show identity contradictions.",
            "What infrastructure is connected?",
            "Are there related cases?",
            "Explain the probable attack path.",
            "What evidence is uncertain?",
            "Analyze authentication results.",
            "Tell me about the domain.",
            "Show the investigation timeline.",
        ]
    }


def _msg_to_response(msg: CopilotMessageRecord) -> CopilotMessageResponse:
    return CopilotMessageResponse(
        id=msg.msg_id,
        role=msg.role,
        content=msg.content,
        timestamp=msg.timestamp,
    )
