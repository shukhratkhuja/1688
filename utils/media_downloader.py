from urllib.parse import urlparse
import requests
import time
import os
from integrations.google_drive import upload_image_if_not_exists
import sys
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.log_config import get_logger
from utils.db_utils import insert_many, update_row
from utils.constants import (DB_NAME, 
                             TABLE_PRODUCT_IMAGES, 
                             LOCAL_IMAGES_FOLDER, 
                             LOCAL_OUTPUT_FOLDER,
                             OXYLABS_USERNAME,
                             OXYLABS_PASSWORD,
                             OXYLABS_ENDPOINT

                            )

logger = get_logger("image download", "app.log")

def decode_filename(image_url):
    
    parsed = urlparse(image_url)
    image_name = os.path.basename(parsed.path)

    return image_name


def download_file(img_url, base_file_path, gd_images_folder_id):

    if img_url:

        entry = entry = ('http://customer-%s-cc-CN:%s@%s' %
            (OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT))

        proxies = {
            "http": entry,
            "https": entry
        }
        print(proxies)
        # proxies={}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.1688.com/"
        }
        proxies = {}
        session = requests.Session()
        session.proxies = proxies
    
        session.headers.update(headers)

        response = session.get(img_url)
        if "rgv587_flag" in response.text:
            print("CAPTCHA chiqdi yoki kutish kerak!")
        else:
            ...
            
        img_filename = decode_filename(img_url)

        print(response.status_code)
    
        if response.status_code == 200:

            with open(f"{base_file_path}/{img_filename}", "wb") as f:
                f.write(response.content)
                logger.info(f"✅ File saved: {img_filename}. URL: {img_url}")
            
            gd_image_id = upload_image_if_not_exists(images_folder_id=gd_images_folder_id, 
                                                     local_image_path=f"{base_file_path}/{img_filename}")
            
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[
                    ("downloaded_status", "1"),
                    ("image_filename", img_filename),
                    ("gd_img_url", gd_image_id),
                ],
                where=[("image_url","=",img_url)]
            )
            return True
        elif response.status_code == 404:
            update_row(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                column_with_value=[
                    ("downloaded_status", "1"),
                    ("image_filename", img_filename),
                    ("gd_img_url", "404"),
                ],
                where=[("image_url","=",img_url)]
            )
            return True

        else:
            logger.error(f"❌ File not downloaded: {img_url}, Response: {str(response.content)}")
            return None


def download_images(image_urls_list, gd_images_folder_id):
    
    # coming img_urls_list as list of tuples like [(img_url), ]
    for img_url in image_urls_list:
        sleep_time = random.randint(30,99) * 0.1
        # download single image
        img_url = img_url[0]

        download_file(img_url=img_url, base_file_path=f"{LOCAL_OUTPUT_FOLDER}/{LOCAL_IMAGES_FOLDER}", gd_images_folder_id=gd_images_folder_id)
        
        logger.info(f"Sleep time while blocking: {sleep_time}")
        time.sleep(sleep_time)
