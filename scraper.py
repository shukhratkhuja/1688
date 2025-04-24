import time
import os, re, json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

from integrations.google_drive import upload_to_drive_and_get_link, get_or_create_folder
from parser import parser

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_utils import update_row, insert_many
from utils.log_config import get_logger
from utils.constants import (DB_NAME, 
                              TABLE_PRODUCT_DATA, 
                              TABLE_PRODUCT_IMAGES, 
                              TABLE_PRODUCT_URLS,
                              LOCAL_OUTPUT_FOLDER
                            )

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
    logger.info("Get driver")
    return driver


def scrape(driver, url):
    
    driver.get(url)
    time.sleep(2)
    # optional: waiting neccery DOM
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'title-text')]"))
        )
    except:
        logger.warning(f"Bad URL! No title-text found in {url}")
        return None
    
    try:
        WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'content-detail')]"))
            )
    except Exception as error:
        logger.warning("No content-details appeared!")
    
    # html output filepath
    filename = f"page_source/current_page.html"

    html = driver.page_source
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"✅ Saved: {filename}")

    return True

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

    # coming list of tuples like [(url1,), ...]
    for product_url in product_urls:

        product_url = product_url[0]

        json_filename = extract_offer_id(url=product_url)

        is_scraped = scrape(driver, product_url)

        if not is_scraped:
           continue 

        parsed_data = None
        with open("page_source/current_page.html") as f:
            html = f.read()
            parsed_data = parser(html)
        
        if not parsed_data:
            continue

        logger.info("Moved to next loop...")
        time.sleep(1)

        output_filepath = os.path.join(LOCAL_OUTPUT_FOLDER, f"{json_filename}.json")
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        title_chn = parsed_data["title_chn"] if parsed_data else None
        product_attributes_chn = parsed_data["product_attributes_chn"] if parsed_data else None
        gallery_images = parsed_data["gallery_images"] if parsed_data else None
        text_details_chn = parsed_data["text_details_chn"] if parsed_data else None
        img_details = parsed_data["img_details"] if parsed_data else None

        product_images = gallery_images + img_details

        # inserting scraped data to db
        insert_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            columns_list=["product_url",
                          "title_chn",
                          "product_attributes_chn",
                          "text_details_chn"
                          ],
            data=[(
                product_url,
                title_chn,
                json.dumps(product_attributes_chn),
                json.dumps(text_details_chn),
            )],
            logger=logger
        )

        # inserting product images to db
        image_details = [(product_url, img_url) for img_url in product_images]
        insert_many(
            db=DB_NAME,
            table=TABLE_PRODUCT_IMAGES,
            columns_list=["product_url","image_url"],
            data=image_details,
            logger=logger
        )
        # update scraped status on product_urls table
        print(product_url)
        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_URLS,
            column_with_value=[
                ("scraped_status", "1",)
                ],
            where=[("product_url", "=", product_url)],
            logger=logger
        )

    logger.info("📦 All product pages scraped.")
    driver.quit()