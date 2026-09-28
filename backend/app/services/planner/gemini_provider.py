import json
import logging
from typing import Optional
import httpx
from app.config import settings
from app.schemas.planner import PlannerOutput
from app.services.planner.base import BasePlannerProvider
from app.services.planner.openai_provider import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class GeminiPlannerProvider(BasePlannerProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def generate_plan(self, prompt: str, target_count: int = 30) -> PlannerOutput:
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")

        # Google Gemini REST endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        user_message = f"User Request: {prompt}\nTarget Record Count: {target_count}\nGenerate the complete structured data collection workflow JSON."
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "parts": [{"text": user_message}]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed_json = json.loads(content)
            return PlannerOutput.model_validate(parsed_json)
