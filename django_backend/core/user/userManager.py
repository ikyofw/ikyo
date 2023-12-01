'''
    User Manager
'''
import inspect

from django.core.handlers.wsgi import WSGIHandler
from django.db import connection

import core.utils.db as dbUtils
from core.core.exception import IkException
from core.core.mailer import EmailAddress
from core.models import User
from core.utils import strUtils
from core.view.authView import getCurrentView
from iktools import IkConfig

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
        cursor.execute("SELECT enable FROM ik_usr WHERE id=" + str(userID))
        rs = dbUtils.dictfetchall(cursor)
        if not dbUtils.isEmpty(rs):
            return "Y" == rs[0]['enable']
        else:
            raise IkException("User does not exist: id=" + str(userID))


def getUserDisplayName(userID) -> str:
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("select * from iky_get_usr_full_nm(" + str(userID) + ") AS usr_nm")
        rs = dbUtils.dictfetchall(cursor)
        return None if dbUtils.isEmpty(rs) else rs[0]['usr_nm']


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


def getLastCoDt(userID) -> str:
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT last_co_dt FROM ik_usr WHERE id=" + str(userID))
        rs = dbUtils.dictfetchall(cursor)
        if not dbUtils.isEmpty(rs):
            return rs[0]['last_co_dt']
    return None


def getIkyUserByDbField(userID, dbField):
    '''ikyUsr'''
    rs = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT %s FROM ik_usr WHERE id=%s" % (dbField, userID))
        rs = dbUtils.dictfetchall(cursor)
    return None if dbUtils.isEmpty(rs) else rs[0][dbField]


def getUserFavoriteProjectID(userID) -> int:
    return getUserInfo(userID, 'favorite_prj_id')


def updateUserFavoriteProjectID(userID, projectID) -> None:
    updateUserInfo(userID, "favorite_prj_id", projectID, userID)


# YL.ikyo, 2022-11-01
def getUserDefaultOffice(usrId) -> str | None:
    with connection.cursor() as cursor:
        cursor.execute('SELECT office FROM ik_usr WHERE id=%s' % usrId)
        rs = dbUtils.dictfetchall(cursor)
    return None if dbUtils.isEmpty(rs) else rs[0]['office']


def getCurrentUser() -> User:
    '''
        get current user
    '''
    try:
        return getCurrentView().getCurrentUser()
    except IkException as e:
        return None
