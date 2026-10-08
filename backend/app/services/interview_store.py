import asyncio

from pydantic import BaseModel, Field

from ..domain_config import DomainName
from ..schemas.answer import Answer
from ..schemas.evaluation import EvaluationResponse
from ..schemas.profile import CandidateProfile
from ..schemas.question import InterviewQuestion
from ..schemas.result import InterviewResult


class InterviewRecord(BaseModel):
    interview_id: str
    domain: DomainName
    candidate_profile: CandidateProfile
    questions: list[InterviewQuestion] = Field(default_factory=list)
    answers: dict[int, Answer] = Field(default_factory=dict)
    evaluation: EvaluationResponse | None = None
    result: InterviewResult | None = None


class InterviewStore:
    def __init__(self) -> None:
        self._records: dict[str, InterviewRecord] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def lock_for(self, interview_id: str) -> asyncio.Lock:
        async with self._lock:
            return self._locks.setdefault(interview_id, asyncio.Lock())

    def get(self, interview_id: str) -> InterviewRecord | None:
        return self._records.get(interview_id)

    def put(self, record: InterviewRecord) -> None:
        self._records[record.interview_id] = record


interview_store = InterviewStore()