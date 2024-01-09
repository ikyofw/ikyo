import core.models as ikModels
from core.session.user import UserManager
from core.utils.langUtils import isNotNullBlank

from .menuManager import MenuManager


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


class MenuBar:

    def __init__(self, selectedMenuId=None):
        self.menus = []
        self.selectedMenuId = selectedMenuId

    def addMenu(self, menu):
        if isNotNullBlank(menu):
            if isinstance(menu, Menu):
                self.menus.append(menu)
            elif type(menu) == list:
                self.menus.extend(menu)
        return self

    def toJson(self) -> dict:
        j = {}
        j['menus'] = []
        if isNotNullBlank(self.menus) and len(self.menus) > 0:
            for m in self.menus:
                j['menus'].append(m.toJson())
        return j


def getUserMenus(request) -> list:
    usrId = request.user.id
    menus = []
    if UserManager.HasLogin(request):
        showSubMenus = False
        currentTopMenu = None
        currentPath = request.GET.get('currentPath', None)
        if isNotNullBlank(currentPath):
            currentPath = currentPath[1:]
            currentMenu = ikModels.Menu.objects.filter(menu_nm__iexact=currentPath).first()
            if isNotNullBlank(currentMenu):
                currentTopMenu = MenuManager.getTopMenu(currentMenu)
                if isNotNullBlank(currentMenu.sub_menu_lct):
                    showSubMenus = True

        # add top menu
        usrTopMenus = MenuManager.getUserAclMenus(usrId)
        for menu in usrTopMenus:  # top menu
            subdirectoryNum = ikModels.Menu.objects.filter(parent_menu_id=menu.id).count()
            if subdirectoryNum > 0:
                action = "menu"
            else:
                action = menu.screen_nm

            topMenu = Menu(menu.id, menu.menu_nm, menu.menu_caption, action)
            menus.append(topMenu)

            # add subMenus if need
            if isNotNullBlank(currentTopMenu) and currentTopMenu.id == menu.id:
                topMenu.isCurrentMenu = True
                if showSubMenus:
                    submenusParentMenuID = MenuManager.getParentMenuIdByMenuNm(currentMenu.menu_nm)
                    subMenus = MenuManager.getUserAclMenus(usrId, submenusParentMenuID)
                    for subMenu in subMenus:
                        if str(subMenu.parent_menu_id) == str(submenusParentMenuID):
                            screenName = subMenu.screen_nm
                            menuAction = screenName.lower() if screenName is not None else ''
                            if currentMenu.id == subMenu.id:
                                topMenu.addSubMenu(Menu(subMenu.id, subMenu.menu_nm, subMenu.menu_caption, menuAction, isCurrentMenu=True))
                            else:
                                topMenu.addSubMenu(Menu(subMenu.id, subMenu.menu_nm, subMenu.menu_caption, menuAction))
        # YL.ikyo, 2022-06-30 - end
        menus.append(Menu(-1, 'Logout', 'Logout', 'logout'))  # YL.ikyo, 2022-04-24 CHANG for logout
    else:
        menus.append(Menu(-2, 'Login', 'Login', 'login'))
    return menus
