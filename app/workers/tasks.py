import asyncio

from app.workers.celery_app import celery_app
from app.services.steps import extract, generate, critique
from app.core.db import session_factory
from app.repositories.jobs import set_status, get_job
from app.schemas.cards import SupplierFacts, CardDraft

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import Settings


settings = Settings()

worker_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
)

worker_session_factory = async_sessionmaker(
    worker_engine,
    expire_on_commit=False,
)


MAX_ATTEMPTS = 3


async def process_card(
        job_id: str,
        supplier_text: str,
        feedback: list[str] | None = None
):
    async with worker_session_factory() as session:
        try:
            await set_status(session, job_id, "extracting")
            facts = await extract(supplier_text)

            await set_status(
                session,
                job_id,
                "generating",
                bump_attempts=True,            
            )
            draft = await generate(facts, feedback)
            
            await set_status(session, job_id, "critiquing")
            celery_app.send_task(
                "app.workers.tasks.critique_card",
                kwargs={
                    "job_id": job_id,
                    "facts_json": facts.model_dump_json(),
                    "draft_json": draft.model_dump_json(),
                    "supplier_text": supplier_text,
                },
                queue="card.critique"    
            )

        except Exception as e:
            await set_status(
                session,
                job_id,
                "failed",
                error=repr(e)
            )
            raise


@celery_app.task(name="app.workers.tasks.generate_card")
def generate_card(
    job_id: str,
    supplier_text: str,
    feedback: list[str] | None = None
):
    asyncio.run(process_card(job_id, supplier_text, feedback))


async def process_critique(
    job_id: str,
    facts_json: str,
    draft_json: str,
    supplier_text: str,
):
    print(f"[CRITIQUE] Начало обработки: {job_id}", flush=True)
    facts = SupplierFacts.model_validate_json(facts_json)
    draft = CardDraft.model_validate_json(draft_json)
    print("[CRITIQUE] Отправляем запрос в LLM", flush=True)

    async with worker_session_factory() as session:
        try:
            report = await critique(facts, draft)

            print(
                f"[CRITIQUE] Ответ модели: {report.verdict}",
                flush=True,
            )

            if report.verdict == "approve":
                await set_status(
                    session,
                    job_id,
                    "approved",
                    result=draft.model_dump(),
                )
                return

            job = await get_job(session, job_id)

            if job is None:
                raise ValueError(F"Job {job_id} not found")

            if job.attempts >= MAX_ATTEMPTS:
                await set_status(
                    session,
                    job_id,
                    "rejected",
                    result=draft.model_dump(),
                )
                return

            await set_status(
                    session,
                    job_id,
                    "regenerating",
                )

            celery_app.send_task(
                "app.workers.tasks.generate_card",
                kwargs={
                    "job_id": job_id,
                    "supplier_text": supplier_text,
                    "feedback": report.issues
                },
                queue="card.generate"
            )

        except Exception as e:
            await set_status(
                session,
                job_id,
                "failed",
                error=repr(e)
            )
            raise 


@celery_app.task(name="app.workers.tasks.critique_card")
def critique_card(
    job_id:str,
    facts_json: str,
    draft_json: str,
    supplier_text: str,
):
    asyncio.run(process_critique(job_id, facts_json, draft_json, supplier_text))