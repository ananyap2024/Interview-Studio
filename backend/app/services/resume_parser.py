import re
import zipfile
from io import BytesIO
from pathlib import Path

import pymupdf as fitz
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..schemas.resume import ResumeMetadata, ResumeUploadResponse


MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024
MAX_DOCX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
GENERIC_MIME_TYPE = "application/octet-stream"


class ResumeParseError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def normalize_resume_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[^\S\n]+", " ", raw_line).strip()
        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")
    return "\n".join(lines).strip()


def _safe_filename(filename: str) -> str:
    return filename.replace("\\", "/").rsplit("/", 1)[-1].strip()


def _extract_pdf(content: bytes) -> str:
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            if document.is_encrypted:
                raise ResumeParseError("encrypted_document", "Password-protected PDFs are not supported.")
            return "\n\n".join(page.get_text("text") for page in document)
    except ResumeParseError:
        raise
    except (fitz.FileDataError, RuntimeError, ValueError) as exc:
        raise ResumeParseError("unreadable_document", "The PDF could not be read.") from exc


def _extract_docx(content: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ResumeParseError("invalid_document", "The DOCX file is invalid or unreadable.")
            if sum(item.file_size for item in archive.infolist()) > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise ResumeParseError("document_too_large", "The expanded DOCX content exceeds the size limit.", 413)
        document = Document(BytesIO(content))
    except ResumeParseError:
        raise
    except Exception as exc:
        raise ResumeParseError("unreadable_document", "The DOCX file could not be read.") from exc

    sections: list[str] = []
    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            sections.append(block.text)
        elif isinstance(block, Table):
            for row in block.rows:
                sections.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(sections)


def parse_resume(filename: str, content_type: str | None, content: bytes) -> ResumeUploadResponse:
    if len(content) > MAX_RESUME_SIZE_BYTES:
        raise ResumeParseError("file_too_large", "The resume exceeds the 5 MB size limit.", 413)
    if not content:
        raise ResumeParseError("empty_file", "The uploaded file is empty.")

    safe_filename = _safe_filename(filename)
    if not safe_filename:
        raise ResumeParseError("missing_filename", "A filename is required.")

    extension = Path(safe_filename).suffix.lower()
    expected_type = {".pdf": PDF_MIME_TYPE, ".docx": DOCX_MIME_TYPE}.get(extension)
    if expected_type is None:
        raise ResumeParseError("unsupported_file_type", "Upload a PDF or DOCX resume.", 415)

    supplied_type = (content_type or "").split(";", 1)[0].strip().lower()
    if supplied_type not in {"", GENERIC_MIME_TYPE, expected_type}:
        raise ResumeParseError("file_type_mismatch", "The file extension and content type do not match.")

    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ResumeParseError("invalid_document", "The file does not contain a valid PDF signature.")
        extracted_text = _extract_pdf(content)
    else:
        extracted_text = _extract_docx(content)

    extracted_text = normalize_resume_text(extracted_text)
    if not extracted_text:
        raise ResumeParseError("empty_document", "No readable text was found in the resume.", 422)

    return ResumeUploadResponse(
        metadata=ResumeMetadata(
            filename=safe_filename,
            content_type=expected_type,
            size_bytes=len(content),
        ),
        extracted_text=extracted_text,
    )