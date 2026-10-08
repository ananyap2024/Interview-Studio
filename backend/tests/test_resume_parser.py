import pytest

from app.services.resume_parser import MAX_RESUME_SIZE_BYTES, ResumeParseError, normalize_resume_text, parse_resume


def test_parses_pdf(pdf_bytes: bytes) -> None:
    result = parse_resume("resume.pdf", "application/pdf", pdf_bytes)

    assert result.metadata.filename == "resume.pdf"
    assert "Candidate Name" in result.extracted_text
    assert "Python Developer" in result.extracted_text


def test_parses_docx(docx_bytes: bytes) -> None:
    result = parse_resume(
        "resume.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        docx_bytes,
    )

    assert "Candidate Name" in result.extracted_text
    assert "Python Developer" in result.extracted_text


def test_rejects_unsupported_file_type() -> None:
    with pytest.raises(ResumeParseError) as error:
        parse_resume("resume.txt", "text/plain", b"some text")

    assert error.value.code == "unsupported_file_type"
    assert error.value.status_code == 415


def test_rejects_empty_or_unreadable_document(empty_pdf_bytes: bytes) -> None:
    with pytest.raises(ResumeParseError) as empty_error:
        parse_resume("resume.pdf", "application/pdf", empty_pdf_bytes)
    with pytest.raises(ResumeParseError) as invalid_error:
        parse_resume("resume.pdf", "application/pdf", b"%PDF-invalid")

    assert empty_error.value.code == "empty_document"
    assert invalid_error.value.code == "unreadable_document"


def test_rejects_oversized_file() -> None:
    with pytest.raises(ResumeParseError) as error:
        parse_resume("resume.pdf", "application/pdf", b"x" * (MAX_RESUME_SIZE_BYTES + 1))

    assert error.value.code == "file_too_large"
    assert error.value.status_code == 413


def test_normalizes_whitespace_without_collapsing_sections() -> None:
    text = normalize_resume_text("  Skills\t  Python  \r\n\r\n\r\n Experience \n\n")

    assert text == "Skills Python\n\nExperience"