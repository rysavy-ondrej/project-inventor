import hashlib
from typing import Union

from jose import jwt

from utils import logs


def encrypt(data: dict, key: str) -> str:
    result = None
    try:
        result = jwt.encode(data, key, algorithm="HS256")
    except AttributeError:
        logs.error(f"Unable to encrypt the data - wrong data type {type(data)} instead of dictionary.")
    except jwt.JWSError:
        logs.error(f"Unable to encrypt the data - wrong key type {type(key)} instead of string.")
    except jwt.JWTError:
        logs.error(f"Unable to encrypt the data - unknown reason.")
    return result


def decrypt(ciphertext: str, key: str) -> Union[None, dict, str]:
    result = None
    try:
        result = jwt.decode(ciphertext, key, algorithms=["HS256"])
    except AttributeError:
        logs.error(f"Unable to decrypt the data - message must be a string and not {type(ciphertext)}.")
    except jwt.JWTError:
        if type(key) is not str:
            message = f"key be a string and not {type(key)}"
        else:
            message = "probably the key is invalid"
        logs.error(f"Unable to decrypt the data - {message}.")
    return result


def calculate_hash(data: str) -> str:
    result = None
    try:
        result = hashlib.sha256(data.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        logs.error(f"Unable to hash the value - encoding error.")
    except AttributeError:
        logs.error(f"Unable to hash the nonstring value type {type(data)}.")
    return result
