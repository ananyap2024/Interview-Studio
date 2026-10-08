import json
import logging
import re
from threading import Lock
from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from ..config import settings


logger = logging.getLogger(__name__)
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
MAX_ATTEMPTS_PER_STAGE = 2
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
CALL_LABELS = {
    "resume_analysis": "resume_analysis",
    "question_generation": "question_generation",
    "answer_evaluation": "answer_evaluation",
}


class GeminiServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _decode_json(text: str) -> object:
    candidates = [text.strip()]
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in dict.fromkeys(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Gemini returned invalid JSON.")


class GeminiService:
    def __init__(self) -> None:
        self._attempts: dict[tuple[str, str], int] = {}
        self._attempt_lock = Lock()

    def _claim_attempt(self, interview_id: str, stage: str) -> None:
        key = (interview_id, stage)
        with self._attempt_lock:
            attempts = self._attempts.get(key, 0)
            if attempts >= MAX_ATTEMPTS_PER_STAGE:
                raise GeminiServiceError("This AI step has used its retry. Please start a new interview.", 409)
            self._attempts[key] = attempts + 1

    async def _request_text(self, stage: str, prompt: str, schema: dict[str, object]) -> str:
        api_key = settings.gemini_api_key
        if not api_key:
            raise GeminiServiceError("AI service is not configured.", 503)
        model = quote(settings.llm_model, safe="-")
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
                "temperature": 0.2,
                "maxOutputTokens": 3200,
            },
        }
        logger.info("Gemini call: %s", CALL_LABELS[stage])
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers={"x-goog-api-key": api_key},
                json=payload,
            )
        if response.status_code >= 400:
            raise httpx.HTTPStatusError("Gemini request failed.", request=response.request, response=response)
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        if not text:
            raise ValueError("Gemini returned no structured output.")
        return text

    async def generate_structured(
        self,
        interview_id: str,
        stage: str,
        prompt: str,
        response_model: type[ResponseModel],
    ) -> ResponseModel:
        if stage not in CALL_LABELS:
            raise ValueError("Unknown Gemini call stage.")
        if not settings.gemini_api_key:
            raise GeminiServiceError("AI service is not configured.", 503)
        last_error: Exception | None = None
        for _ in range(MAX_ATTEMPTS_PER_STAGE):
            self._claim_attempt(interview_id, stage)
            try:
                response_text = await self._request_text(stage, prompt, response_model.model_json_schema())
                return response_model.model_validate(_decode_json(response_text))
            except GeminiServiceError:
                raise
            except (httpx.HTTPError, ValueError, ValidationError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in RETRYABLE_STATUS_CODES:
                    break
        raise GeminiServiceError("The AI response could not be completed. Your interview data has been preserved.") from last_error


gemini_service = GeminiService()