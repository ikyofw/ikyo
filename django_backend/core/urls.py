import logging

from django.db import connection
from django.urls import URLPattern, path, re_path

import core.utils.db as dbUtils
import core.utils.django_utils as ikDjangoUtils
import core.utils.model_utils as model_utils
from core import views
from core.auth.index import AuthView
from core.help import ScreenHelpView
from core.menu.menu_view import Menu, MenuBarView
from core.utils.lang_utils import isNullBlank

logger = logging.getLogger('ikyo')

API_URLS = []
CLASS_GET_VIEW_URL_METHOD_NAME = 'getViewUrl'
API_SCREEN_URLS = []


def apiUrl(url) -> str:
    url = 'api/%s' % ('' if url is None else url)
    if url in API_URLS:
        return url
    API_URLS.append(url)
    return url


def apiScreenUrl(apiViewClass, url: str = None) -> URLPattern:
    if ikDjangoUtils.isRunDjangoServer():
        url2 = url
        if url2 is None:
            if hasattr(apiViewClass, CLASS_GET_VIEW_URL_METHOD_NAME):
                url2 = getattr(apiViewClass, CLASS_GET_VIEW_URL_METHOD_NAME)()
            if isNullBlank(url2):
                url2 = apiViewClass.__name__.lower()
        if url2.lower() in API_SCREEN_URLS:
            logger.warning('Duplicate screen api: %s (%s.%s)' % (url2, apiViewClass.__module__, apiViewClass.__qualname__))
        API_SCREEN_URLS.append(url2.lower())
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
        sql = 'SELECT DISTINCT a.screen_sn,a.screen_title,a.app_nm,a.class_nm,a.api_url '
        sql += 'FROM ik_screen a '
        sql += 'INNER JOIN (select screen_sn,max(rev) max_rev from ik_screen group by screen_sn) b ON a.screen_sn=b.screen_sn and a.rev=b.max_rev '
        sql += 'WHERE a.app_nm IS NOT NULL '
        sql += 'ORDER BY a.screen_sn'
        cursor.execute(sql)
        screens = dbUtils.dictfetchall(cursor)

    urlpatterns = []
    if screens is not None:
        for screen in screens:
            screen_sn = screen.get('screen_sn', None)
            screen_title = screen.get('screen_title', None)
            screen_app_name = screen.get('app_nm', None)
            screen_class_nm = screen.get('class_nm', None)
            api_url = screen.get('api_url', None)

            view_class = model_utils.get_model_class_2(screen_app_name, screen_sn, screen_class_nm)
            if view_class is not None:
                url = apiScreenUrl(view_class, None if isNullBlank(api_url) else api_url.lower())
                urlpatterns.append(url)
                logger.debug('Auto add URL from DB: [%s]' % url)
            else:
                logger.error('Auto add URL from DB failed: url=[%s], screen=[%s], title=[%s], app=[%s].' % (
                    api_url, screen_sn, screen_title, screen_app_name))
    return urlpatterns


if ikDjangoUtils.isRunDjangoServer():
    urlpatterns.extend(getScreenUrlFromDatabase())
