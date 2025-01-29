from pathlib import Path
import logging
from PyPDF2 import PdfReader
import docx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DocumentParser:
    """Handle different document types for text extraction"""
    
    @staticmethod
    def read_pdf(file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise

    @staticmethod
    def read_docx(file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            raise

    @staticmethod
    def read_txt(file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {e}")
            raise

    @staticmethod
    def read_html(file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                return soup.get_text()
        except Exception as e:
            logger.error(f"Error reading HTML {file_path}: {e}")
            raise