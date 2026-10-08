from fastapi import APIRouter, File, UploadFile

from ...schemas.resume import ResumeUploadResponse
from ...services.resume_parser import MAX_RESUME_SIZE_BYTES, ResumeParseError, parse_resume


router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    try:
        if file.size is not None and file.size > MAX_RESUME_SIZE_BYTES:
            raise ResumeParseError("file_too_large", "The resume exceeds the 5 MB size limit.", 413)
        content = await file.read(MAX_RESUME_SIZE_BYTES + 1)
        return parse_resume(file.filename or "", file.content_type, content)
    finally:
        await file.close()