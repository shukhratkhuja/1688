import os

from dotenv import load_dotenv
from utils.log_config import get_logger
from utils.db_utils import prepare_table
load_dotenv()

DB_NAME = os.getenv("LOCAL_DB", "product_data.db")
TABLE_PRODUCT_URLS = os.getenv("TABLE_PRODUCT_URLS", "product_urls")
TABLE_PRODUCT_DATA = os.getenv("TABLE_PRODUCT_DATA", "product_data")
TABLE_PRODUCT_IMAGES = os.getenv("TABLE_PRODUCT_IMAGES", "product_images")
logger = get_logger("db", "app.log")

def main():

    # creating urls table
    prepare_table(
        db=DB_NAME,
        table=TABLE_PRODUCT_URLS,

        columns_dict={
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "product_url": "TEXT",
            "scraped_status": "BOOLEAN DEFAULT 0",
            "notion_id": "TEXT",
            "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
        },
        drop=True
    )

    # creating product data table
    prepare_table(
            db=DB_NAME, 
            table=TABLE_PRODUCT_DATA,
            columns_dict={
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "product_url": "TEXT",
                "title_chn": "TEXT",
                "title_en": "TEXT",
                "product_attributes_chn": "TEXT", # dumped json string
                "product_attributes_en": "TEXT", # dumped json string
                "text_details_chn": "TEXT", # dumped json string
                "text_details_en": "TEXT", # dumped json string
                "gd_file_url": "TEXT",
                "notion_id": "TEXT",
                "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
            },
            drop=True
            )
    
    # creating product images table
    prepare_table(db=DB_NAME, 
              table= TABLE_PRODUCT_IMAGES, 
              columns_dict={
                  "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                  "product_url": "TEXT",
                  "image_url": "TEXT",
                  "downloaded_status": "BOOLEAN DEFAULT 0",
                  "text_extracted_status": "BOOLEAN DEFAULT 0",
                  "text_translated_status": "BOOLEAN DEFAULT 0",
                  "image_name": "TEXT", # dumped list string
                  "image_text": "TEXT", # dumped list string
                  "image_text_en": "TEXT",
                  "gd_img_url": "TEXT",
                  "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
              },
              drop=True
              )


if __name__ == "__main__":
    main()