from django.db.models import QuerySet

import core.models as ikModels
from core.menu.menuManager import MenuManager
from core.session.user import UserManager
from core.sys.accessLog import getLatestAccessLog
from core.utils.langUtils import isNotNullBlank, isNullBlank


class Menu:

    def __init__(self, id, name, title, action=None, subMenus=[], isCurrentMenu=None):
        self.id = id
        self.name = name
        self.title = title
        self.action = action if isNotNullBlank(action) else name
        self.subMenus = []
        self.isCurrentMenu = isCurrentMenu
        if isNotNullBlank(subMenus) and len(subMenus) > 0:
            self.subMenus.extend(subMenus)

    def addSubMenu(self, subMenu):
        if isNotNullBlank(subMenu):
            if isinstance(subMenu, Menu):
                self.subMenus.append(subMenu)
            elif type(subMenu) == list:
                self.subMenus.extend(subMenu)
        return self

    def toJson(self):
        j = {'id': self.id, 'title': self.title, 'action': '' if self.action is None else self.action}
        if isNotNullBlank(self.subMenus) and len(self.subMenus) > 0:
            j['subMenus'] = []
            for m in self.subMenus:
                j['subMenus'].append(m.toJson())
        if isNotNullBlank(self.isCurrentMenu):
            j['isCurrentMenu'] = self.isCurrentMenu
        return j

    def __str__(self):
        return self.title


MENU_FILTERS = None
'''
Global menu filter function: <br />
Invoke:
    {"actionFilter" : getMenuActionFilter, "menuFilter": getPyiMenuFilter}
    
    getMenuActionFilter(userID, ikModels.Menu) -> str
    getPyiMenuFilter (screenNm) -> ikModels.Menu
'''


def getUserMenus(request) -> list:
    usrID = request.user.id
    menus = []
    if UserManager.HasLogin(request):
        showSubMenus = False
        currentTopMenu = None
        currentPath = request.GET.get('currentPath', None)
        if isNotNullBlank(currentPath):
            currentPath = currentPath[1:]
            currentMenu = ikModels.Menu.objects.filter(screen_nm__iexact=currentPath).order_by('-id').first()
            if isNotNullBlank(currentMenu):
                currentTopMenu = MenuManager.getTopMenu(currentMenu)
                if isNotNullBlank(currentMenu.sub_menu_lct):
                    showSubMenus = True

        # add top menu
        usrTopMenus = MenuManager.getUserAclMenus(usrID)
        for menu in usrTopMenus:  # top menu
            subdirectoryRcs = ikModels.Menu.objects.filter(parent_menu_id=menu.id)
            showSubMenusInMenuBar = True
            for i in subdirectoryRcs:
                if isNullBlank(i.sub_menu_lct):
                    showSubMenusInMenuBar = False
                    continue
            action = None
            if len(subdirectoryRcs) > 0:
                if showSubMenusInMenuBar:
                    action = MenuManager.getFirstValidSubMenu(usrID, menu.id)
                else:
                    action = "menu"
            else:
                # for open wci1
                if MENU_FILTERS:
                    action = MENU_FILTERS.get("actionFilter")(usrID, menu)
                if not action:
                    action = menu.screen_nm

            topMenu = Menu(menu.id, menu.menu_nm, menu.menu_caption, action)
            menus.append(topMenu)

            # add subMenus if need
            if isNotNullBlank(currentTopMenu) and currentTopMenu.id == menu.id:
                topMenu.isCurrentMenu = True
                if showSubMenus:
                    parentMenuRc1 = MenuManager.getParentMenuByMenuNm(currentMenu.menu_nm)
                    subMenus1 = MenuManager.getUserMenus(usrID, int(parentMenuRc1.id))
                    if isNotNullBlank(parentMenuRc1.sub_menu_lct):
                        parentMenuRc2 = MenuManager.getParentMenuByMenuId(parentMenuRc1.id)
                        subMenus2 = MenuManager.getUserMenus(usrID, int(parentMenuRc2.id))
                        topMenu = __addSubMenu(usrID, topMenu, subMenus2, parentMenuRc1)
                    else:
                        topMenu = __addSubMenu(usrID, topMenu, subMenus1, currentMenu)

                    for secondaryMenu in topMenu.subMenus:
                        subMenus = MenuManager.getUserMenus(usrID, secondaryMenu.id)
                        secondaryMenu = __addSubMenu(usrID, secondaryMenu, subMenus, currentMenu)
        # YL.ikyo, 2022-06-30 - end
        menus.append(Menu(-1, 'Logout', 'Logout', 'logout'))  # YL.ikyo, 2022-04-24 CHANG for logout
    else:
        menus.append(Menu(-2, 'Login', 'Login', 'login'))
    return menus


def __addSubMenu(usrID: int, parentMenu: Menu, subMenus: QuerySet[ikModels.Menu], currentMenu: ikModels.Menu) -> Menu:
    for subMenu in subMenus:
        menuAction = ''
        if isNullBlank(subMenu.screen_nm):
            subMenusRcs = MenuManager.getUserMenus(usrID, subMenu.id)
            subMenuIDList = [str(i.id) for i in subMenusRcs]
            subMenuIDstr = ", ".join(subMenuIDList)
            latestAccessMenu = getLatestAccessLog(usrID, subMenuIDstr)
            if len(latestAccessMenu) == 0:
                menuAction = MenuManager.getFirstValidSubMenu(usrID, subMenu.id)
            else:
                menuAction = latestAccessMenu[0]['screen_nm']
        else:
            menuAction = subMenu.screen_nm.lower()

        if currentMenu.id == subMenu.id:
            parentMenu.addSubMenu(Menu(subMenu.id, subMenu.menu_nm, subMenu.menu_caption, menuAction, isCurrentMenu=True))
        else:
            parentMenu.addSubMenu(Menu(subMenu.id, subMenu.menu_nm, subMenu.menu_caption, menuAction))
    return parentMenu
