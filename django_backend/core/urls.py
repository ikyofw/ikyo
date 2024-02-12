import logging, sys
from django.db import connection
from django.urls import URLPattern, path, re_path

import core.utils.db as dbUtils
import core.utils.modelUtils as modelUtils
import core.utils.djangoUtils as ikDjangoUtils
from core.auth.index import AuthView
from core.menu.views import Menu, MenuBarView
from core.utils.langUtils import isNullBlank
from core import views
from core.help import ScreenHelpView

logger = logging.getLogger('ikyo')

API_URLS = []


def apiUrl(url) -> str:
    url = 'api/%s' % ('' if url is None else url)
    if url in API_URLS:
        return url
    API_URLS.append(url)
    return url


def apiScreenUrl(apiViewClass, url: str = None) -> URLPattern:
    if ikDjangoUtils.isRunDjangoServer():
        url2 = apiViewClass().getViewUrl() if url is None else url
        url2 = apiUrl(url2 + '/<str:action>')
        return path(url2, apiViewClass.as_view())
    else:
        return views.index


urlpatterns = [
    re_path(apiUrl('auth$'), AuthView.as_view()),

    path(apiUrl('help/screen/<str:viewID>'), ScreenHelpView.as_view()),

    re_path(apiUrl('menubar/getMenubar$'), MenuBarView.as_view()),
    path(apiUrl('menu/<str:action>'), Menu.as_view()),

    re_path(apiUrl('getRouters$'), views.getRouters),
]


def getScreenUrlFromDatabase() -> list[URLPattern]:
    screens = None
    with connection.cursor() as cursor:
        sql = 'SELECT DISTINCT a.screen_sn,a.screen_title,a.class_nm,a.api_url '
        sql += 'FROM ik_screen a '
        sql += 'INNER JOIN (select screen_sn,max(rev) max_rev from ik_screen group by screen_sn) b ON a.screen_sn=b.screen_sn and a.rev=b.max_rev '
        sql += 'WHERE a.class_nm IS NOT NULL '
        sql += 'ORDER BY a.screen_sn'
        cursor.execute(sql)
        screens = dbUtils.dictfetchall(cursor)

    urlpatterns = []
    if screens is not None:
        for screen in screens:
            screenSN = screen.get('screen_sn', None)
            screenTitle = screen.get('screen_title', None)
            screenClassName = screen.get('class_nm', None)
            apiUrl = screen.get('api_url', None)
            try:
                viewClass = modelUtils.getModelClass(screenClassName)
                url = apiScreenUrl(viewClass, None if isNullBlank(apiUrl) else apiUrl.lower())
                urlpatterns.append(url)
                # logger.info('Auto add URL from DB: [%s]' % url)
            except Exception as e:
                logger.error('Auto add URL from DB failed: Url=[%s], screen=[%s], title=[%s], classs=[%s], error: %s' % (
                    apiUrl, screenSN, screenTitle, screenClassName, str(e)))
                # logger.error(e,exc_info=True)
    return urlpatterns

if ikDjangoUtils.isRunDjangoServer():
    urlpatterns.extend(getScreenUrlFromDatabase())
