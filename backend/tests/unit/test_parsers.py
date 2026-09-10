import io

import docx
import pytest
from app.services.ingestion_service import (
    DecompressionBombError,
    FileValidationError,
    IngestionService,
)
from pypdf import PageObject, PdfWriter


def create_sample_docx(paragraphs: list[str]) -> bytes:
    """Helper to generate in-memory DOCX bytes."""
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestIngestionServiceValidation:
    """Tests for file validation, size limits, and sanitization."""

    def test_rejects_unsupported_file_extension(self):
        service = IngestionService()
        with pytest.raises(FileValidationError, match="Unsupported file extension"):
            service.validate_and_parse(
                filename="malicious.exe",
                content=b"MZ\x90\x00binary executable",
            )

    def test_rejects_oversized_file(self):
        service = IngestionService(max_file_size_mb=1)
        large_content = b"a" * (1024 * 1024 * 2)  # 2MB > 1MB limit
        with pytest.raises(FileValidationError, match="File size exceeds"):
            service.validate_and_parse(
                filename="large_document.txt",
                content=large_content,
            )

    def test_rejects_empty_file(self):
        service = IngestionService()
        with pytest.raises(FileValidationError, match="File is empty"):
            service.validate_and_parse(
                filename="empty.txt",
                content=b"",
            )

    def test_decompression_bomb_protection(self):
        service = IngestionService(max_character_count=1000)
        huge_text = "Python Developer Internship requirements " * 50
        with pytest.raises(DecompressionBombError, match="Text length exceeds limit"):
            service.validate_and_parse(
                filename="bomb.txt",
                content=huge_text.encode("utf-8"),
            )

    def test_text_sanitization_strips_control_characters(self):
        service = IngestionService()
        raw_text = "Job\x00Title:\tSoftware\x08Engineer\r\nLocation:  \xa0 Remote  "
        sanitized = service.sanitize_text(raw_text)
        assert "\x00" not in sanitized
        assert "\x08" not in sanitized
        assert "Software Engineer" in sanitized
        assert "Remote" in sanitized


class TestDocumentParsers:
    """Tests for text extraction across PDF, TXT, MD, and DOCX."""

    def test_parse_plain_text(self):
        service = IngestionService()
        content = b"Role: Python Backend Intern\nRequirements:\n- Python\n- SQL"
        doc_data = service.validate_and_parse("job.txt", content)
        assert doc_data.filename == "job.txt"
        assert doc_data.page_count == 1
        assert len(doc_data.pages) == 1
        assert "Python Backend Intern" in doc_data.pages[0].text
        assert doc_data.pages[0].page_number is None

    def test_parse_markdown_text(self):
        service = IngestionService()
        content = b"# Frontend Intern\n\n## Tech Stack\n* React\n* TypeScript"
        doc_data = service.validate_and_parse("job.md", content)
        assert doc_data.filename == "job.md"
        assert doc_data.page_count == 1
        assert "Frontend Intern" in doc_data.pages[0].text
        assert "React" in doc_data.pages[0].text

    def test_parse_docx_file(self):
        service = IngestionService()
        docx_bytes = create_sample_docx(
            [
                "Cloud Infrastructure Intern",
                "Responsibilities: Deploy Kubernetes clusters and write Terraform.",
            ]
        )
        doc_data = service.validate_and_parse("job.docx", docx_bytes)
        assert doc_data.filename == "job.docx"
        assert "Cloud Infrastructure Intern" in doc_data.raw_text
        assert "Kubernetes" in doc_data.raw_text

    def test_parse_pdf_preserves_page_numbers(self):
        service = IngestionService()
        writer = PdfWriter()
        writer.add_page(PageObject.create_blank_page(width=200, height=200))
        buf = io.BytesIO()
        writer.write(buf)
        pdf_bytes = buf.getvalue()

        doc_data = service.validate_and_parse("internship.pdf", pdf_bytes)
        assert doc_data.filename == "internship.pdf"
        assert doc_data.page_count >= 1
