from pydantic import BaseModel, Field


class Answer(BaseModel):
    question_id: int = Field(ge=1, le=10)
    text: str = Field(default="", max_length=12000)
    selected_answer: str | None = None