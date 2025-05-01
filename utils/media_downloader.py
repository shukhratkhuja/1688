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
    """
    Download an image from a URL and upload it to Google Drive.
    
    Args:
        img_url (str): URL of the image to download
        base_file_path (str): Local directory to save the image
        gd_images_folder_id (str): Google Drive folder ID for images
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    if not img_url:
        logger.error("Empty image URL provided")
        return False

    try:
        entry = ('http://customer-%s-cc-CN:%s@%s' %
                (OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT))

        proxies = {
            "http": entry,
            "https": entry
        }
        
        # Fallback to no proxy if needed
        proxies = {}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.1688.com/"
        }
        
        session = requests.Session()
        session.proxies = proxies
        session.headers.update(headers)
        
        # Add timeout to prevent hanging
        response = session.get(img_url, timeout=(10, 30))  # 10s connect, 30s read
        
        if "rgv587_flag" in response.text:
            logger.warning("CAPTCHA detected or waiting required!")
            time.sleep(random.uniform(5, 15))  # Random sleep on CAPTCHA
            return False

        img_filename = decode_filename(img_url)
        
        if response.status_code == 200:
            # Ensure the directory exists
            os.makedirs(base_file_path, exist_ok=True)
            
            file_path = f"{base_file_path}/{img_filename}"
            with open(file_path, "wb") as f:
                f.write(response.content)
                logger.info(f"✅ File saved: {img_filename}. URL: {img_url}")
            
            # Handle potential Google Drive upload failures
            try:
                gd_image_id = upload_image_if_not_exists(
                    images_folder_id=gd_images_folder_id,
                    local_image_path=file_path
                )
                
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
            except Exception as e:
                logger.error(f"Failed to upload to Google Drive: {str(e)}")
                # Update DB to mark as downloaded but failed upload
                update_row(
                    db=DB_NAME,
                    table=TABLE_PRODUCT_IMAGES,
                    column_with_value=[
                        ("downloaded_status", "1"),
                        ("image_filename", img_filename),
                        ("gd_img_url", "upload_failed"),
                    ],
                    where=[("image_url","=",img_url)]
                )
                return False
                
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
        elif response.status_code in (429, 403):
            logger.warning(f"Rate limited or access denied: {response.status_code}")
            time.sleep(random.uniform(10, 20))  # Back off on rate limiting
            return False
        else:
            logger.error(f"❌ File not downloaded: {img_url}, Response Code: {response.status_code}, Response: {str(response.content)[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while downloading image: {img_url}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while downloading image: {img_url}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while downloading image {img_url}: {str(e)}")
        return False

def download_images(image_urls_list, gd_images_folder_id, max_retries=3):
    """
    Download multiple images with retry logic.
    
    Args:
        image_urls_list (list): List of image URLs to download
        gd_images_folder_id (str): Google Drive folder ID for images
        max_retries (int): Maximum number of retry attempts for failed downloads
        
    Returns:
        dict: Dictionary of results with URLs as keys and success status as values
    """
    results = {}
    
    # coming img_urls_list as list of tuples like [(img_url), ]
    for img_url_tuple in image_urls_list:
        img_url = img_url_tuple[0]
        
        # Skip empty URLs
        if not img_url:
            logger.warning("Empty image URL found, skipping")
            continue
        
        # Implement retry logic
        success = False
        attempts = 0
        
        while not success and attempts < max_retries:
            attempts += 1
            
            # Exponential backoff if retrying
            if attempts > 1:
                backoff_time = random.uniform(5, 15) * (attempts - 1)
                logger.info(f"Retry attempt {attempts} for {img_url}, waiting {backoff_time:.2f}s")
                time.sleep(backoff_time)
            
            # Randomized sleep between requests
            sleep_time = random.uniform(1, 5)
            logger.info(f"Sleep time between downloads: {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
            # Download the image
            success = download_file(
                img_url=img_url, 
                base_file_path=f"{LOCAL_OUTPUT_FOLDER}/{LOCAL_IMAGES_FOLDER}", 
                gd_images_folder_id=gd_images_folder_id
            )
        
        results[img_url] = success
        
        if not success:
            logger.warning(f"Failed to download {img_url} after {max_retries} attempts")
    
    return results
