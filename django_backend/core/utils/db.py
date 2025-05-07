import datetime
import logging
from enum import Enum

from django.db import connection

logger = logging.getLogger('ikyo')


def toSqlField(s) -> str:
    if isinstance(s, Enum):
        return __toSqlField(s.value)
    return __toSqlField(s)


def __toSqlField(s) -> str:
    if s is None:
        return 'NULL'
    elif type(s) == float or type(s) == int:
        return str(s)
    elif type(s) == datetime.datetime:
        return "'" + s.strftime('%Y-%m-%d %H:%M:%S') + "'"
    elif type(s) == datetime.date:
        return "'" + s.strftime('%Y-%m-%d') + "'"
    elif type(s) == datetime.time:
        return "'" + s.strftime('%H:%M:%S') + "'"
    else:
        s2 = str(s)
        return "'" + s2.replace("'", "''") + "'"


def isEmpty(rs) -> bool:
    return rs is None or len(rs) == 0


def dictfetchall(cursor) -> list:
    '''
        Return all rows from a cursor as a dict
    '''
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def getFieldValues(records, fields) -> list:
    '''
        return [[field1, field2...], [field1, field2...]...]
    '''
    rs = []
    for r in records:
        data = []
        for f in fields:
            data.append(r.get(f, None))
        rs.append(data)
    return rs


def getNextSequence(sequenceName, engine=None) -> int:
    if engine and engine == 'sqlite3':
        with connection.cursor() as cursor:
            cursor.execute("SELECT (seq + 1) AS seq FROM sqlite_sequence WHERE name=" + toSqlField(sequenceName))
            rs = dictfetchall(cursor)
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval(" + toSqlField(sequenceName) + ") as seq")
            rs = dictfetchall(cursor)
    return None if isEmpty(rs) else rs[0]['seq']
