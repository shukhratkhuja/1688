from paddleocr import PaddleOCR
from PIL import Image

# 1. OCR modelini yaratamiz
# ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 'ch' for Chinese

# 2. Test qilish uchun rasm yo'lini belgilang

# 3. OCRni ishga tushiramiz
# results = ocr.ocr(image_path, cls=True)

# 4. Natijani chiqaramiz
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')
result = ocr.ocr(image_path, cls=True)

# Yig'ilgan bloklar: (text, y_center, x_start)
blocks = []
for line in result:
    for word_info in line:
        box = word_info[0]
        text = word_info[1][0]
        y_center = sum([point[1] for point in box]) / 4
        x_start = min([point[0] for point in box])
        blocks.append((text, y_center, x_start))

# Avval y (qator) bo‘yicha sort, keyin har qator ichida x bo‘yicha
blocks.sort(key=lambda b: (round(b[1] / 10), b[2]))  # y ni 10 pikselgacha yaqinlashtiramiz

# Chop etamiz
print("Detected text blocks in order:")
for text, _, _ in blocks:
    print(text)










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