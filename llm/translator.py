import openai
import json, ast



from utils.constants import (OPENAI_API_KEY,
                             DB_NAME,
                             TABLE_PRODUCT_DATA,
                             TABLE_PRODUCT_IMAGES,
                             TRANSLATION_MODEL
                             )
from utils.db_utils import fetch_many, update_row
from utils.log_config import get_logger

logger = get_logger("tranlation", "app.log")

def merge_duplicate_values(data):
    merged_data = {}
    for key, value in data.items():
        if key in merged_data:
            # Agar kalit avval ham mavjud bo‘lsa, yangi qiymatni qo‘shamiz
            existing = merged_data[key]
            if isinstance(existing, str):
                # Agar qiymatlar bir xil bo‘lmasa, birlashtiramiz
                if value not in existing:
                    merged_data[key] = existing + ", " + value
            else:
                # Boshqa tur bo‘lsa, to‘g‘ridan-to‘g‘ri yangilash
                merged_data[key] = value
        else:
            # Yangi kalitni qo‘shamiz
            merged_data[key] = value
    return merged_data

def clear_tanslated_product_json(translated_content):

    # # 2. Asosiy JSON'ni o‘girish
    translated_data = json.loads(translated_content)

    # 3. Ichki string JSON'ni tozalash
    if isinstance(translated_data.get("product_attributes_en"), str):
        translated_data["product_attributes_en"] = json.loads(translated_data["product_attributes_en"])
    # print(translated_data)

    # print("-"*100)
    transform_data = merge_duplicate_values(translated_data)

    return transform_data


def clear_translated_img_json(translated_content):

    safe_conent = translated_content.replace('\n', '\\n').replace('\t', '\\t')
    # 1. JSON stringdan dict yasash
    translated_data = json.loads(safe_conent)

    # 2. image_text_en ichidagi stringlarni tozalash
    raw_list = translated_data["image_text_en"]

    # 3. Har bir elementni qochirish
    clean_list = [text.strip('"') for text in raw_list]

    # 4. Yangilangan dict
    translated_data["image_text_en"] = clean_list

    # 5. Natija
    # print(json.dumps(translated_data, indent=2))
    return json.dumps(translated_data, indent=2)

def translate_entry(client, entry, system_prompt, entry_type="image_text"):
    
    # print(entry)
    USER_PROMPT = f"""
        Translate this JSON:
        {json.dumps(entry, ensure_ascii=False, indent=2)}
        """
    try:
        response = client.chat.completions.create(
            model=TRANSLATION_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT}
            ]
        )
        translated_content = response.choices[0].message.content
        print(translated_content)
        if entry_type == "product_data":
            cleared_content = clear_tanslated_product_json(translated_content=translated_content)
        else:
            cleared_content = clear_translated_img_json(translated_content=translated_content)
        
        return cleared_content
    except Exception as error:
        logger.log_exception(error, context="openai request")
        return None

def translate_product_data(product_data_to_translate):

    
    SYSTEM_PROMPT = (
            "You are a professional e-commerce translator. "
            "Translate all Chinese keys and values in JSON to English. "
            "Preserve JSON structure exactly."
            "- Always escape special characters like newline (\n), tab (\t) in the JSON output."
            "If keys have '_chn', change to '_en'."
            )


    for row_data in product_data_to_translate:

        json_data = {
            "title_chn": row_data[1],
            "product_attributes_chn": row_data[2],
            "text_details_chn": row_data[3]
        } 
        # print(json_data)
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        translated_data = translate_entry(client=client, system_prompt=SYSTEM_PROMPT, entry=json_data, entry_type="product_data")
        # print(translated_data)
        # print("="*100)

        # print(translated_data["title_en"])
        # print(json.dumps(translated_data["product_attributes_en"]))
        # print(json.dumps(translated_data["text_details_en"]))

        title_en = translated_data["title_en"].replace("'", "''")
        product_attributes_en = json.dumps(translated_data["product_attributes_en"])
        text_details_en = json.dumps(translated_data["text_details_en"])
        
        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            column_with_value=[
                ("title_en", title_en),
                ("product_attributes_en", product_attributes_en),
                ("text_details_en", text_details_en),
            ],
            where=[
                ("product_url","=",row_data[0])
            ]
        )

    print("✅ All product data translated and saved to db")



def translate_product_img_texts(img_texts_to_translate):

    SYSTEM_PROMPT = (
            "You are a professional e-commerce translator. "
            "Translate all Chinese keys and values in JSON to English. "
            "Preserve JSON structure exactly. "
            "If keys have '_chn', change to '_en'."
            )
    
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    print(img_texts_to_translate)
    for row_data in img_texts_to_translate:

        json_data = {
            "image_text_chn": row_data[1],
        } 
        print(json_data)
        print("="*100)

        translated_data = translate_entry(system_prompt=SYSTEM_PROMPT, entry=json_data, client=client)
        print(translated_data)

        # update_row(
        #     db=DB_NAME,
        #     table=TABLE_PRODUCT_IMAGES,
        #     column_with_value=[
        #         ("image_text_en",)
        #     ],
        #     where=[
        #         ("image_url","=",row_data[0])
        #     ]
        # )

        print(translated_data)

    print("✅ All image texts translated and saved to db")
