from django.http import HttpResponse
from core.auth.index import hasLogin
from core.core.http import IkSccJsonResponse
from core.init import initIk
from core.menu.menuManager import MenuManager
import core.utils.djangoUtils as ikDjangoUtils

from core.screen import ScreenDfnView, TypeWidgetMntView
from core.user import UsrGrpMntView, UsrMntView

def index(request):
    '''
        Used for 
    '''
    return HttpResponse("Hello, Ikyo World!")

ROUTER_EXCLUDE_SCREENS = [
    'menu',
]

def getRouters(request):
    screenIDs, screenUrls = [], []
    if hasLogin(request):
        excludeScreens = [s.lower() for s in ROUTER_EXCLUDE_SCREENS]
        screenNames = MenuManager.getIkScreens()
        for screenName in screenNames:
            if screenName.lower() not in excludeScreens:
                sn = screenName.lower()
                screenIDs.append(sn)
                screenUrls.append(sn)
    return IkSccJsonResponse(data={"screenIDs": screenIDs, "paths": screenUrls})

# ------------------------------------------------------------------------------
# initializing the all services
# ------------------------------------------------------------------------------
if ikDjangoUtils.isRunDjangoServer():
    initIk()


class ScreenDfn(ScreenDfnView.ScreenDfnView):
    def __init__(self) -> None:
        super().__init__()

class TypeWidgetMnt(TypeWidgetMntView.TypeWidgetMntView):
    def __init__(self) -> None:
        super().__init__()

class UsrGrpMnt(UsrGrpMntView.UsrGrpMntView):
    def __init__(self) -> None:
        super().__init__()

class UsrMnt(UsrMntView.UsrMntView):
    def __init__(self) -> None:
        super().__init__()