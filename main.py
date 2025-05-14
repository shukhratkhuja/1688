import os
import sys
import time
import json, requests
import sqlite3
from contextlib import contextmanager

from utils.prepare_db import main as prepare_tables
from utils.db_utils import insert_many, fetch_many, update_row
from utils.log_config import get_logger
from integrations.google_drive import (get_or_create_folder, 
                                       get_or_create_subfolder, 
                                       get_or_create_sub_subfolder, 
                                       upload_to_drive_and_get_link)
from integrations.notion import get_urls, notion_update_json_content
from scraper import main as main_scraper
from utils.media_downloader import download_images
from ocr.paddle_ocr import main as text_extraction
from llm.translator import translate_product_data, translate_product_img_texts
from utils.utils import json_dumps, json_loads

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.constants import (DB_NAME, 
                            TABLE_PRODUCT_IMAGES, 
                            TABLE_PRODUCT_DATA,
                            LOCAL_OUTPUT_FOLDER,
                            GD_OUTPUT_FOLDER, 
                            GD_IMAGES_FOLDER)

logger = get_logger("main", "app.log")

@contextmanager
def handle_process(name, retries=3, retry_delay=5):
    """
    Context manager for handling process execution with proper error handling, 
    logging, and optional retries.
    
    Args:
        name (str): Name of the process for logging
        retries (int): Number of retries for transient errors
        retry_delay (int): Base delay between retries in seconds
        
    Yields:
        None
    """
    retry_count = 0
    last_error = None
    
    while retry_count <= retries:
        try:
            if retry_count > 0:
                logger.info(f"Retry attempt {retry_count}/{retries} for {name} process...")
                # Exponential backoff
                time.sleep(retry_delay * (2 ** (retry_count - 1)))
            else:
                logger.info(f"Starting {name} process...")
                
            yield
            logger.info(f"✅ {name} process completed successfully!")
            return
        except (requests.exceptions.Timeout, 
                requests.exceptions.ConnectionError, 
                sqlite3.OperationalError) as e:
            # These errors may be transient, so we'll retry
            retry_count += 1
            last_error = e
            logger.warning(f"Transient error in {name} process (attempt {retry_count}/{retries}): {str(e)}")
            
            if retry_count > retries:
                logger.error(f"❌ {name} process failed after {retries} retries")
                logger.log_exception(last_error, context=name)
                raise
        except Exception as error:
            # Non-transient error, don't retry
            logger.error(f"❌ {name} process failed with non-transient error")
            logger.log_exception(error, context=name)
            raise


def main():
    try:
        with handle_process("Google Drive setup"):
            gd_main_folder_id = get_or_create_folder(folder_name=GD_OUTPUT_FOLDER)
            gd_images_folder_id = get_or_create_subfolder(parent_id=gd_main_folder_id, folder_name=GD_IMAGES_FOLDER)

        with handle_process("Database setup"):
            prepare_tables()

        with handle_process("URL processing"):
            product_urls = get_urls()
            if product_urls:
                existing_urls = fetch_many(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_DATA,
                    columns_list=["product_url"],
                    logger=logger
                )
                existing_urls = [url[0] for url in existing_urls if existing_urls]
                logger.info(f"{len(existing_urls)} URLs in db now")

                new_urls = [product_url for product_url in product_urls if product_url[0] not in existing_urls]
                logger.info(f"{len(new_urls)} new URLs coming")
                
                if new_urls:
                    insert_many(
                        db=DB_NAME,
                        table=TABLE_PRODUCT_DATA,
                        columns_list=["product_url", "notion_product_id"],
                        data=new_urls,
                        logger=logger
                    )

        with handle_process("Scraping"):
            urls_to_scrape = True
            while urls_to_scrape:
                urls_to_scrape = fetch_many(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_DATA,
                    columns_list=["product_url"],
                    where=[("scraped_status", "=", "0")],
                    logger=logger
                )

                if urls_to_scrape:

                    main_scraper(product_urls=urls_to_scrape, gd_main_folder_id=gd_main_folder_id, gd_images_folder_id=gd_images_folder_id)
                else:
                    logger.info("No data to scrape...")
                time.sleep(1)

        with handle_process("Image downloading"):
            imgs_to_download = True
            while imgs_to_download:
                imgs_to_download = fetch_many(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_IMAGES,
                    columns_list=["image_url", "gd_product_images_folder_id"],
                    where=[("downloaded_status", "=", "0")],
                    logger=logger
                )
                if imgs_to_download:
                    download_images(image_details_to_downlaod=imgs_to_download)
                time.sleep(5)

        with handle_process("Text extraction"):
            imgs_to_text_extraction = True
            while imgs_to_text_extraction:
                imgs_to_text_extraction = fetch_many(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_IMAGES,
                    columns_list=["image_url", "image_filename"],
                    where=[("text_extracted_status", "=", "0"),
                           ("image_filename","IS NOT", "NULL"),
                            ("gd_img_url", "!=", "404")
                           ],
                    logger=logger
                )
                if imgs_to_text_extraction:
                    text_extraction(img_details=imgs_to_text_extraction)
        

        with handle_process("Translation"):
            data_to_translate = True
            while data_to_translate:
                data_to_translate = fetch_many(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_DATA,
                    columns_list=["product_url","title_chn", "product_attributes_chn", "text_details_chn"],
                    where=[
                        ("scraped_status", "=", "1"),
                        ("translated_status", "=", "0"),
                        ("title_chn","!=", "404")
                           ],
                    logger=logger
                )
                if data_to_translate:
                    translate_product_data(product_data_to_translate=data_to_translate)

            imgs_to_translate = True
            while imgs_to_translate:
                imgs_to_translate = fetch_many(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_IMAGES,
                    columns_list=["image_url","image_text"],
                    where=[("text_translated_status", "=", "0"),
                           ("text_extracted_status", "=", "1"),
                           ("image_text", "!=", "None")],
                    logger=logger,
                )
                if imgs_to_translate:
                    translate_product_img_texts(img_details_to_translate=imgs_to_translate)


        with handle_process("Google Drive upload"):
            not_uploaded_product_data = fetch_many(
                db=DB_NAME,
                table=TABLE_PRODUCT_DATA,
                columns_list=["product_url", 
                              "title_chn", 
                              "title_en", 
                              "product_attributes_chn",
                              "product_attributes_en",
                              "text_details_chn",
                              "text_details_en",
                              "notion_product_id"
                              ],
                where=[("uploaded_to_gd_status", "=", "0"),
                       ("translated_status","=","1")
                       ]
            )

            if not_uploaded_product_data:
                for not_uploaded in not_uploaded_product_data:
                    try:
                        product_data = {}
                        product_url = not_uploaded[0]
                        title_chn = not_uploaded[1]
                        title_en = not_uploaded[2]
                        product_attributes_chn = json_loads(not_uploaded[3])
                        product_attributes_en = json_loads(not_uploaded[4])
                        text_details_chn = json_loads(not_uploaded[5])
                        text_details_en = json_loads(not_uploaded[6])
                        notion_product_id = not_uploaded[7]

                        product_data.update({
                            "product_url": product_url,
                            "title_chn": title_chn,
                            "title_en": title_en,
                            "product_attributes_chn": product_attributes_chn,
                            "product_attributes_en": product_attributes_en,
                            "text_details_chn": text_details_chn,
                            "text_details_en": text_details_en,
                            "images": []
                        })

                        product_images_data = fetch_many(
                            db=DB_NAME,
                            table=TABLE_PRODUCT_IMAGES,
                            columns_list=["image_url", 
                                          "image_text", 
                                          "image_text_en", 
                                          "gd_img_url"],
                            where=[
                                ("product_url","=", product_url)
                            ]
                        )

                        if product_images_data:
                            for image_data in product_images_data:
                                image_url = image_data[0]
                                image_text = json_loads(image_data[1])
                                image_text_en = json_loads(image_data[2])
                                gd_img_url = image_data[3]
                                product_data["images"].append({
                                    "image_url": image_url,  
                                    "image_text": image_text,
                                    "image_text_en": image_text_en,
                                    "gd_img_url": gd_img_url
                                })

                        product_data_filepath = f"{LOCAL_OUTPUT_FOLDER}/{notion_product_id}.json"
                        with open(product_data_filepath, "w", encoding="utf-8") as jf:
                            json.dump(product_data, jf, ensure_ascii=False)
                        
                        gd_file_url = upload_to_drive_and_get_link(
                            gd_main_folder_id=gd_main_folder_id, 
                            local_filepath=product_data_filepath
                        )
                    
                        update_row(
                            db=DB_NAME,
                            table=TABLE_PRODUCT_DATA,
                            column_with_value=[
                                ("gd_file_url", gd_file_url),
                                ("uploaded_to_gd_status", "1")
                            ],
                            where=[("product_url", "=", product_url)]
                        )
                    except Exception as error:
                        logger.log_exception(error, context=f"Processing product {product_url}")

        with handle_process("Notion update"):
            data_to_update_notion = fetch_many(
                db=DB_NAME,
                table=TABLE_PRODUCT_DATA,
                columns_list=["product_url", "gd_file_url", "notion_product_id", "gd_product_images_folder_id"],
                where=[
                    ("uploaded_to_gd_status", "=", "1"),
                    ("updated_on_notion_status", "=", "0")
                ]
            )

            if data_to_update_notion:
                for dt in data_to_update_notion:
                    try:
                        product_url = dt[0]
                        gd_file_url = dt[1]
                        notion_product_id = dt[2]
                        gd_product_images_folder_id = dt[3]

                        notion_update_json_content(page_id=notion_product_id, gd_file_url=gd_file_url, gd_product_images_folder_id=gd_product_images_folder_id)
                        update_row(
                            db=DB_NAME,
                            table=TABLE_PRODUCT_DATA,
                            column_with_value=[("updated_on_notion_status", "1")],
                            where=[("product_url", "=", product_url)]
                        )
                    except Exception as error:
                        logger.log_exception(error, context=f"Updating Notion for product {product_url}")

    except Exception as error:
        logger.log_exception(error, context="main process")
        raise

if __name__ == "__main__":
    main()