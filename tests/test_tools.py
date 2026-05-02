import os
import pytest
from unittest.mock import patch, MagicMock

from app.tools import extract_cv_text, job_posting_scraper


class TestExtractCvText:
    """Tests for the extract_cv_text tool."""

    def test_pdf_extraction(self, tmp_path):
        """Test PDF text extraction with a mock PDF."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample CV content from PDF"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("app.tools.pdfplumber.open", return_value=mock_pdf):
            result = extract_cv_text.invoke("test.pdf")
            assert "Sample CV content from PDF" in result

    def test_docx_extraction(self, tmp_path):
        """Test DOCX text extraction with a mock document."""
        mock_para1 = MagicMock()
        mock_para1.text = "Education: BS Computer Science"
        mock_para2 = MagicMock()
        mock_para2.text = "Experience: 5 years"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]

        with patch("app.tools.docx.Document", return_value=mock_doc):
            result = extract_cv_text.invoke("test.docx")
            assert "Education: BS Computer Science" in result
            assert "Experience: 5 years" in result

    def test_unsupported_format(self):
        """Test that unsupported formats return an error message."""
        result = extract_cv_text.invoke("test.txt")
        assert "Unsupported file format" in result

    def test_pdf_file_not_found(self):
        """Test that a missing PDF returns an error message."""
        result = extract_cv_text.invoke("nonexistent.pdf")
        assert "Error reading .pdf file" in result

    def test_docx_file_not_found(self):
        """Test that a missing DOCX returns an error message."""
        result = extract_cv_text.invoke("nonexistent.docx")
        assert "Error reading .doc" in result

    def test_pdf_multi_page(self, tmp_path):
        """Test PDF extraction with multiple pages."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("app.tools.pdfplumber.open", return_value=mock_pdf):
            result = extract_cv_text.invoke("test.pdf")
            assert "Page 1 content" in result
            assert "Page 2 content" in result

    def test_pdf_empty_page(self):
        """Test PDF extraction skips pages with no text."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("app.tools.pdfplumber.open", return_value=mock_pdf):
            result = extract_cv_text.invoke("test.pdf")
            assert "Content" in result


class TestJobPostingScraper:
    """Tests for the job_posting_scraper tool."""

    @patch("app.tools.OpenAI")
    def test_successful_scrape(self, mock_openai_cls):
        """Test successful job posting scraping."""
        mock_message = MagicMock()
        mock_message.content = "Job Title: Software Engineer\nCompany: TestCorp"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        result = job_posting_scraper.invoke("https://example.com/job/123")
        assert "Software Engineer" in result
        assert "TestCorp" in result

    @patch("app.tools.OpenAI")
    def test_api_called_with_correct_model(self, mock_openai_cls):
        """Test that the scraper uses gpt-4o-search-preview."""
        mock_message = MagicMock()
        mock_message.content = "Job details"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        job_posting_scraper.invoke("https://example.com/job/123")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o-search-preview"
