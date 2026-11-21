from app.schemas.cards import SupplierFacts, CardDraft, CritiqueReport
from app.llm.client import generate_text
import time


async def extract(supplier_text: str) -> SupplierFacts:
    prompt = (
        "Ты — специалист по извлечению характеристик товаров.\n"
        "Извлеки ВСЕ факты из текста поставщика.\n"
        "Правила:\n"
        "1. В product_name запиши полное название товара, включая модель.\n"
        "2. В characteristics запиши ВСЕ указанные характеристики.\n"
        "3. Сохраняй числовые значения и единицы измерения.\n"
        "4. Не придумывай характеристики, которых нет в тексте.\n"
        "5. В missing_fields указывай только явно необходимые, "
        "но отсутствующие характеристики.\n"
        "6. Не заменяй отсутствующие значения строкой 'нет данных'.\n\n"
        f"Текст поставщика:\n{supplier_text}"
    )
    raw = await generate_text(prompt, response_model=SupplierFacts)
    return SupplierFacts.model_validate_json(raw)

async def generate(facts: SupplierFacts, feedback: list[str] | None = None) -> CardDraft:
    prompt = (
        "Составь карточку товара на русском языке по переданным фактам. "
        "Заголовок сделай коротким, описание — в 1–2 предложения. "
        "Перенеси характеристики без изменений. "
        # "Тон описания должен содержат пассивную агрессию."
        "Если факты не подтверждают ни одного преимущества, верни benefits: [].\n\n"
        f"Факты о товаре:\n{facts.model_dump_json(indent=2)}"
    )
    if feedback:
        issues = "\n".join(f"- {issue}" for issue in feedback)
        prompt += f"\n\nИсправь замечания критика:\n{issues}"
    raw = await generate_text(promt=prompt, response_model=CardDraft)
    return CardDraft.model_validate_json(raw)


async def critique(facts: SupplierFacts, draft: CardDraft) -> CritiqueReport:
    prompt = (
        "Сверь черновик карточки с фактами поставщика. "
        "Проверь характеристики, название модели и утверждения о качестве. "
        "Если есть неподтверждённое утверждение или искажённый факт, "
        "верни regenerate и перечисли конкретные проблемы в issues. "
        "Иначе верни approve и пустой список issues.\n\n"
        f"Факты поставщика:\n{facts.model_dump_json(indent=2)}\n\n"
        f"Черновик:\n{draft.model_dump_json(indent=2)}"
    )
    raw = await generate_text(promt=prompt, response_model=CritiqueReport)
    return CritiqueReport.model_validate_json(raw)        


async def run_pipeline(
        supplier_text: str, 
        max_attempts: int = 3
        ) -> tuple[CardDraft, CritiqueReport]:
    start = time.perf_counter()
    facts = await extract(supplier_text=supplier_text)
    feedback: list[str] | None = None
    for attempt in range(1, max_attempts + 1):
        draft = await generate(facts=facts, feedback=feedback)
        report = await critique(facts, draft)

        if report.verdict == "approve" or attempt == max_attempts:
            print(f"Время вызова: {time.perf_counter() - start:.3f}")
            return draft, report

        feedback = report.issues

    raise ValueError("max_attempts должно быть не меньше 1")

