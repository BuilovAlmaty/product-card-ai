from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.repositories.jobs import create_job, get_job
from app.workers.celery_app import celery_app


router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobRequest(BaseModel):
    supplier_text: str = Field(min_length=1)


@router.post("", status_code=202)
async def submit_job(
    body: JobRequest,
    session: AsyncSession = Depends(get_db),
):
    job = await create_job(session, body.supplier_text)

    celery_app.send_task(
        "app.workers.tasks.generate_card",
        kwargs={
            "job_id": job.id,
            "supplier_text": body.supplier_text,
        },
        queue="card.generate"
    )

    return {
        "id": job.id,
        "status": job.status,
    }


@router.get("/{job_id}")
async def job_status(
    job_id: str, 
    session: AsyncSession = Depends(get_db),
):
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found!")

    return {
        "id": job.id,
        "status": job.status,
        "attempts": job.attempts,
        "result": job.result,
        "error": job.error,
    }