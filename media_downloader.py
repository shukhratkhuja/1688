import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote


def decode_filename(image_url):
    
    parsed = urlparse(image_url)
    image_name = os.path.basename(parsed.path)

    return image_name


def dowload_file(img_url, base_file_path):

    if img_url:
    
        response = requests.get(img_url)
        img_filename = decode_filename(img_url)
    
        if response.status_code == 200:
    
            with open(f"{base_file_path}/{img_filename}", "wb") as f:
                f.write(response.content)
            print("✅ File saved:", f"{img_filename}")
            
        else:
            print(response.content)
            print("❌ File not downloaded:", img_url)


def media_main():
    

    load_dotenv()

    IMAGES_FOLDER = os.getenv("IMAGES_FOLDER", "images")
    os.makedirs(IMAGES_FOLDER, exist_ok=True)

    ...