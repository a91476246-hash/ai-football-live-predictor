"""Prediction endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionOut

router = APIRouter()


@router.get("", response_model=list[PredictionOut], summary="List predictions")
async def list_predictions(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[Prediction]:
    rows = await db.execute(select(Prediction).order_by(Prediction.created_at.desc()).limit(limit))
    return list(rows.scalars().all())
