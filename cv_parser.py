import pdfplumber
import logging
import io
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_pdf(file_content: bytes) -> str:
    text = ""
    try:
        with io.BytesIO(file_content) as pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        return text
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du PDF : {e}")
        return ""

def extract_text_from_file(uploaded_file) -> str:
    try:
        file_content = uploaded_file.read()
        if uploaded_file.name.lower().endswith('.pdf'):
            raw_text = read_pdf(file_content)
            raw_text = re.sub(r'\(cid:\d+\)', '', raw_text)
            logging.info(f"Texte extrait du PDF : {raw_text[:500]}...")
            return raw_text
        else:
            logging.error("Format de fichier non supporté. Seuls les PDF sont acceptés.")
            return ""
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction du texte : {e}")
        return ""