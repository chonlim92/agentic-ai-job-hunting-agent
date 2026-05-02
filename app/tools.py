from dotenv import load_dotenv
import os
import docx
import pdfplumber
import subprocess
from openai import OpenAI
from langchain_core.tools import tool


load_dotenv()


@tool
def extract_cv_text(file_path: str) -> str:
    """
    Extract text content from a CV/resume file.

    Supports .docx, .pdf, and .doc formats. For .doc files,
    LibreOffice (soffice) is used to convert to .docx first.

    Args:
        file_path: Path to the CV/resume file (.docx, .pdf, or .doc).

    Returns:
        str: Extracted text content from the file, or an error message if reading fails.
    """
    ext = os.path.splitext(file_path)[-1].lower()

    if '.docx' in ext:
        try:
            doc = docx.Document(file_path)
            text = [para.text for para in doc.paragraphs]
            return '\n'.join(text)
        except Exception as e:
            return f"Error reading .docx file: {e}"

    elif '.pdf' in ext:
        try:
            text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return '\n'.join(text)
        except Exception as e:
            return f"Error reading .pdf file: {e}"

    elif '.doc' in ext:
        try:
            temp_docx = file_path + '.temp.docx'
            subprocess.run(
                ['soffice', '--headless', '--convert-to', 'docx',
                 '--outdir', os.path.dirname(file_path), file_path],
                check=True
            )
            doc = docx.Document(temp_docx)
            text = [para.text for para in doc.paragraphs]
            return '\n'.join(text)
        except Exception as e:
            return f"Error reading .doc file: {e}"

    else:
        return "Unsupported file format. Please upload a .doc, .docx, or .pdf file."


@tool
def job_posting_scraper(job_link: str) -> str:
    """
    Scrape job posting details from a given URL.

    Args:
        job_link: URL of the job posting to scrape.

    Returns:
        str: A structured summary of the job posting details, or an error message if scraping fails.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={"search_context_size": "medium"},
        messages=[
            {
                "role": "system",
                "content": """
You are a helpful tool that visits the following job posting and carefully reads its content.
Visit the provided link and summarize the key details in a clear and concise format, including:
- Job Title
- Company Name
- Location
- Job Description
- Employment Type (e.g., Full-time, Part-time, Contract)
- Required Qualifications
- Preferred Qualifications
- Application Instructions
- Salary Range (if listed)
- Primary Responsibilities
- Benefits (if listed)
- Posting Date (if available)
- Any other relevant information that would help a job seeker understand the role and how to apply

Format:
- Respond with a clear and structured bullet point list
- Use exact factual information from the posting, no rewording beyond make it concise.
- If the posting is missing, inaccessible or contains no job details, respond with "Job posting unavailable or contains no job details."

Do's:
- Do visit the provided link and read the job posting carefully.
- Ensure all extracted details are accurate and directly taken from the posting.
- Keep descriptions concise while retaining all critical information, short, professional and easy to scan.
- Use consistent formatting for all fields (e.g. "Job Title: ...")

Dont's:
- Do not include any information that is not explicitly stated in the job posting.
- Do not make assumptions or add interpretations beyond what is provided in the posting.
- Do not include filler language, speculation or personal opinions.
- Do not rewrite or interpret details-only report factual information from the posting.
"""
            },
            {
                "role": "user",
                "content": f"Visit this job posting link and extract details:\n{job_link}"
            }
        ]
    )

    return completion.choices[0].message.content
