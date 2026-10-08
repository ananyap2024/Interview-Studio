import pytest

from app.schemas.profile import CandidateProfile
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services import gemini_service as service_module


@pytest.mark.anyio
async def test_invalid_json_retries_once_then_exhausts_budget(monkeypatch) -> None:
    monkeypatch.setattr(service_module.settings, "gemini_api_key", "test-only-key")
    service = GeminiService()
    responses = iter(["not json", '{"name":"Candidate","skills":["Python"]}'])
    calls = 0

    async def fake_request(stage: str, prompt: str, schema: dict[str, object]) -> str:
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr(service, "_request_text", fake_request)
    profile = await service.generate_structured(
        "test-interview-123",
        "resume_analysis",
        "ignored prompt",
        CandidateProfile,
    )

    assert profile.name == "Candidate"
    assert calls == 2
    with pytest.raises(GeminiServiceError):
        await service.generate_structured(
            "test-interview-123",
            "resume_analysis",
            "ignored prompt",
            CandidateProfile,
        )
    assert calls == 2