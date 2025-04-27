import json

def json_loads(json_string: str) -> dict:
    
    json_string = json_string.replace("'", "''")

    try:
        return json.loads(json_string)
    except Exception as error:
        print(str(error))


def json_dumps(json_dct: dict) -> str:

    try:
        return json.dumps(json_dct, ensure_ascii=False)
    except Exception as error:
        print("Error while dumping json to string")
        raise error