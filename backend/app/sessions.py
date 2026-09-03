from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user
from app.db import get_db
from app.models import PromptTemplate
from app.models import Session as SessionModel

router = APIRouter(dependencies=[Depends(require_user)])


class PromptTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    interview_focus: str
    is_system: bool

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    format_id: uuid.UUID


class SessionOut(BaseModel):
    id: uuid.UUID
    format_id: uuid.UUID
    status: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("/prompt-templates", response_model=list[PromptTemplateOut])
async def list_prompt_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptTemplate).order_by(PromptTemplate.name))
    return result.scalars().all()


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    template = await db.get(PromptTemplate, body.format_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown format_id")

    session = SessionModel(user_id=uuid.UUID(user_id), format_id=body.format_id, status="offen")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.user_id == uuid.UUID(user_id))
        .order_by(SessionModel.created_at)
    )
    return result.scalars().all()
