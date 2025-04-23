from urllib.parse import urlparse
import requests
import time
import os
from dotenv import load_dotenv
from utils.log_config import get_logger
from integrations.google_drive import upload_image_if_not_exists
from db_utils import insert_many, update_row
from prepare_db import DB_NAME, TABLE_PRODUCT_IMAGES
load_dotenv()

LOCAL_IMAGES_FOLDER = os.getenv("IMAGES_FOLDER", "images")
logger = get_logger("image download", "app.log")

def decode_filename(image_url):
    
    parsed = urlparse(image_url)
    image_name = os.path.basename(parsed.path)

    return image_name


def download_file(img_url, base_file_path, gd_images_folder_id):

    if img_url:
    
        response = requests.get(img_url)
        img_filename = decode_filename(img_url)
    
        if response.status_code == 200:

            with open(f"{base_file_path}/{img_filename}", "wb") as f:
                f.write(response.content)
            logger.info("✅ File saved:", f"{img_filename}. URL: {img_url}")
            
            gd_image_id = upload_image_if_not_exists(images_folder_id=gd_images_folder_id, 
                                                     local_image_path=f"{base_file_path}/{img_filename}")

            insert_many(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,

            )

            return gd_image_id

        else:
            logger.error(f"❌ File not downloaded: {img_url}, Response: {str(response.content)}")
            
    return None


def download_images(image_urls_list, gd_images_folder_id):
    
    os.makedirs(LOCAL_IMAGES_FOLDER, exist_ok=True)

    for img_url in image_urls_list:
        # download single image
        download_file(img_url=img_url, base_file_path=LOCAL_IMAGES_FOLDER, gd_images_folder_id=gd_images_folder_id)
        time.sleep(3)