from app.models.job import Job 
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update


async def create_job(
        session: AsyncSession, 
        supplier_text: str
    ) -> Job:
    job = Job(
        id=uuid4().hex,
        status="pending",
        payload={"supplier_text": supplier_text}
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    return job


async def set_status(
    session: AsyncSession,
    job_id: str,
    status: str,
    *,
    result: dict | None = None,
    error: str | None = None,
    bump_attempts: bool = False,
) -> None:
    values = {"status": status}

    if result is not None:
        values["result"] = result

    if error is not None:
        values["error"] = error

    if bump_attempts:
        values["attempts"] = Job.attempts + 1

    await session.execute(
        update(Job).where(Job.id == job_id).values(**values)
    )
    await session.commit()


async def get_job(session: AsyncSession, job_id: str) -> Job | None:
    return await session.get(Job, job_id)