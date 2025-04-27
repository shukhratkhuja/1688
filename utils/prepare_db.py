import os

from utils.log_config import get_logger
from utils.db_utils import prepare_table

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.constants import (DB_NAME,
                       TABLE_PRODUCT_DATA,
                       TABLE_PRODUCT_IMAGES,
                       LOCAL_OUTPUT_FOLDER,
                       LOCAL_IMAGES_FOLDER
                       )

logger = get_logger("db", "app.log")

def main():

    # creating product data table
    prepare_table(
            db=DB_NAME, 
            table=TABLE_PRODUCT_DATA,
            columns_dict={
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                # main data columns
                "product_url": "TEXT",
                "title_chn": "TEXT",
                "title_en": "TEXT",
                "product_attributes_chn": "TEXT", # dumped json string
                "product_attributes_en": "TEXT", # dumped json string
                "text_details_chn": "TEXT", # dumped json string
                "text_details_en": "TEXT", # dumped json string
                # columns to check the process status
                "notion_product_id": "TEXT",
                "scraped_status": "BOOLEAN DEFAULT 0",
                "translated_status": "BOOLEAN DEFAULT 0",
                "gd_file_url": "TEXT",
                "uploaded_to_gd_status": "BOOLEAN DEFAULT 0",
                "updated_on_notion_status": "BOOLEAN DEFAULT 0",
                "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
            },
            drop=False
            )
    
    # creating product images table
    prepare_table(db=DB_NAME, 
              table= TABLE_PRODUCT_IMAGES, 
              columns_dict={
                  "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                  "image_url": "TEXT",
                  "image_filename": "TEXT", 
                  "image_text": "TEXT", # dumped list string
                  "image_text_en": "TEXT", # dumped list string
                  "downloaded_status": "BOOLEAN DEFAULT 0",
                  "text_extracted_status": "BOOLEAN DEFAULT 0",
                  "text_translated_status": "BOOLEAN DEFAULT 0",
                  "product_url": "TEXT",
                  "gd_img_url": "TEXT",
                  "created_at": "DATETIME DEFAULT (datetime('now','localtime'))"
              },
              drop=False
              )
    
    os.makedirs(LOCAL_OUTPUT_FOLDER, exist_ok=True)

    images_output_folder = os.path.join(LOCAL_OUTPUT_FOLDER, LOCAL_IMAGES_FOLDER)
    os.makedirs(images_output_folder, exist_ok=True)

if __name__ == "__main__":
    main()