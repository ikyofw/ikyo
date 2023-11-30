from core.utils.langUtils import isNullBlank
from django.core.cache import cache


def clearAllCache():
    cache.clear()


def updatePageDefinitionCache(screenSN, screenDfn):
    if isNullBlank(screenSN) or isNullBlank(screenDfn):
        return None
    cache.set(screenSN, screenDfn)


def getPageDefinitionFromCache(screenSN):
    if isNullBlank(screenSN):
        return None
    screenDfn = cache.get(screenSN)
    return screenDfn
