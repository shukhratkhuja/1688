import os

from utils.prepare_db import main as prepare_tables
from utils.db_utils import insert_many, fetch_many, update_row
from utils.log_config import get_logger
from integrations.google_drive import (get_or_create_folder, 
                                       get_or_create_subfolder, 
                                       upload_to_drive_and_get_link)
from integrations.notion import get_urls, notion_update_json_content
from scraper import main as main_scraper
from utils.media_downloader import download_images
from ocr.paddle_ocr import main as text_extraction
from llm.translator import translate_product_data, translate_product_img_texts
import sys, time
import os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.constants import (DB_NAME, 
                            TABLE_PRODUCT_IMAGES, 
                            TABLE_PRODUCT_DATA,
                            LOCAL_OUTPUT_FOLDER,
                            GD_OUTPUT_FOLDER, 
                            GD_IMAGES_FOLDER)

logger = get_logger("main", "app.log")

def main():

    gd_main_folder_id=get_or_create_folder(folder_name=GD_OUTPUT_FOLDER)
    gd_images_folder_id = get_or_create_subfolder(parent_id=gd_main_folder_id, folder_name=GD_IMAGES_FOLDER)

    # creating table if not exists
    prepare_tables()

    # pulling urls from notion
    product_urls = get_urls()

    # if new urls coming
    if product_urls:

        # Taking urls from db
        existing_urls = fetch_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            columns_list=["product_url"],
            logger=logger
        )
        # Creating list of string urls from list of tuples
        existing_urls = [url[0] for url in existing_urls if existing_urls]
        logger.info(f"{len(existing_urls)} URLs in db now")

        # Separating new urls and which is not in db
        new_urls = [product_url for product_url in product_urls if product_url[0] not in existing_urls]
        logger.info(f"{len(new_urls)} new URLs coming")
        
        # Inserting new URLs into db
        if new_urls:
            insert_many(
                db=DB_NAME,
                table=TABLE_PRODUCT_DATA,
                columns_list=["product_url", "notion_product_id"],
                data=new_urls,
                logger=logger
            )

    urls_to_scrape = True # For entering the loop
    while urls_to_scrape:
        print("...")
        # Taking urls with not scraped status to scrape
        urls_to_scrape = fetch_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            columns_list=["product_url"],
            where=[("scraped_status", "=", "0")],
            limit=1,
            logger=logger
            )

        try:
            if urls_to_scrape:
                main_scraper(product_urls=urls_to_scrape, gd_main_folder_id=gd_main_folder_id)
            else:
                logger.info("No data to scrape...")
            time.sleep(1)
            break
        except Exception as error:
            logger.log_exception(error, context="scraping...")
        
        break
    logger.info("✅ Scraping finished successfully!")

    # imgs_to_download = True
    # while imgs_to_download:
    #     imgs_to_download = fetch_many(
    #         db=DB_NAME,
    #         table=TABLE_PRODUCT_IMAGES,
    #         columns_list=["image_url"],
    #         where=[("downloaded_status", "=", "0")],
    #         logger=logger
    #     )
    #     try:
    #         download_images(image_urls_list=imgs_to_download, gd_images_folder_id=gd_images_folder_id)
    #     except Exception as error:
    #         logger.log_exception(error, context="downloading images...")
    #     time.sleep(5)
    
    # logger.info("✅ Images downloaded successfully!")


    # imgs_to_text_extraction = True
    # while imgs_to_text_extraction:
    #     imgs_to_text_extraction = fetch_many(
    #         db=DB_NAME,
    #         table=TABLE_PRODUCT_IMAGES,
    #         columns_list=["image_url", "image_filename"],
    #         where=[("text_extracted_status", "=", "0"),
    #                ("image_filename","IS NOT", "NULL")
    #                ],
    #         logger=logger
    #     )
    #     print(imgs_to_text_extraction)
    #     try:
    #         text_extraction(img_details=imgs_to_text_extraction)
    #     except Exception as error:
    #         logger.log_exception(error, context="extracting text...")


    # print("finished")
    # data_to_translate = True
    # while data_to_translate:
    #     data_to_translate = fetch_many(
    #         db=DB_NAME,
    #         table=TABLE_PRODUCT_DATA,
    #         columns_list=["product_url","title_chn", "product_attributes_chn", "text_details_chn"],
    #         where=[
    #             ("scraped_status", "=", "1"),
    #             ("translated_status", "=", "0")
    #                ],
    #         limit=1,
    #         logger=logger
    #     )
    #     translate_product_data(product_data_to_translate=data_to_translate)
    #     break


    # imgs_to_translate = True
    # while imgs_to_translate:
    #     imgs_to_translate = fetch_many(
    #         db=DB_NAME,
    #         table=TABLE_PRODUCT_IMAGES,
    #         columns_list=["image_url","image_text"],
    #         where=[("text_translated_status", "=", "0"),
    #                ("text_extracted_status", "=", "1"),
    #                ("image_text", "!=", "None")],
    #         logger=logger,
    #         limit=3
    #     )
    #     translate_product_img_texts(img_details_to_translate=imgs_to_translate)
    #     break

    # not_uploaded_product_data = fetch_many(
    #     db=DB_NAME,
    #     table=TABLE_PRODUCT_DATA,
    #     columns_list=["product_url", 
    #                   "title_chn", 
    #                   "title_en", 
    #                   "product_attributes_chn",
    #                   "product_attributes_en",
    #                   "text_details_chn",
    #                   "text_details_en",
    #                   "notion_product_id"
    #                   ],
    #     where=[("uploaded_to_gd_status", "=", "0"),
    #            ("translated_status","=","1")]
    #     )
    # # gathering all data from db and create json file then upload to google drive 
    # logger.info("📁 Came to file upload part...")
    # if not_uploaded_product_data:
    #     for not_uploaded in not_uploaded_product_data:
    #         product_data = {}
            
    #         product_url = not_uploaded[0]
    #         title_chn = not_uploaded[1]
    #         title_en = not_uploaded[2]
    #         product_attributes_chn = not_uploaded[3]; product_attributes_chn = json.loads(product_attributes_chn)
    #         product_attributes_en = not_uploaded[4]; product_attributes_en = json.loads(product_attributes_en)
    #         text_details_chn = not_uploaded[5]; text_details_chn = json.loads(text_details_chn)
    #         text_details_en = not_uploaded[6]; text_details_en = json.loads(text_details_en)
            
    #         notion_product_id = not_uploaded[7]

    #         product_data["product_url"] = product_url
    #         product_data["title_chn"] = title_chn
    #         product_data["title_en"] = title_en
    #         product_data["product_attributes_chn"] = product_attributes_chn
    #         product_data["product_attributes_en"] = product_attributes_en
    #         product_data["text_details_chn"] = text_details_chn
    #         product_data["text_details_en"] = text_details_en
    #         product_data["images"] = []

    #         product_images_data = fetch_many(
    #             db=DB_NAME,
    #             table=TABLE_PRODUCT_IMAGES,
    #             columns_list=["image_url", 
    #                           "image_text", 
    #                           "image_text_en", 
    #                           "gd_img_url"],
    #             where=[
    #                 ("text_translated_status","=","1"),
    #                 ("product_url","=", product_url)

    #             ]
    #         )
    #         if product_images_data:
    #             for image_data in product_images_data:
    #                 image_url = image_data[0]
    #                 image_text = image_data[1]; image_text = json.loads(image_text)
    #                 image_text_en = image_data[2]; image_text_en = json.loads(image_text_en)
    #                 gd_img_url = image_data[3]
    #                 product_data["images"].append(
    #                     {
    #                      "image_url": image_url,  
    #                      "image_text": image_text,
    #                      "image_text_en": image_text_en,
    #                      "gd_img_url": gd_img_url
    #                     }
    #                 )
    #             print(product_data)

    #         product_data_filepath = f"{LOCAL_OUTPUT_FOLDER}/{notion_product_id}.json"
    #         with open(product_data_filepath, "w", encoding="utf-8") as jf:
    #             json.dump(product_data, jf, ensure_ascii=False)
            
    #         gd_file_url = upload_to_drive_and_get_link(gd_main_folder_id=gd_main_folder_id, 
    #                                                    local_filepath=product_data_filepath)
        
    #         update_row(
    #             db=DB_NAME,
    #             table=TABLE_PRODUCT_DATA,
    #             column_with_value=[
    #                 ("gd_file_url",gd_file_url),
    #                 ("uploaded_to_gd_status","1")
    #             ],
    #             where=[
    #                 ("product_url", "=", product_url)
    #             ]
    #         )
    # else:
    #     logger.info("No data to upload to google drive!")

    # logger.info("📁 Upload proccess finished!")


    # # update notion page with file url
    # logger.info("🔄 came to update notion with gd file url")
    # data_to_update_notion = fetch_many(
    #         db=DB_NAME,
    #         table=TABLE_PRODUCT_DATA,
    #         columns_list=["product_url",
    #                       "gd_file_url",
    #                     "notion_product_id"],
    #         where=[
    #             ("uploaded_to_gd_status", "=","1"),
    #             ("updated_on_notion_status", "=","0")
    #             ]
    #         )
    # if data_to_update_notion:
    #     for dt in data_to_update_notion:
    #         product_url = dt[0]
    #         gd_file_url = dt[1]
    #         notion_product_id = dt[2]

    #         notion_update_json_content(page_id=notion_product_id, gd_file_url=gd_file_url)
    #         update_row(
    #             db=DB_NAME,
    #             table=TABLE_PRODUCT_DATA,
    #             column_with_value=[
    #                 ("updated_on_notion_status","1")
    #             ],
    #             where=[
    #                 ("product_url","=",product_url)
    #             ]
    #         )
    # else:
    #     logger.info("No data to update on notion!")
        
    # logger.info("🔄 updating notion files finished!")


if __name__ == "__main__":

    main()