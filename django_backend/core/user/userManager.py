'''
    User Manager
'''
from django.db import connection

import core.utils.db as dbUtils
from core.core.exception import IkException
from core.core.mailer import EmailAddress
from core.models import User
from core.view.authView import getCurrentView

ADMINISTRATOR_USER_ID = -2
'''
    -2
'''

SYSTEM_USER_ID = -1
'''
    -1
'''


def getSystemID() -> int:
    return SYSTEM_USER_ID


def getUser(userID: int) -> User:
    return User.objects.filter(id=userID).first()


def getUserName(userID) -> str:
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT usr_nm FROM ik_usr WHERE id=%s" % (userID))
        rs = dbUtils.dictfetchall(cursor)
    return None if dbUtils.isEmpty(rs) else rs[0]['usr_nm']


def getUserID(userNm) -> int:
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM ik_usr WHERE usr_nm=%s" % (dbUtils.toSqlField(userNm)))
        rs = dbUtils.dictfetchall(cursor)
    return None if dbUtils.isEmpty(rs) else rs[0]['id']


def isEnable(userID) -> bool:
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT active FROM ik_usr WHERE id=" + str(userID))
        rs = dbUtils.dictfetchall(cursor)
        if not dbUtils.isEmpty(rs):
            return rs[0]['active']
        else:
            raise IkException("User does not exist: id=" + str(userID))


def getUserEmailAddress(userID) -> EmailAddress | None:
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT usr_nm, email FROM ik_usr WHERE id=" + str(userID))
        rs = dbUtils.dictfetchall(cursor)
        return None if dbUtils.isEmpty(rs) else EmailAddress(rs[0]['email'], rs[0]['usr_nm'])


def getUserEmailAddresses(userIDs) -> list:
    '''
    '''
    if userIDs is None or len(userIDs) == 0:
        return []
    sql = 'SELECT usr_nm, email FROM ik_usr WHERE id'
    if len(userIDs) == 1:
        sql += '=%s' % userIDs[0]
    else:
        sql += ' IN(%s)' % ','.join(str(i) for i in userIDs)

    emails = []
    with connection.cursor() as cursor:
        cursor.execute(sql)
        rs = dbUtils.dictfetchall(cursor)
        if not dbUtils.isEmpty(rs):
            for r in rs:
                emails.append(EmailAddress(r['email'], r['usr_nm']))
    return emails


def getCurrentUser() -> User:
    '''
        get current user
    '''
    try:
        return getCurrentView().getCurrentUser()
    except IkException as e:
        return None
