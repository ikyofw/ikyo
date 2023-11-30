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


'''
    YL.ikyo, 2022-11-21
    check email
'''


def isEmail(email) -> bool:
    if email is None or email == '':
        return False
    if email.endswith('@ywlgroup.com') or email.endswith('@int.ywlgroup.com'):
        return True
    return False
