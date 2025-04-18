import time
import os, re, json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from dotenv import load_dotenv

from parser import parser

load_dotenv()
OUTPUT_FILE_PATH = os.getenv("OUTPUT_FILE_PATH")

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
    print(f"🔗 Opening: {url}")
    driver.get(url)
    time.sleep(5)
    # optional: kerakli DOM mavjudligini kutish
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'title-text')]"))
        )
    except:
        print(f"⚠️ Warning: No title-text found in {url}")
        return None

    html = driver.page_source

    # offer_id = extract_offer_id(url=url)
    # filename = f"{offer_id}.html"

    return html
   
    # with open(filename, "w", encoding="utf-8") as f:
    #     f.write(html)
    # print(f"✅ Saved: {filename}")

def main():
    urls = [
        "https://detail.1688.com/offer/777184250811.html?_t=1730862375591&spm=a2615.7691456.co_0_0_wangpu_score_0_0_0_0_0_0_0000_0.0",
        "https://detail.1688.com/offer/777184250811.html?_t=1730862375591&spm=a2615.7691456.co_0_0_wangpu_score_0_0_0_0_0_0_0000_0.0",
        "https://detail.1688.com/offer/771865212900.html?_t=1731918728168&spm=a2615.7691456.co_0_0_wangpu_score_0_0_0_0_0_0_0000_0.0",
        "https://detail.1688.com/offer/735430314845.html?_t=1739252024934&spm=a2615.7691456.co_0_0_wangpu_score_0_0_0_0_0_0_0000_0.0",
        # yana URL qo‘shing...
    ]

    driver = get_optimized_driver()
    driver.set_script_timeout(1000)
    driver.maximize_window()
    json_data = []
    for url in urls:
        
        data = {
            "url": url,
            "data": []
        }
        
        html = scrape(driver, url)

        if html:
            parsed_data = parser(html)
            data["data"] = parsed_data

        json_data.append(data)

        time.sleep(1)
    
    os.makedirs(OUTPUT_FILE_PATH, exist_ok=True)
    
    output_filename = os.path.join(OUTPUT_FILE_PATH, "result.json")
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)


    print("📦 All pages saved.")
    driver.quit()

if __name__ == "__main__":
    main()
