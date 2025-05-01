import json
from json import JSONDecodeError
import logging
from typing import Optional, Dict, Any

# Get logger for this module
logger = logging.getLogger("utils")

def json_loads(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON string into a Python dictionary.
    
    Args:
        json_string (str): The JSON string to parse
        
    Returns:
        Dict or None: The parsed JSON object as a dictionary, or None if parsing failed
    """
    if not json_string:
        return None
    
    try:
        # Replace single quotes with double quotes for JSON compatibility
        json_string = json_string.replace("'", "''")
        return json.loads(json_string)
    except JSONDecodeError as jde:
        logger.error(f"JSON decode error: {str(jde)}")
        return None
    except Exception as error:
        logger.error(f"Error while loading JSON string: {str(error)}")
        return None


def json_dumps(json_dct: dict) -> Optional[str]:
    """
    Safely convert a Python dictionary to a JSON string.
    
    Args:
        json_dct (dict): The dictionary to convert
        
    Returns:
        str or None: The JSON string representation, or None if conversion failed
    """
    if not json_dct:
        return None
    
    try:
        return json.dumps(json_dct, ensure_ascii=False)
    except JSONDecodeError as jde:
        logger.error("JSON decode error while dumping dictionary to string")
        raise jde
    except TypeError as te:
        logger.error(f"Type error while dumping JSON: {str(te)}")
        # Try to sanitize the dictionary by converting problematic types
        sanitized_dict = _sanitize_json_dict(json_dct)
        return json.dumps(sanitized_dict, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Error while dumping JSON to string: {str(error)}")
        raise error

def _sanitize_json_dict(data: Dict) -> Dict:
    """
    Attempt to sanitize a dictionary to make it JSON serializable.
    
    Args:
        data (dict): The dictionary to sanitize
        
    Returns:
        dict: A sanitized copy of the dictionary
    """
    if isinstance(data, dict):
        return {k: _sanitize_json_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize_json_dict(i) for i in data]
    elif isinstance(data, (int, float, str, bool, type(None))):
        return data
    else:
        # Convert any other type to string
        return str(data)