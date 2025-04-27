from paddleocr import PaddleOCR
import json, os
import sys, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ocr.pytsrct_ocr import is_text_present
from utils.db_utils import update_row
from utils.constants import DB_NAME, TABLE_PRODUCT_IMAGES, LOCAL_IMAGES_FOLDER, LOCAL_OUTPUT_FOLDER


def extract_text(image_path):

    if not is_text_present(image_path=image_path):
        return None
    
    # 1. creating OCR 
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_space_char=True)  # 'ch' for Chinese

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


def extract_line_by_line(image_path):

    if not is_text_present(image_path=image_path):
        return None

    # 1. creating OCR 
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 'ch' for Chinese

    # 3. starting OCR 
    results = ocr.ocr(image_path, cls=True)
    print(results)
    # So'zlarni (text, y_middle) formatida yig'amiz
    words = []
    for line in results:
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
            try:
                lines.append(' '.join(current_line))
                current_line = [text]
            except:
                time.sleep(100)
        prev_y = y

    # Oxirgi qatorni ham qo‘shamiz
    if current_line:
        try:
            lines.append(' '.join(current_line))
        except:
            time.sleep(199)
    # Chop etamiz
    for idx, line in enumerate(lines):
        print(f"Line {idx + 1}: {line}")
    
    return lines


def main(img_details):

    for image_url, image_filename in img_details:
        # print(LOCAL_IMAGES_FOLDER)
        # print(image_filename)
        image_path = os.path.join(LOCAL_OUTPUT_FOLDER, LOCAL_IMAGES_FOLDER, image_filename)
        text_list = extract_line_by_line(image_path=image_path)

        if text_list:
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[
                    ("image_text", json.dumps(text_list, ensure_ascii=False) if text_list else None),
                    ("text_extracted_status", "1")
                    ],
                where=[
                    ("image_url","=",image_url)
                    ]
            )
        else:
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[
                    ("text_extracted_status", "1")
                    ],
                where=[
                    ("image_url","=",image_url)
                    ]
            )

        time.sleep(0.5)
