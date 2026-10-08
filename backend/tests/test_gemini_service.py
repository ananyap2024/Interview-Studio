import json

import httpx
import pytest

from app.schemas.evaluation import EvaluationResponse
from app.schemas.profile import CandidateProfile
from app.services import gemini_service as service_module
from app.services.gemini_service import GeminiService, GeminiServiceError


def valid_evaluation() -> dict[str, object]:
    return {
        "evaluations": [
            {
                "question_id": question_id,
                "score": 8,
                "correctness": 8,
                "relevance": 7,
                "completeness": 8,
                "clarity": 8,
                "depth": 9,
                "feedback": f"Feedback for {question_id}",
                "strengths": ["Clear explanation"],
                "improvements": ["Add an example"],
            }
            for question_id in range(6, 11)
        ],
        "strengths": ["Clear explanations"],
        "weaknesses": ["Could add examples"],
        "recommended_topics": ["Testing"],
        "overall_assessment": "A strong technical foundation.",
    }


def provider_error(status_code: int = 503) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.test/generateContent")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("Gemini request failed.", request=request, response=response)


@pytest.mark.anyio
async def test_theoretical_evaluation_succeeds_with_one_mocked_request(monkeypatch) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    calls = 0

    async def fake_request(*args) -> str:
        nonlocal calls
        calls += 1
        return json.dumps(valid_evaluation())

    monkeypatch.setattr(service, "_request_text", fake_request)
    result = await service.generate_structured(
        "test-interview-123",
        "answer_evaluation",
        "mock theoretical evaluation prompt",
        EvaluationResponse,
    )

    assert len(result.evaluations) == 5
    assert calls == 1


@pytest.mark.anyio
async def test_provider_failure_retries_once_then_succeeds(monkeypatch, caplog) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    calls = 0

    async def fake_request(*args) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise provider_error()
        return json.dumps(valid_evaluation())

    monkeypatch.setattr(service, "_request_text", fake_request)
    result = await service.generate_structured(
        "test-interview-123",
        "answer_evaluation",
        "mock theoretical evaluation prompt",
        EvaluationResponse,
    )

    assert len(result.evaluations) == 5
    assert calls == 2
    assert "category=provider_http status=503" in caplog.text
    assert "attempt=1" in caplog.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("failure_type", "category"),
    [(httpx.ReadTimeout, "timeout"), (httpx.ConnectError, "network")],
)
async def test_timeout_and_network_failures_are_logged_and_retried(
    monkeypatch,
    caplog,
    failure_type,
    category: str,
) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    calls = 0

    async def fake_request(*args) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise failure_type("mock transport failure")
        return json.dumps(valid_evaluation())

    monkeypatch.setattr(service, "_request_text", fake_request)
    result = await service.generate_structured(
        "test-interview-123",
        "answer_evaluation",
        "mock theoretical evaluation prompt",
        EvaluationResponse,
    )

    assert len(result.evaluations) == 5
    assert calls == 2
    assert f"category={category}" in caplog.text


@pytest.mark.anyio
async def test_two_failed_attempts_exhaust_invocation_and_later_submit_can_retry(monkeypatch) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    calls = 0

    async def fake_request(*args) -> str:
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise provider_error()
        return json.dumps(valid_evaluation())

    monkeypatch.setattr(service, "_request_text", fake_request)
    with pytest.raises(GeminiServiceError, match="AI response could not be completed"):
        await service.generate_structured(
            "test-interview-123",
            "answer_evaluation",
            "mock theoretical evaluation prompt",
            EvaluationResponse,
        )
    assert calls == 2

    result = await service.generate_structured(
        "test-interview-123",
        "answer_evaluation",
        "mock theoretical evaluation prompt",
        EvaluationResponse,
    )
    assert len(result.evaluations) == 5
    assert calls == 3


def test_attempt_guard_rejects_attempt_beyond_existing_limit() -> None:
    with pytest.raises(GeminiServiceError, match="used its retry"):
        GeminiService._claim_attempt("test-interview-123", "answer_evaluation", 3)


@pytest.mark.anyio
async def test_structured_response_validation_failure_is_logged_and_retried(monkeypatch, caplog) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    responses = iter([
        json.dumps({**valid_evaluation(), "evaluations": []}),
        json.dumps(valid_evaluation()),
    ])

    async def fake_request(*args) -> str:
        return next(responses)

    monkeypatch.setattr(service, "_request_text", fake_request)
    result = await service.generate_structured(
        "test-interview-123",
        "answer_evaluation",
        "mock prompt containing candidate-private-answer",
        EvaluationResponse,
    )

    assert len(result.evaluations) == 5
    assert "category=pydantic_validation_failure" in caplog.text
    assert "candidate-private-answer" not in caplog.text


@pytest.mark.anyio
async def test_invalid_json_retries_once_then_returns_validation_model(monkeypatch, caplog) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    responses = iter(["not json", '{"name":"Candidate","skills":["Python"]}'])
    calls = 0

    async def fake_request(*args) -> str:
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr(service, "_request_text", fake_request)
    profile = await service.generate_structured(
        "test-interview-456",
        "resume_analysis",
        "ignored prompt",
        CandidateProfile,
    )

    assert profile.name == "Candidate"
    assert calls == 2
    assert "category=structured_json_failure" in caplog.text
