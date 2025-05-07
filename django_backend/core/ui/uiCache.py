from core.utils.langUtils import isNullBlank
from core.core.exception import IkValidateException
from django.core.cache import cache

from core.models import ScreenFgType, ScreenFieldWidget


def clearAllCache():
    cache.clear()


def setPageDefinitionCache(screenSN, screenDfn):
    if isNullBlank(screenSN) or isNullBlank(screenDfn):
        return None
    cache.set(screenSN, screenDfn)


def getPageDefinitionFromCache(screenSN):
    if isNullBlank(screenSN):
        return None
    screenDfn = cache.get(screenSN)
    return screenDfn


def deletePageDefinitionFromCache(screenSN):
    if isNullBlank(screenSN):
        return None
    cache.delete(screenSN)


def setFieldGroupTypeCache():
    fgTypes = list(ScreenFgType.objects.values_list('type_nm', flat=True))
    cache.set('fgTypes', fgTypes)
    return fgTypes


def isFieldGroupTypeExist(typeName):
    fgTypes = cache.get('fgTypes')
    if isNullBlank(fgTypes):
        fgTypes = setFieldGroupTypeCache()
    if typeName in fgTypes:
        return typeName
    raise IkValidateException('Unsupported screen field group type: %s' % typeName)


def setFieldWidgetCache():
    fieldWidgets = list(ScreenFieldWidget.objects.values_list('widget_nm', flat=True))
    cache.set('fieldWidgets', fieldWidgets)
    return fieldWidgets


def isFieldWidgetExist(widgetName):
    fieldWidgets = cache.get('fieldWidgets')
    if isNullBlank(fieldWidgets):
        fieldWidgets = setFieldWidgetCache()
    if widgetName in fieldWidgets:
        return widgetName
    raise IkValidateException('Unsupported screen field widget: %s' % widgetName)