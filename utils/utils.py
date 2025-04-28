import json
from json import JSONDecodeError

def json_loads(json_string: str) -> dict:

    if json_string:
        json_string = json_string.replace("'", "''")
    else:
        return None
    
    try:
        return json.loads(json_string)
    except Exception as error:
        print(str(error))


def json_dumps(json_dct: dict) -> str:

    if json_dct:

        try:
            return json.dumps(json_dct, ensure_ascii=False)
        except JSONDecodeError as jde:
            print("ERROR: Json decode error")
            raise jde
        except Exception as error:
            print("Error while dumping json to string")
            raise error
    else:
        return None