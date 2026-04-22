# utils.py
import PyPDF2
import docx
from PIL import Image
import pytesseract
import io

def extract_text_from_file(uploaded_file):
    """Extracts text from various file formats to feed to the LLM."""
    file_type = uploaded_file.name.split('.')[-1].lower()
    text = ""

    try:
        if file_type == 'pdf':
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        elif file_type in ['doc', 'docx']:
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        elif file_type == 'txt':
            text = uploaded_file.getvalue().decode("utf-8")
            
        elif file_type in ['png', 'jpg', 'jpeg']:
            # Uses OCR to read text from images
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
            text = f"[Extracted Text from Image:]\n{text}"
            
        else:
            text = f"Unsupported file type: {file_type}"
            
    except Exception as e:
        text = f"Error reading file: {str(e)}"
        
    return text