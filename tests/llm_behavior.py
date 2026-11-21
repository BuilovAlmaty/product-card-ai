import asyncio
from app.services.steps import extract, generate
from app.schemas.cards import SupplierFacts, CardDraft


async def extr(prompt: str) -> SupplierFacts:
    facts = await extract(prompt)
    print("\n=== ИЗВЛЕЧЁННЫЕ ФАКТЫ ===")
    print(facts.model_dump_json(indent=2))
    return facts


async def gen(facts: SupplierFacts) -> CardDraft:
    draft = await generate(facts)
    print("\n=== СГЕНЕРИРОВАННАЯ КАРТОЧКА ===")
    print(draft.model_dump_json(indent=2))
    return draft

async def main():
    prompt = (
        "Блендер погружной МиксерПро 800. "
        "Мощность 800 Вт, питание 220 В. "
        "6 скоростей и турбо. Металлическая ножка. "
        "Гарантия 12 месяцев."
    )
    facts = await extr(prompt)
    draft = await gen(facts)
    
asyncio.run(main())