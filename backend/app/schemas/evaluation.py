from pydantic import BaseModel, ConfigDict, Field, model_validator


class Evaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int = Field(ge=6, le=10)
    score: float = Field(ge=0, le=10)
    correctness: float = Field(ge=0, le=10)
    relevance: float = Field(ge=0, le=10)
    completeness: float = Field(ge=0, le=10)
    clarity: float = Field(ge=0, le=10)
    depth: float = Field(ge=0, le=10)
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluations: list[Evaluation]
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
    overall_assessment: str
    evaluations: list[Evaluation]

    @model_validator(mode="after")
    def validate_evaluations(self) -> "EvaluationResponse":
        question_ids = {evaluation.question_id for evaluation in self.evaluations}
        if len(self.evaluations) != 5 or question_ids != set(range(6, 11)):
            raise ValueError("Exactly the five theoretical questions must be evaluated.")
        return self