import requests
import os, json

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.log_config import get_logger
from notion_client import Client
from utils.constants import NOTION_BEARER_TOKEN, NOTION_DB_ID


logger = get_logger("notion", "app.log")
notion = Client(auth=NOTION_BEARER_TOKEN)

notion_product_id = ""
def get_urls():
    
    # taking first 100 urls from db where "CLEARED FOR SCRAPE" checkbox True
    try:
        response = notion.databases.query(
            database_id=NOTION_DB_ID,
            page_size=100,
            filter = {
                    "property": "CLEARED FOR SCRAPE",
                    "checkbox": {
                        "equals": True
                    }
                }
        )

    except Exception as error:
        logger.log_exception(error, context="notion connection")

    data = response.get("results")

    # Check if there are more than 100 urls and take them if there are
    if data:
        logger.info(f"{len(data)} rows came")

        while response["has_more"]:
            response = notion.databases.query(
                database_id=NOTION_DB_ID,
                page_size=100,
                start_cursor=response["next_cursor"],
                filter = {
                    "property": "CLEARED FOR SCRAPE",
                    "checkbox": {
                        "equals": True
                    }
                }
            )

            data.extend(response.get("results")) if response.get("results") else None
    else:
        logger.warning(f"No data came from notion")

    data_collection = []
    # extracting coming neccery columns and write
    for resp in data:
        # print(resp)
        notion_product_id = resp["id"]
        primary_supplier_url = resp["properties"]["PRIMARY SUPPLIER "]["url"]
        data_collection.append((primary_supplier_url, notion_product_id))
    
    return data_collection 
        
        
def update_json_content(notion, page_id, drive_file_id):
    direct_url = f"https://drive.google.com/uc?export=download&id={drive_file_id}"

    notion.pages.update(
        page_id=page_id,
        properties={
            "1668 JASON FILE": {
                "files": [
                    {
                        "name": "product_data.json",
                        "external": {
                            "url": direct_url
                        }
                    }
                ]
            }
        }
    )
