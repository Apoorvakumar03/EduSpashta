from PyPDF2 import PdfReader
import io

def process_pdf(pdf_file):
    """Extracts text from the given PDF file."""
    reader = PdfReader(io.BytesIO(pdf_file.read()))
    text = [page.extract_text() for page in reader.pages if page.extract_text()]
    return " ".join(text)  # Join all text from pages into a single string
