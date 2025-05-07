import logging
import traceback

from django.http import HttpResponse

import core.utils.djangoUtils as ikDjangoUtils
from core.auth.index import hasLogin
from core.core.http import *
from core.db.transaction import IkTransaction
from core.inbox import InboxView
from core.init import initIk
from core.menu import views as MenuView
from core.menu.menuManager import MenuManager
from core.models import Currency as CurrencyModel
from core.models import Office as OfficeModel
from core.screen import AppMntView, ScreenDfnView, TypeWidgetMntView
from core.user import UsrGrpMntView, UsrMntView
from core.utils.langUtils import isNullBlank
from core.view.screenView import ScreenAPIView

logger = logging.getLogger('ikyo')


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


class AppMnt(AppMntView.AppMntView):
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


class Inbox(InboxView.InboxView):
    def __init__(self) -> None:
        super().__init__()


class MenuMnt(MenuView.MenuMnt):
    def __init__(self) -> None:
        super().__init__()


class Office(ScreenAPIView):
    """ Office
    """

    def getCcyRcs(self):
        data = [
            {"id": ccy.id, "code": f'{ccy.code} - {ccy.name}'}
            for ccy in CurrencyModel.objects.all().order_by('seq')
        ]
        return IkSccJsonResponse(data=data)

    def save(self):
        officeTable = self.getRequestData().get("officeTable", None)
        if isNullBlank(officeTable):
            return IkSysErrJsonResponse()
        try:
            pytrn = IkTransaction(userID=self.getCurrentUserId())
            pytrn.add(officeTable)
            b = pytrn.save()
            if not b.value:
                return IkErrJsonResponse(message=b.dataStr)
            return IkSccJsonResponse(message="Saved.")
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))


class Currency(ScreenAPIView):
    """ Currency
    """

    def save(self):
        ccyTable = self.getRequestData().get("ccyTable", None)
        if isNullBlank(ccyTable):
            return IkSysErrJsonResponse()

        ccyTable.sort(key=lambda o: o.seq)
        seq = 0
        for r in ccyTable:
            if r.ik_is_status_delete():
                continue
            seq += 1
            if seq != r.seq:
                r.seq = seq
                if not r.ik_is_status_new():
                    r.ik_set_status_modified()

        try:
            pytrn = IkTransaction(userID=self.getCurrentUserId())
            pytrn.add(ccyTable)
            b = pytrn.save()
            if not b.value:
                return IkErrJsonResponse(message=b.dataStr)
            return IkSccJsonResponse(message="Saved.")
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))
