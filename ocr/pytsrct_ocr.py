from PIL import Image
import pytesseract


def is_text_present(image_path, min_chars=10):
    text = pytesseract.image_to_string(Image.open(image_path))
    return len(text.strip()) >= min_chars


