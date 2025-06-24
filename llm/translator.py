import openai
import json, ast
from collections import defaultdict



from utils.constants import (OPENAI_API_KEY,
                             DB_NAME,
                             TABLE_PRODUCT_DATA,
                             TABLE_PRODUCT_IMAGES,
                             TRANSLATION_MODEL
                             )
from utils.db_utils import fetch_many, update_row
from utils.log_config import get_logger
from utils.utils import json_loads, json_dumps

logger = get_logger("tranlation", "app.log")


def parse_json_with_duplicates(json_str):

    if type(json_str) == dict:
        return json_str
    
    json_str = json_str.replace("'", "''")
    pairs = json.loads(json_str, object_pairs_hook=lambda pairs: pairs)
    merged = defaultdict(list)
    
    for key, value in pairs:
        merged[key].append(value)
    
    result = {}
    for key, values in merged.items():
        if len(values) > 1:
            result[key] = ', '.join(values)
        else:
            result[key] = values[0]
    return result


def translate_entry(client, entry, system_prompt):
    
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
        translated_content = json_loads(translated_content)
        return translated_content
    
    except Exception as error:
        logger.log_exception(error, context="openai request")
        raise error

def translate_product_data(product_data_to_translate):

    
    SYSTEM_PROMPT = (
            "You are a professional e-commerce translator. "
            "Translate all Chinese keys and values in JSON to English. "
            "Preserve JSON structure exactly and serializable"
            "Return the list in the same order."
            )

    for product_url, title_chn, product_attributes_chn, text_details_chn in product_data_to_translate:

        # gathering content to list for translation
        entry = [title_chn, product_attributes_chn, text_details_chn]

        # creating openai client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        # taking translated content
        translated_data = translate_entry(client=client, system_prompt=SYSTEM_PROMPT, entry=entry)
        if translated_data:
            print(translated_data)


            print("TITLE CHN", title_chn)
            # polishing translated data
            title_en = translated_data[0]
            if title_en:
                title_en = title_en.replace("'", "''")
            
            product_attributes_en = translated_data[1]
            if product_attributes_en:
                product_attributes_en = parse_json_with_duplicates(product_attributes_en)
                product_attributes_en = json_dumps(product_attributes_en)

            text_details_en = translated_data[2]
            if text_details_en:
                if type(text_details_en) == str:
                    text_details_en = text_details_en.replace("'", "''")
                    
                text_details_en = json_dumps(text_details_en)

        # writing translations to db
        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            column_with_value=[
                ("title_en", title_en),
                ("product_attributes_en", product_attributes_en),
                ("text_details_en", text_details_en),
                ("translated_status", 1),
            ],
            where=[
                ("product_url","=", product_url)
            ]
        )

    logger.info("✅ All product data translated and saved to db")


def translate_product_img_texts(img_details_to_translate):

    SYSTEM_PROMPT = (
        "Return the list in the same order."
        "Detect and separate any combined English words that should be written with spaces between them"
        "Translate all Chinese text in this list to English."
    )
    
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    for image_url, image_text in img_details_to_translate:

        print(image_text)
        print("-"*100)

        translated_data = translate_entry(system_prompt=SYSTEM_PROMPT, entry=image_text, client=client)
        print(translated_data)
        print("="*100)
        if translated_data:
            translated_data = [line.replace("'", "''") for line in translated_data]

        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_IMAGES,
            column_with_value=[
                ("image_text_en", json.dumps(translated_data)),
                ("text_translated_status", "1")
            ],
            where=[
                ("image_url","=",image_url)
            ]
        )

    print("✅ All image texts translated and saved to db")