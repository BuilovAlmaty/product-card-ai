from openai import AsyncOpenAI

from app.core.config import Settings
from pydantic import BaseModel


settings = Settings()

async def generate_text(
        promt: str, 
        *, 
        response_model: type[BaseModel] | None = None,
        ) -> str:
    if not settings.llm_base_url or not settings.llm_model:
        raise RuntimeError("Check content in variables llm_base_url and llm_model.")

    extra_body = None
    if response_model is not None:
        extra_body = {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema()
                }
            }
        }
    
    async with AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        ) as client:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": promt}],
            extra_body=extra_body
        )
    return response.choices[0].message.content or ""