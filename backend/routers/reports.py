"""Report generation endpoint."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import ReportResponse
from services.report_service import generate_report, get_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{case_id}", response_model=ReportResponse)
async def get_case_report(case_id: str, db: AsyncSession = Depends(get_db)):
    report = await get_report(db, case_id)
    if not report:
        raise HTTPException(404, "Report not found. Generate it first via POST.")
    return report


@router.post("/{case_id}/generate", response_model=ReportResponse)
async def generate_case_report(case_id: str, db: AsyncSession = Depends(get_db)):
    try:
        report = await generate_report(db, case_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return report
