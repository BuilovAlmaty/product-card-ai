from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas.cards import CardDraft
from app.services.steps import run_pipeline

router = APIRouter(prefix="/cards", tags=["Cards"])


class CardRequest(BaseModel):
    supplier_text: str = Field(min_length=1)


@router.post("", response_model=CardDraft)
async def create_card(body: CardRequest) -> dict[str, str]:
    draft, report = await run_pipeline(body.supplier_text)
    return draft