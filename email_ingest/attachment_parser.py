import io
import pdfplumber
from PIL import Image
import pytesseract

def parse_pdf(data: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def parse_image(data: bytes) -> str:
    image = Image.open(io.BytesIO(data))
    text = pytesseract.image_to_string(image)
    return text

def parse_attachments(attachments):
    results = []
    for att in attachments:
        filename = att['filename']
        data = att['data']
        if filename.lower().endswith('.pdf'):
            text = parse_pdf(data)
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            text = parse_image(data)
        else:
            text = None
        results.append({'filename': filename, 'text': text})
    return results 