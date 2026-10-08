from typing import Literal

from pydantic import BaseModel, Field


class ResumeMetadata(BaseModel):
    filename: str = Field(min_length=1)
    content_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    size_bytes: int = Field(gt=0)


class ResumeUploadResponse(BaseModel):
    metadata: ResumeMetadata
    extracted_text: str = Field(min_length=1)