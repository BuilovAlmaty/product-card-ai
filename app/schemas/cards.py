from pydantic import BaseModel
from typing import Literal


class SupplierFacts(BaseModel):
    product_name: str
    characteristics: dict[str, str]
    missing_fields: list[str]


class CardDraft(BaseModel):
    title: str
    description: str
    characteristics: dict[str, str]
    benefits: list[str]


class CritiqueReport(BaseModel):
    verdict: Literal["approve", "regenerate"]
    issues: list[str]