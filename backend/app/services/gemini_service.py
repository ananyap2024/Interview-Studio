import hashlib
import json
import logging
import re
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
    @staticmethod
    def _safe_interview_ref(interview_id: str) -> str:
        return hashlib.sha256(interview_id.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _claim_attempt(interview_id: str, stage: str, attempt: int) -> None:
        if not 1 <= attempt <= MAX_ATTEMPTS_PER_STAGE:
            logger.warning(
                "Gemini attempt rejected interview_ref=%s stage=%s attempt=%d category=retry_exhausted",
                GeminiService._safe_interview_ref(interview_id),
                CALL_LABELS.get(stage, "unknown_stage"),
                attempt,
            )
            raise GeminiServiceError("This AI step has used its retry. Please start a new interview.", 409)

    async def _request_text(
        self,
        interview_id: str,
        stage: str,
        attempt: int,
        prompt: str,
        schema: dict[str, object],
    ) -> str:
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
        interview_ref = self._safe_interview_ref(interview_id)
        logger.info(
            "Gemini request started interview_ref=%s stage=%s attempt=%d",
            interview_ref,
            CALL_LABELS[stage],
            attempt,
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers={"x-goog-api-key": api_key},
                json=payload,
            )
        logger.info(
            "Gemini response received interview_ref=%s stage=%s attempt=%d status=%d",
            interview_ref,
            CALL_LABELS[stage],
            attempt,
            response.status_code,
        )
        if response.status_code >= 400:
            raise httpx.HTTPStatusError("Gemini request failed.", request=response.request, response=response)
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Gemini returned an invalid response envelope.")
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
            raise ValueError("Gemini returned an invalid response envelope.")
        content = candidates[0].get("content")
        if not isinstance(content, dict):
            raise ValueError("Gemini returned an invalid response envelope.")
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise ValueError("Gemini returned an invalid response envelope.")
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
        interview_ref = self._safe_interview_ref(interview_id)
        for attempt in range(1, MAX_ATTEMPTS_PER_STAGE + 1):
            self._claim_attempt(interview_id, stage, attempt)
            try:
                response_text = await self._request_text(
                    interview_id,
                    stage,
                    attempt,
                    prompt,
                    response_model.model_json_schema(),
                )
            except GeminiServiceError:
                raise
            except httpx.TimeoutException as exc:
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=timeout message=request timed out",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                )
                last_error = exc
                continue
            except httpx.NetworkError as exc:
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=network message=network request failed",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                )
                last_error = exc
                continue
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=provider_http status=%d message=Gemini provider returned HTTP %d",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                    status_code,
                    status_code,
                )
                last_error = exc
                if status_code not in RETRYABLE_STATUS_CODES:
                    break
                continue
            except httpx.HTTPError as exc:
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=network message=HTTP transport failed",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                )
                last_error = exc
                continue
            except ValueError as exc:
                category = "provider_response_failure"
                message = "Gemini returned an unreadable response"
                if isinstance(exc, json.JSONDecodeError):
                    category = "provider_response_json_failure"
                    message = "Gemini returned invalid response JSON"
                elif str(exc) == "Gemini returned no structured output.":
                    category = "structured_json_failure"
                    message = str(exc)
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=%s message=%s",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                    category,
                    message,
                )
                last_error = exc
                continue

            try:
                decoded = _decode_json(response_text)
            except ValueError as exc:
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=structured_json_failure message=%s",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                    str(exc),
                )
                last_error = exc
                continue

            try:
                return response_model.model_validate(decoded)
            except ValidationError as exc:
                error_summary = "; ".join(
                    f"{'.'.join(str(part) for part in error['loc']) or '<root>'}: {error['type']}"
                    for error in exc.errors(include_input=False)
                )[:300]
                logger.warning(
                    "Gemini attempt failed interview_ref=%s stage=%s attempt=%d category=pydantic_validation_failure validation_error=%s",
                    interview_ref,
                    CALL_LABELS[stage],
                    attempt,
                    error_summary,
                )
                last_error = exc
        raise GeminiServiceError("The AI response could not be completed. Your interview data has been preserved.") from last_error


gemini_service = GeminiService()