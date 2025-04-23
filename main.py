import os

from utils.prepare_db import main as prepare_tables
from integrations.notion import get_urls
from utils.db_utils import insert_many, fetch_many
from utils.log_config import get_logger
from utils.prepare_db import DB_NAME, TABLE_PRODUCT_URLS, TABLE_PRODUCT_IMAGES
from integrations.google_drive import get_or_create_folder, get_or_create_subfolder
from scraper import main as main_scraper
from dotenv import load_dotenv
from integrations.notion import get_urls
from utils.media_downloader import download_images

load_dotenv()

GD_OUTPUT_FOLDER = os.getenv("GD_OUTPUT_FOLDER", "1688_product_data")
GD_IMAGES_FOLDER = os.getenv("GD_IMAGES_FOLDER", "images")

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
            table=TABLE_PRODUCT_URLS,
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
                table=TABLE_PRODUCT_URLS,
                columns_list=["product_url", "notion_product_id"],
                data=new_urls,
                logger=logger
            )

    urls_to_scrape = True # For entering the loop
    while urls_to_scrape:

        # Taking urls with not scraped status to scrape
        urls_to_scrape = fetch_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_URLS,
            columns_list=["product_url"],
            where=[("scraped_status", "=", "0")],
            logger=logger
            )

        try:
            main_scraper(urls_to_scrape)
            break
        except Exception as error:
            logger.log_exception(error, context="scraping...")

        

    logger.info("✅ Scraping finished successfully!")



    imgs_to_download = True
    while imgs_to_download:
        imgs_to_download = fetch_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_IMAGES,
            columns_list=["image_url"],
            where=[("downloaded_status", "=", "0")],
            logger=logger
        )
        try:
            download_images(image_urls_list=imgs_to_download, gd_images_folder_id=gd_images_folder_id)
        except Exception as error:
            logger.log_exception(error, context="downloading images...")
    
    logger.info("✅ Images downloaded successfully!")

    