import os
from dotenv import load_dotenv
load_dotenv()

# db 
DB_NAME=os.getenv("LOCAL_DB", "product_data.db")
TABLE_PRODUCT_DATA=os.getenv("TABLE_PRODUCT_DATA", "product_data")
TABLE_PRODUCT_IMAGES=os.getenv("TABLE_PRODUCT_IMAGES", "product_images")

# folder names
LOCAL_IMAGES_FOLDER=os.getenv("LOCAL_IMAGES_FOLDER", "images")
LOCAL_OUTPUT_FOLDER=os.getenv("LOCAL_OUTPUT_FOLDER", "output")
GD_OUTPUT_FOLDER=os.getenv("GD_OUTPUT_FOLDER", "1688_product_data")
GD_IMAGES_FOLDER=os.getenv("GD_IMAGES_FOLDER", "images")

# env & task vars
ENV=os.getenv("ENV", "dev")
HEADLESS=os.getenv("HEADLESS", False)
TRANSLATION_MODEL=os.getenv("TRANSLATION_MODEL", "gpt-3.5-turbo")
# tokens & ids
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", "default_openai_token")
NOTION_BEARER_TOKEN=os.getenv("NOTION_BEARER_TOKEN", "default_notion_token")
NOTION_DB_ID=os.getenv("NOTION_DB_ID", "default_db_id")

# oxylabs
OXYLABS_USERNAME=os.getenv("OXYLABS_USERNAME", "oxylabs_username")
OXYLABS_PASSWORD=os.getenv("OXYLABS_PASSWORD", "oxylabs_password")
OXYLABS_ENDPOINT=os.getenv("OXYLABS_ENDPOINT", "pr.oxylabs.io:7777")
