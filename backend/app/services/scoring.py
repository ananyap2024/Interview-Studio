from ..schemas.evaluation import EvaluationResponse
from ..schemas.result import InterviewResult
from .interview_store import InterviewRecord


def build_interview_result(record: InterviewRecord, evaluation: EvaluationResponse) -> InterviewResult:
    mcq_questions = [question for question in record.questions if question.type == "mcq"]
    mcq_correct = sum(
        record.answers[question.id].selected_answer == question.correct_answer
        for question in mcq_questions
    )
    mcq_incorrect = len(mcq_questions) - mcq_correct
    mcq_score = mcq_correct / max(1, len(mcq_questions)) * 10
    theoretical_score = sum(item.score for item in evaluation.evaluations) / max(1, len(evaluation.evaluations))
    overall_score = mcq_score * 0.4 + theoretical_score * 0.6
    category_scores = {
        "technical_knowledge": round(sum(item.correctness for item in evaluation.evaluations) / 5, 1),
        "domain_knowledge": round(sum(item.relevance for item in evaluation.evaluations) / 5, 1),
        "answer_quality": round(
            sum((item.clarity + item.completeness) / 2 for item in evaluation.evaluations) / 5,
            1,
        ),
        "problem_solving": round(sum(item.depth for item in evaluation.evaluations) / 5, 1),
    }
    return InterviewResult(
        interview_id=record.interview_id,
        overall_score=max(1.0, round(overall_score, 1)),
        mcq_correct=mcq_correct,
        mcq_incorrect=mcq_incorrect,
        mcq_score=round(mcq_score, 1),
        theoretical_score=round(theoretical_score, 1),
        evaluations=evaluation.evaluations,
        strengths=evaluation.strengths,
        weaknesses=evaluation.weaknesses,
        recommended_topics=evaluation.recommended_topics,
        overall_assessment=evaluation.overall_assessment,
        category_scores=category_scores,
    )