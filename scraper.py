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


from utils.db_utils import update_row, insert_many, fetch_many
from utils.log_config import get_logger
from utils.constants import (DB_NAME, 
                              TABLE_PRODUCT_DATA, 
                              TABLE_PRODUCT_IMAGES, 
                              TABLE_PRODUCT_URLS,
                              LOCAL_OUTPUT_FOLDER,
                              OXYLABS_USERNAME,
                              OXYLABS_PASSWORD,
                              OXYLABS_ENDPOINT
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

    # oxylab proxy

    # entry = ('http://customer-%s-cc-CN:%s@pr.oxylabs.io:7777' %
    #     (OXYLABS_USERNAME, OXYLABS_PASSWORD))

    # options.add_argument(f'--proxy-server={entry}')

    driver = uc.Chrome(options=options)
    logger.info("Get driver")
    return driver


def scrape(driver, url):

    # logger.info("🌐 IP ADDRESS: ", )
    
    driver.get(url)
    time.sleep(2)
    # optional: waiting neccery DOM
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'title-text')]"))
        )
    except:
        logger.warning(f"Bad URL! No title-text found in {url}")
        try:
            driver.find_element("xpath", "//h3[contains(text(), '商品已下架')]")
            logger.warning("⚠️ Element removed from the site!")
            return 404
        except:        
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
        if is_scraped == 404:
            update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            column_with_value=[
                ("scraped_status", "1"),
                ("translated_status", "1"),
                ("title_chn", "404"),
                ],
            where=[("product_url", "=", product_url)],
            logger=logger
            )
            continue
        elif not is_scraped:
           continue 

        parsed_data = None
        with open("page_source/current_page.html") as f:
            html = f.read()
            parsed_data = parser(html)
        
        if not parsed_data:
            continue

        logger.info("Moved to next loop...")
        time.sleep(1)

        # output_filepath = os.path.join(LOCAL_OUTPUT_FOLDER, f"{json_filename}.json")
        # with open(output_filepath, "w", encoding="utf-8") as f:
        #     json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        title_chn = parsed_data["title_chn"] if parsed_data else None
        product_attributes_chn = parsed_data["product_attributes_chn"] if parsed_data else None
        gallery_images = parsed_data["gallery_images"] if parsed_data else None
        text_details_chn = parsed_data["text_details_chn"] if parsed_data else None
        img_details = parsed_data["img_details"] if parsed_data else None

        # parsed images
        product_images = gallery_images + img_details

        # inserting scraped data to db
        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            column_with_value=[
                ("title_chn", title_chn),
                ("product_attributes_chn", json.dumps(product_attributes_chn,  ensure_ascii=False)),
                ("text_details_chn", json.dumps(text_details_chn,  ensure_ascii=False)),
            ],
            where=[
                ("product_url", "=", product_url)
                ],
            logger=logger
        )

        # inserting product images to db if not exists else add and update with current product id
        if product_images:
            existing_images = fetch_many(
                db=DB_NAME,
                table=TABLE_PRODUCT_IMAGES,
                columns_list=["image_url", 
                            "image_filename",
                            "image_text",
                            "image_text_en",
                            "downloaded_status",
                            "text_extracted_status",
                            "text_translated_status",
                            "product_url",
                            "gd_img_url"]
            )
            existing_image_urls = [row[0] for row in existing_images]

            image_details = [(product_url, img_url) for img_url in product_images]
            for product_url, img_url in image_details:
                if img_url not in existing_image_urls:
                    insert_many(
                        db=DB_NAME,
                        table=TABLE_PRODUCT_IMAGES,
                        columns_list=["product_url","image_url"],
                        data=[(product_url, img_url)],
                        logger=logger
                    )
                else:
                    lindex = existing_image_urls.index(img_url)
                    
                    image_url = existing_images[lindex][0]
                    image_filename = existing_images[lindex][1]
                    image_text = existing_images[lindex][2]
                    image_text_en = existing_images[lindex][3]
                    downloaded_status = existing_images[lindex][4]
                    text_extracted_status = existing_images[lindex][5]
                    text_translated_status = existing_images[lindex][6]
                    gd_img_url = existing_images[lindex][6]

                    row_data = (image_url, image_filename, image_text, image_text_en, 
                            downloaded_status, text_extracted_status, text_translated_status,
                            gd_img_url, product_url)

                    insert_many(
                        db=DB_NAME,
                        table=TABLE_PRODUCT_IMAGES,
                        columns_list=[
                            "image_url",
                            "image_filename",
                            "image_text",
                            "image_text_en",
                            "downloaded_status",
                            "text_extracted_status",
                            "text_translated_status",
                            "gd_img_url",
                            "product_url"
                        ],
                        data=[row_data],
                        logger=logger
                    )
                
        # update scraped status on product_urls table
        update_row(
            db=DB_NAME,
            table=TABLE_PRODUCT_DATA,
            column_with_value=[
                ("scraped_status", "1",)
                ],
            where=[("product_url", "=", product_url)],
            logger=logger
        )

    logger.info("📦 All product pages scraped.")
    driver.quit()