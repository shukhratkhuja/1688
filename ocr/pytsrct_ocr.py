from PIL import Image
import pytesseract


def is_text_present(image_path, min_chars=10):

    # For windows machine tesseract.exe path
    # pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Administrator\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

    text = pytesseract.image_to_string(Image.open(image_path))
    return len(text.strip()) >= min_chars


