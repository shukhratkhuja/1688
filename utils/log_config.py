import logging
import traceback
import os
from dotenv import load_dotenv

load_dotenv()
ENV = os.getenv("ENV", "dev")

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

class CustomLogger(logging.Logger):
    def log_exception(self, exception: Exception, context: str = None):
        error_type = type(exception).__name__
        error_message = str(exception)
        traceback_str = traceback.format_exc()

        prefix = f"❌ EXCEPTION"
        if context:
            prefix += f" IN {context.upper()}"

        self.error(f"{prefix}\n"
                   f"Type: {error_type}\n"
                   f"Message: {error_message}\n"
                   f"Traceback:\n{traceback_str}")

# logger klassini ro'yxatdan o'tkazamiz
logging.setLoggerClass(CustomLogger)


class UppercaseFilter(logging.Filter):
    def filter(self, record):
        record.name = record.name.upper()
        return True
    

def get_logger(name: str, log_file: str, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Oldini olish: logger har chaqirilganda 2-3 marta handler ulanmasligi
    if logger.hasHandlers():
        return logger

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Fayl handler
    file_path = os.path.join(LOG_DIR, log_file)
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(UppercaseFilter())
    logger.addHandler(file_handler)

    # Dev rejimida konsolga ham chiqaramiz
    if ENV != "prod":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(UppercaseFilter())
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger
