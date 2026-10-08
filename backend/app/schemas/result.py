from pydantic import BaseModel, Field

from .evaluation import Evaluation


class InterviewResult(BaseModel):
    interview_id: str
    overall_score: float = Field(ge=1, le=10)
    mcq_correct: int = Field(ge=0, le=5)
    mcq_incorrect: int = Field(ge=0, le=5)
    mcq_score: float = Field(ge=0, le=10)
    theoretical_score: float = Field(ge=0, le=10)
    evaluations: list[Evaluation] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
    overall_assessment: str
    category_scores: dict[str, float]