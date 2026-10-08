from pydantic import BaseModel, ConfigDict, Field


class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    seniority: str = ""
    summary: str = ""