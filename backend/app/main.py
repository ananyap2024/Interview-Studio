import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.routes.domains import router as domains_router
from .api.routes.interviews import router as interviews_router
from .api.routes.resume import router as resume_router
from .config import settings
from .schemas.errors import ErrorResponse
from .services.resume_parser import ResumeParseError
from .services.gemini_service import GeminiServiceError


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(domains_router)
app.include_router(interviews_router)
app.include_router(resume_router)


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        message = "The requested resource was not found."
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = "The request could not be processed."
    body = ErrorResponse(code="http_error", message=message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(ResumeParseError)
async def handle_resume_parse_error(request: Request, exc: ResumeParseError) -> JSONResponse:
    body = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(GeminiServiceError)
async def handle_gemini_error(request: Request, exc: GeminiServiceError) -> JSONResponse:
    body = ErrorResponse(code="ai_service_error", message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = ErrorResponse(code="validation_error", message="Request validation failed.")
    return JSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).error("Unhandled request failure.")
    body = ErrorResponse(code="internal_error", message="An internal server error occurred.")
    return JSONResponse(status_code=500, content=body.model_dump())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}