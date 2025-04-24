import os

from utils.log_config import get_logger
from utils.db_utils import prepare_table

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.constants import (DB_NAME,
                       TABLE_PRODUCT_DATA,
                       TABLE_PRODUCT_IMAGES,
                       TABLE_PRODUCT_URLS)

logger = get_logger("db", "app.log")

def main():

    # creating urls table
    prepare_table(
        db=DB_NAME,
        table=TABLE_PRODUCT_URLS,

        columns_dict={
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "product_url": "TEXT",
            "notion_product_id": "TEXT",
            "scraped_status": "BOOLEAN DEFAULT 0",
            "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
        },
        drop=True
    )
    logger.info("")

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
                "translated_status": "BOOLEAN DEFAULT 0",
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
                  "image_filename": "TEXT", 
                  "image_text_chn": "TEXT", # dumped list string
                  "image_text_en": "TEXT", # dumped list string
                  "gd_img_url": "TEXT",
                  "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
              },
              drop=True
              )


if __name__ == "__main__":
    main()