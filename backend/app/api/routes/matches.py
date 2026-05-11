"""Match-related endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.match import Match
from app.schemas.match import MatchOut

router = APIRouter()


@router.get("", response_model=list[MatchOut], summary="List recently observed matches")
async def list_matches(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[Match]:
    rows = await db.execute(select(Match).order_by(Match.updated_at.desc()).limit(limit))
    return list(rows.scalars().all())
