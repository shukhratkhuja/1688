from paddleocr import PaddleOCR
from PIL import Image

from pytsrct_ocr import is_text_present


def extract_text(image_path):

    if not is_text_present(image_path=image_path):
        return None
    
    # 1. creating OCR 
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 'ch' for Chinese

    # 3. starting OCR 
    results = ocr.ocr(image_path, cls=True)

    # Gathered blocks: (text, y_center, x_start)
    blocks = []
    for line in results:
        for word_info in line:
            box = word_info[0]
            text = word_info[1][0]
            y_center = sum([point[1] for point in box]) / 4
            x_start = min([point[0] for point in box])
            blocks.append((text, y_center, x_start))

    # First sort by y (column), then by x for each row
    blocks.sort(key=lambda b: (round(b[1] / 10), b[2]))  # get closer till 10 pxs
    
    text_list = []
    # Detected text blocks in order
    for text, _, _ in blocks:
        text_list.append(text)

    return text_list


"""
# So'zlarni (text, y_middle) formatida yig'amiz
words = []
for line in result:
    for word_info in line:
        box = word_info[0]
        text = word_info[1][0]
        # Bounding boxdagi y koordinatalarni o'rtachasi
        y_coords = [point[1] for point in box]
        y_center = sum(y_coords) / len(y_coords)
        words.append((text, y_center))

# Qatorlarni aniqlaymiz: y_center bo‘yicha sort qilamiz
words.sort(key=lambda x: x[1])

# Qatordagi so‘zlar orasidagi maksimal y_farq
line_threshold = 10  # kerak bo‘lsa sozlash mumkin

lines = []
current_line = []
prev_y = None

for text, y in words:
    if prev_y is None or abs(y - prev_y) < line_threshold:
        current_line.append(text)
    else:
        lines.append(' '.join(current_line))
        current_line = [text]
    prev_y = y

# Oxirgi qatorni ham qo‘shamiz
if current_line:
    lines.append(' '.join(current_line))

# Chop etamiz
for idx, line in enumerate(lines):
    print(f"Line {idx + 1}: {line}")
"""