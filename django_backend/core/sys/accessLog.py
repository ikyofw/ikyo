import logging
from datetime import datetime

import core.utils.db as dbUtils
from core.auth.index import getRequestToken, getSessionID, getUser
from core.core.http import getClientIP, isSupportSession
from core.db.transaction import IkTransaction
from core.models import AccessLog, Menu
from django.db import connection
from django.db.models import Q

logger = logging.getLogger('ikyo')


def addAccessLog(request, menuID, pageName, actionName=None, remarks=None):
    '''
        add access log (ik_access_log)
    '''
    try:
        urlReferer = request.META.get('HTTP_REFERER', '')  # urlReferer = request.META['HTTP_REFERER']
        if urlReferer != '' and urlReferer is not None:
            remarks = ('' if remarks is None else ('%s ' % remarks)) + 'HttpReferer=%s' % urlReferer
        url = request.META['wsgi.url_scheme'] + '://' + request.META['HTTP_HOST'] + request.get_full_path()
        userID = None
        try:
            user = getUser(request)
            if user is not None:
                userID = user.id
        except:
            pass

        sessionID = None
        if isSupportSession(request):
            sessionID = getSessionID(request)
        else:
            sessionID = getRequestToken(request)
            if sessionID is not None:
                sessionID = 'token=%s' % sessionID
        rc = AccessLog()
        rc.cre_dt = datetime.now()
        rc.session_id = sessionID
        rc.request_url = url
        rc.ip = getClientIP(request=request)
        rc.usr_id = userID
        rc.menu_id = menuID
        rc.page_nm = pageName
        rc.action_nm = actionName
        rc.rmk = remarks

        ptrn = IkTransaction()
        ptrn.add(rc)
        b = ptrn.save()
        if not b.value:
            logger.error('Save access log failed: url=%s, userID=%s, error=%s' % (url, userID, b.dataStr))
    except Exception as e:
        logger.error(e, exc_info=True)


def getAccessLog(userID):
    sql = "SELECT a.menu_id, a.menu_caption, a.screen_nm FROM ("
    sql += " SELECT l.menu_id, m.menu_caption, m.screen_nm, max(l.id) AS id FROM ik_access_log l LEFT JOIN ik_menu m ON m.id=l.menu_id WHERE usr_id=%s" % dbUtils.toSqlField(
        userID)
    # sql += " AND l.cre_dt>=%s" % dbUtils.toSqlField(startDt)
    sql += " AND l.menu_id IS NOT NULL AND l.menu_id NOT IN (%s)" % __getExcludedMenus()
    sql += " AND m.screen_nm IS NOT NULL AND m.parent_menu_id IS NOT NULL GROUP BY l.menu_id, m.menu_caption, m.screen_nm"
    sql += " ) a"
    sql += " LEFT JOIN ik_access_log log ON a.id=log.id"
    sql += " ORDER BY a.id DESC LIMIT 10 OFFSET 1"

    data = []
    with connection.cursor() as cursor:
        cursor.execute(sql)
        data = dbUtils.dictfetchall(cursor)
    return data


def getLatestAccessLog(userID, menuIDs: str):
    sql = "SELECT a.screen_nm FROM ("
    sql += " SELECT l.menu_id, m.menu_caption, m.screen_nm, max(l.id) AS id FROM ik_access_log l LEFT JOIN ik_menu m ON m.id=l.menu_id WHERE usr_id=%s" % dbUtils.toSqlField(
        userID)
    sql += " AND l.menu_id IS NOT NULL AND l.menu_id NOT IN (%s) AND l.menu_id IN (%s)" % (__getExcludedMenus(), menuIDs)
    sql += " AND m.screen_nm IS NOT NULL AND m.parent_menu_id IS NOT NULL GROUP BY l.menu_id, m.menu_caption, m.screen_nm"
    sql += " ) a"
    sql += " LEFT JOIN ik_access_log log ON a.id=log.id"
    sql += " ORDER BY a.id DESC LIMIT 1"

    data = []
    with connection.cursor() as cursor:
        cursor.execute(sql)
        data = dbUtils.dictfetchall(cursor)
    return data


def __getExcludedMenus():
    querySet = Menu.objects.filter(Q(menu_nm__icontains='HOME') | Q(menu_nm__iexact='MENU') | Q(menu_nm__icontains='IB000'))
    data = []
    for i in querySet:
        data.append(str(i.id))
    return ", ".join(data)
