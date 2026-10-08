from pydantic import BaseModel, Field

from ..domain_config import DomainName
from .resume import ResumeMetadata


class InterviewCreationRequest(BaseModel):
    interview_id: str = Field(min_length=8, max_length=80)
    domain: DomainName
    resume_text: str = Field(min_length=1, max_length=100000)


class InterviewAnswerRequest(BaseModel):
    question_id: int = Field(ge=1, le=10)
    text: str = Field(default="", max_length=12000)
    selected_answer: str | None = None


class InterviewStateResponse(BaseModel):
    interview_id: str
    domain: DomainName
    candidate_profile: "CandidateProfile"
    questions: list["PublicQuestion"] = Field(default_factory=list)
    answers: dict[int, InterviewAnswerRequest] = Field(default_factory=dict)
    completed: bool = False
    result: "InterviewResult | None" = None


from .profile import CandidateProfile
from .question import PublicQuestion
from .result import InterviewResult

InterviewStateResponse.model_rebuild()


class ProfileAnalysisResponse(BaseModel):
    interview_id: str
    candidate_profile: CandidateProfile


class QuestionGenerationResponse(BaseModel):
    interview_id: str
    questions: list[PublicQuestion]