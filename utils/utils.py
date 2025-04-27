import json

def json_loads(json_string: str) -> dict:
    
    try:
        return json.loads(json_string)
    except:
        ...


def json_dumps(json_dct: dict) -> str:

    try:
        return json.dumps(json_dct)
    except:
        ...