from fastapi.testclient import TestClient
from uuid import uuid4

from app.domain_config import DOMAIN_NAMES
from app.main import app
from app.schemas.evaluation import Evaluation, EvaluationResponse
from app.schemas.profile import CandidateProfile
from app.schemas.question import InterviewQuestion, QuestionSet
from app.services.gemini_service import gemini_service


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_domains_returns_configured_names() -> None:
    response = client.get("/api/domains")

    assert response.status_code == 200
    assert [domain["name"] for domain in response.json()] == list(DOMAIN_NAMES)


def test_domains_allows_frontend_origin() -> None:
    response = client.get("/api/domains", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_not_found_uses_safe_error_shape() -> None:
    response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "code": "http_error",
        "message": "The requested resource was not found.",
    }


def test_resume_upload_returns_extracted_pdf_text(pdf_bytes: bytes) -> None:
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["content_type"] == "application/pdf"
    assert "Candidate Name" in response.json()["extracted_text"]


def test_resume_upload_returns_extracted_docx_text(docx_bytes: bytes) -> None:
    response = client.post(
        "/api/resume/upload",
        files={
            "file": (
                "resume.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert "Python Developer" in response.json()["extracted_text"]


def test_resume_upload_rejects_unsupported_file() -> None:
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", b"resume text", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_file_type"


def test_resume_upload_rejects_oversized_file() -> None:
    from app.services.resume_parser import MAX_RESUME_SIZE_BYTES

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", b"x" * (MAX_RESUME_SIZE_BYTES + 1), "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_full_interview_uses_three_mocked_calls_and_scores_mcqs_locally(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    async def fake_generate(interview_id, stage, prompt, response_model):
        calls.append((stage, prompt))
        if stage == "resume_analysis":
            return CandidateProfile(name="Candidate", skills=["Python"], seniority="student")
        if stage == "answer_evaluation":
            return EvaluationResponse(
                evaluations=[
                    Evaluation(
                        question_id=question_id,
                        score=8,
                        correctness=8,
                        relevance=7,
                        completeness=8,
                        clarity=8,
                        depth=9,
                        feedback=f"Feedback for {question_id}",
                    )
                    for question_id in range(6, 11)
                ],
                strengths=["Clear explanations"],
                weaknesses=["Could add examples"],
                recommended_topics=["Testing"],
                overall_assessment="A strong technical foundation.",
            )
        questions = []
        difficulties = ["easy", "easy", "medium", "medium", "medium", "medium", "medium", "hard", "hard", "hard"]
        for question_id, difficulty in enumerate(difficulties, start=1):
            if question_id <= 5:
                questions.append(InterviewQuestion(
                    id=question_id,
                    type="mcq",
                    question=f"MCQ {question_id}",
                    topic="Python",
                    difficulty=difficulty,
                    options=["a", "b", "c", "d"],
                    correct_answer="a",
                ))
            else:
                questions.append(InterviewQuestion(
                    id=question_id,
                    type="theoretical",
                    question=f"Theory {question_id}",
                    topic="Python",
                    difficulty=difficulty,
                ))
        return QuestionSet(questions=list(reversed(questions)))

    monkeypatch.setattr(gemini_service, "generate_structured", fake_generate)
    interview_id = str(uuid4())
    create_response = client.post("/api/interviews", json={
        "interview_id": interview_id,
        "domain": "Python Full Stack",
        "resume_text": "Python Engineer; confidential resume detail",
    })
    assert create_response.status_code == 200
    assert calls[0][0] == "resume_analysis"
    assert "confidential resume detail" in calls[0][1]

    first_questions = client.post(f"/api/interviews/{interview_id}/questions")
    second_questions = client.post(f"/api/interviews/{interview_id}/questions")

    assert first_questions.status_code == 200
    assert first_questions.json() == second_questions.json()
    public_questions = first_questions.json()["questions"]
    assert len(public_questions) == 10
    assert [question["id"] for question in public_questions] == list(range(1, 11))
    assert sum(question["type"] == "mcq" for question in public_questions) == 5
    assert sum(question["type"] == "theoretical" for question in public_questions) == 5
    assert all("correct_answer" not in question for question in public_questions)
    assert calls[1][0] == "question_generation"
    assert "confidential resume detail" not in calls[1][1]
    for question_id in range(1, 11):
        question = public_questions[question_id - 1]
        answer = {
            "question_id": question_id,
            "text": f"Candidate answer {question_id}" if question_id > 5 else "",
        }
        if question_id <= 5:
            answer["selected_answer"] = "a" if question_id <= 3 else "d"
        saved = client.put(f"/api/interviews/{interview_id}/answers/{question_id}", json=answer)
        assert saved.status_code == 200

    result = client.post(f"/api/interviews/{interview_id}/complete")
    repeated_result = client.post(f"/api/interviews/{interview_id}/complete")

    assert result.status_code == 200
    assert result.json() == repeated_result.json()
    assert result.json()["mcq_correct"] == 3
    assert result.json()["mcq_incorrect"] == 2
    assert result.json()["mcq_score"] == 6
    assert result.json()["theoretical_score"] == 8
    assert result.json()["overall_score"] == 7.2
    assert set(result.json()["category_scores"]) == {
        "technical_knowledge", "domain_knowledge", "answer_quality", "problem_solving"
    }
    assert [stage for stage, _ in calls] == ["resume_analysis", "question_generation", "answer_evaluation"]
    assert "confidential resume detail" not in calls[2][1]
    assert "correct_answer" not in calls[2][1]
    state = client.get(f"/api/interviews/{interview_id}")
    assert state.status_code == 200
    assert state.json()["completed"] is True
    assert all("correct_answer" not in question for question in state.json()["questions"])