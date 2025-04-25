import sys, os, requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from utils.db_utils import update_row, insert_many
from utils.log_config import get_logger
from utils.constants import (
                              OXYLABS_USERNAME,
                              OXYLABS_PASSWORD,
                              OXYLABS_ENDPOINT
                            )

entry = entry = ('http://customer-%s-cc-CN:%s@pr.oxylabs.io:7777' %
    (OXYLABS_USERNAME, OXYLABS_PASSWORD))

proxies = {
    "http": entry,
    "https": entry
}

response = requests.get("https://httpbin.org/ip", proxies=proxies)
print(response.text)

