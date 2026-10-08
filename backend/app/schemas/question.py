from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InterviewQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(ge=1, le=10)
    type: Literal["mcq", "theoretical"]
    question: str = Field(min_length=1)
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    options: list[str] = Field(default_factory=list)
    correct_answer: str = ""

    @model_validator(mode="after")
    def validate_answer_key(self) -> "InterviewQuestion":
        if self.type == "mcq":
            if len(self.options) != 4 or len(set(self.options)) != 4:
                raise ValueError("MCQs must have exactly four unique options.")
            if self.correct_answer not in self.options:
                raise ValueError("MCQs must have one correct answer from their options.")
        elif self.options or self.correct_answer:
            raise ValueError("Theoretical questions cannot include options or an answer key.")
        return self


class PublicQuestion(BaseModel):
    id: int
    type: Literal["mcq", "theoretical"]
    question: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    options: list[str] = Field(default_factory=list)


class QuestionSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[InterviewQuestion]

    @model_validator(mode="after")
    def validate_question_set(self) -> "QuestionSet":
        if len(self.questions) != 10:
            raise ValueError("Exactly ten questions are required.")
        if {question.id for question in self.questions} != set(range(1, 11)):
            raise ValueError("Question IDs must be the integers 1 through 10.")
        if sum(question.type == "mcq" for question in self.questions) != 5:
            raise ValueError("Exactly five MCQs are required.")
        if sum(question.type == "theoretical" for question in self.questions) != 5:
            raise ValueError("Exactly five theoretical questions are required.")
        difficulty_counts = {difficulty: sum(q.difficulty == difficulty for q in self.questions) for difficulty in ("easy", "medium", "hard")}
        if difficulty_counts != {"easy": 2, "medium": 5, "hard": 3}:
            raise ValueError("Difficulty distribution must be two easy, five medium, and three hard.")
        return self