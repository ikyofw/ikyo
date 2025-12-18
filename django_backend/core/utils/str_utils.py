import re
import string
from datetime import datetime
from random import randint


def getTimestamp(timestamp=None, format='%Y%m%d%H%M%S%f') -> str:
    '''
        timestamp: none means current
        format: default %Y%m%d%H%M%S%f
    '''
    dt = datetime.now() if timestamp is None else timestamp
    return datetime.strftime(dt, format)


def isEmpty(s) -> bool:
    # Deprecated: This method is no longer recommended. It will be removed in a future version.
    if s is None or type(s) == str and s == '':
        return True
    return False


def is_null_or_empty(s, trim_whitespace=True) -> bool:
    if trim_whitespace and isinstance(s, str):
        s = s.strip()
    if s is None or type(s) == str and s == '':
        return True
    return False


def stripStr(s) -> str | None:
    if isEmpty(s):
        return None
    if not isinstance(s, str):
        s = str(s)
    return s.strip()


def getRandomStr(length) -> str:
    return "".join(string.ascii_letters[randint(0, 51)] for _ in range(length))


def isEmail(email) -> bool:
    if email is None or email == '':
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
