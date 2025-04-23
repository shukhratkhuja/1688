import time
import os, re, json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from dotenv import load_dotenv

from integrations.google_drive import upload_to_drive_and_get_link, get_or_create_folder
from utils.log_config import get_logger
from utils.db_utils import update_row, insert_many
from parser import parser
from utils.prepare_db import (DB_NAME, 
                              TABLE_PRODUCT_DATA, 
                              TABLE_PRODUCT_IMAGES, 
                              TABLE_PRODUCT_URLS
                            )

load_dotenv()
LOCAL_OUTPUT_FOLDER = os.getenv("LOCAL_OUTPUT_FOLDER", "output")
logger = get_logger("scraper", "app.log")


def extract_offer_id(url: str) -> str:
    match = re.search(r'/offer/(\d+)', url)
    return match.group(1) if match else "unknown"


def get_optimized_driver(headless=False):
    options = uc.ChromeOptions()
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-features=VizDisplayCompositor')
    if headless:
        options.add_argument('--headless=new')
    driver = uc.Chrome(options=options)
    return driver


def scrape(driver, url):
    driver.get(url)
    time.sleep(5)
    # optional: waiting neccery DOM
    try:
        WebDriverWait(driver, 50).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'title-text')]"))
        )
    except:

        logger.warning(f"Bad URL! No title-text found in {url}")
        return None

    html = driver.page_source

    # can be removed after testing
    offer_id = extract_offer_id(url=url)
    filename = f"{LOCAL_OUTPUT_FOLDER}/{offer_id}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"✅ Saved: {filename}")

    return html

def main(product_urls, gd_main_folder_id):

    # get masked driver
    driver = get_optimized_driver()
    driver.set_script_timeout(100)
    driver.maximize_window()

    """
    Website detecting the requested host is bot (or not) according to session history(or cookies)
    if session empty it returns capcha, 
    to solve this after first request we'll wait a bit, and then request another url
    without closing the session. So old session will be the history for next requests
    For that reason we add first url to the end of the list of urls.
    """
    product_urls.append(product_urls[0])

    for product_url in product_urls:

        json_filename = extract_offer_id(url=product_url)
        
        html = scrape(driver, product_url)

        parsed_data = parser(html)
        data = parsed_data

        time.sleep(1)

        output_filepath = os.path.join(LOCAL_OUTPUT_FOLDER, json_filename)
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        
        # upload json file to google drive
        gd_file_link = upload_to_drive_and_get_link(gd_main_folder_id=gd_main_folder_id, local_filepath=output_filepath)
        
        title_chn = data["title_chn"] if data else None
        product_attributes_chn = data["product_attributes_chn"] if data else None
        gallery_images = data["gallery_images"] if data else None
        text_details_chn = data["text_details_chn"] if data else None
        img_details = data["img_details"] if data else None

        product_images = gallery_images + img_details

        # inserting scraped data to db
        insert_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            columns_list=["product_url"
                          "file_name",
                          "title_chn",
                          "product_attributes_chn",
                          "text_details_chn",
                          "gd_file_url"],
            data=[(
                json_filename,
                title_chn,
                product_attributes_chn,
                text_details_chn,
                gd_file_link,
            )]
        )

        # inserting product images to db
        insert_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_IMAGES,
            columns_list=["image_url"],
            data=product_images
        )
        # update scraped status on product_urls table
        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_URLS,
            column_with_value=[("scraped_status","=","1")],
            where=["product_url", "=", product_url]
        )

    logger.info("📦 All product pages scraped.")
    driver.quit()