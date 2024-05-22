import core.ui.ui as ikui
import core.menu.menu as coreMenu
import core.models as ikModels
from core.core.http import IkSccJsonResponse
from core.menu.menuManager import MenuManager
from core.sys.accessLog import getAccessLog, getLatestAccessLog
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.view.authView import AuthAPIView
from core.view.screenView import ScreenAPIView


class MenuBarView(AuthAPIView):

    def get(self, request, *args, **kwargs):
        menus = coreMenu.getUserMenus(request)
        data = []
        for menu in menus:
            data.append(menu.toJson())
        return IkSccJsonResponse(data=data)

    def toJson(self, menus) -> dict:
        j = []
        if menus is not None and len(menus) > 0:
            for m in menus:
                j.append(m.toJson())
        return j


class Menu(ScreenAPIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def beforeInitScreenData(self, screen: ikui.Screen):
        super().beforeInitScreenData(screen)
        
        menuID1 = self.getSessionParameter('menuID1')
        activeRow1 = self.getSessionParameter('activeRow1')
        activeRow2 = self.getSessionParameter('activeRow2')

        if isNotNullBlank(menuID1):
            screen.setFieldGroupCaption(fieldGroupName='MenuFg_level_1', value=MenuManager.getMenuCaption(menuID1))
        if isNotNullBlank(activeRow1):
            screen.setFieldGroupCaption(fieldGroupName='MenuFg_level_2', value=MenuManager.getMenuCaption(activeRow1))
        if isNotNullBlank(activeRow2):
            screen.setFieldGroupCaption(fieldGroupName='MenuFg_level_3', value=MenuManager.getMenuCaption(activeRow2))

    # override
    def getMenuName(self) -> str:
        """Override.
        Returns:
            menu name (str): Menu page's menu name.
        """
        return 'menu'

    def getScreen(self) -> dict:
        menuID1 = self.request.GET.get('last', None)
        if menuID1:
            preMenuID1 = self.getSessionParameter('menuID1')
            if preMenuID1 != menuID1:
                self.setSessionParameters({'menuID1': menuID1})
                self.deleteSessionParameters(nameFilters=['activeRow1', 'activeRow2'])
        return super().getScreen()

    def getMenu1(self):
        menuID1 = self.getSessionParameter('menuID1')
        activeRow1 = self.getSessionParameter('activeRow1')
        data = self.getSubdir(menuID1, activeRow1)
        return IkSccJsonResponse(data=data)

    def getNextMenu1(self):
        activeRow1 = self.getRequestData().get('activeRow')
        self.setSessionParameters({'activeRow1': str(activeRow1) if activeRow1 else ''})
        self.deleteSessionParameters(nameFilters=['activeRow2'])
        return IkSccJsonResponse()

    def getMenu2(self):
        activeRow1 = self.getSessionParameter('activeRow1')
        activeRow2 = self.getSessionParameter('activeRow2')
        data = self.getSubdir(activeRow1, activeRow2)
        return IkSccJsonResponse(data=data)

    def getNextMenu2(self):
        activeRow2 = self.getRequestData().get('activeRow')
        self.setSessionParameters({'activeRow2': str(activeRow2) if activeRow2 else ''})
        return IkSccJsonResponse()

    def getMenu3(self):
        activeRow2 = self.getSessionParameter('activeRow2')
        data = self.getSubdir(activeRow2)
        return IkSccJsonResponse(data=data)

    # Find subdirectories of this directory by menu ID
    def getSubdir(self, menuID, activeRow=None):
        usrID = self.getCurrentUserId()
        data = []
        if not isNullBlank(menuID):
            # YL.ikyo, 2023-02-10 CHANGE bugfix - just list user have permission menus - start
            usrAclMenuIDs = []
            usrAclMenuQs = MenuManager.getUserAclMenus(usrID, int(menuID))
            usrAclMenuIDs = [i.id for i in usrAclMenuQs if i.id]

            subMenuQs = ikModels.Menu.objects.filter(parent_menu_id=int(menuID)).order_by("order_no")
            for m in subMenuQs:
                subdirNum = len(ikModels.Menu.objects.filter(parent_menu_id=m.id))
                aclSubdirNum = len(ikModels.Menu.objects.filter(parent_menu_id=m.id, id__in=usrAclMenuIDs))
                if m.id in usrAclMenuIDs and (subdirNum == 0 or aclSubdirNum > 0):
                    action = None
                    rowStatus = 0
                    if subdirNum == 0:
                        if coreMenu.MENU_FILTERS:
                            action = coreMenu.MENU_FILTERS.get("actionFilter")(usrID, m)  # wci
                        else:
                            action = m.screen_nm
                    elif self.__showSubMenusInMenuBar(m.id):
                        subMenuIDList = [str(i.id) for i in MenuManager.getAllSubMenus(m.id) if i.id in usrAclMenuIDs]
                        subMenuIDstr = ", ".join(subMenuIDList)
                        latestAccessMenu = getLatestAccessLog(usrID, subMenuIDstr)
                        if len(latestAccessMenu) == 0:
                            action = MenuManager.getFirstValidSubMenu(usrID, m.id)
                        else:
                            action = latestAccessMenu[0]['screen_nm']
                    else:
                        rowStatus = 1
                        if str(activeRow) == str(m.id):
                            rowStatus = 2
                    data.append({'id': m.id, 'menu_caption': m.menu_caption, 'screen_nm': action, "rowStatus": rowStatus})
            # YL.ikyo, 2023-02-10 - end
        return data

    def getBackMenus(self):
        return getAccessLog(self.getCurrentUserId())

    def __showSubMenusInMenuBar(self, menuID) -> bool:
        menuRcs = ikModels.Menu.objects.filter(parent_menu_id=menuID)
        for i in menuRcs:
            if isNotNullBlank(i.sub_menu_lct):
                return True
        return False
