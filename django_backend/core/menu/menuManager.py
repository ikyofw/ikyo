import logging

from django.db import connection
from django.db.models import Q

import core.models as ikModels
import core.utils.db as dbUtils
from core.core.exception import IkValidateException
from core.ui.ui import IkUI, Screen

logger = logging.getLogger('backend')
'''
    ik_menu.app = 'backend'
'''
MENU_APP_IK = 'backend'

ACL_READ = 'R'
ACL_WRITE = 'W'
ACL_DENY = 'D'


class __MenuManager():

    def __init__(self) -> None:
        pass

    def getUserMenus(self, usrID, parentMenu=None):
        parentMenuID = None
        if parentMenu is not None:
            if type(parentMenu) == int:
                parentMenuID = parentMenu
            else:  # menu Name
                parentMenuID = self.getMenuId(parentMenu)

        usr_groups_ids = []
        menu_ids = []
        if usrID is not None:
            usr_groups_ids = ikModels.UserGroup.objects.filter(usr_id=usrID).values_list('grp_id', flat=True)
            menu_ids = ikModels.GroupMenu.objects.filter(grp__in=menu_ids).values_list('menu_id', flat=True)

        usrAclMenusQs = ikModels.Menu.objects.filter(Q(is_free_access=True) | Q(
            id__in=menu_ids)).exclude(menu_nm='Menu').order_by('order_no', 'caption')
        if parentMenuID is not None:
            usrAclMenusQs = usrAclMenusQs.filter(parent_menu_id=parentMenuID)
        return usrAclMenusQs

    def getUserMenuAcl(self, usrID, menuID) -> str:
        menuRc = ikModels.Menu.objects.get(id=menuID)
        if menuRc:
            if menuRc.is_free_access:
                return ACL_WRITE
            groups_ids = ikModels.UserGroup.objects.filter(usr_id=usrID).values_list('grp_id', flat=True)
            acl_permissions = ikModels.GroupMenu.objects.filter(grp__in=groups_ids, menu=menuRc).values_list('acl', flat=True)
            if acl_permissions:
                if ACL_WRITE in acl_permissions:
                    return ACL_WRITE
                if ACL_READ in acl_permissions:
                    return ACL_READ
            return ACL_DENY
        else:
            logger.error("Menu ID[%s] does not exist." % menuID)
            return ACL_DENY

    def getUserMenuByMenuName(self, menuName) -> dict:
        '''
            return None if not found else return ik_menu record
        '''
        menus = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM ik_menu WHERE menu_nm=' + dbUtils.toSqlField(menuName))
            menus = dbUtils.dictfetchall(cursor)
        return menus[0] if not dbUtils.isEmpty(menus) else None

    def getMenuInfoByMenuName(self, menuName) -> dict:
        sql = 'SELECT * FROM ik_menu WHERE menu_nm=' + dbUtils.toSqlField(menuName)
        rs = None
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rs = dbUtils.dictfetchall(cursor)
        return rs[0] if not dbUtils.isEmpty(rs) else None

    def getUserPermission(self, usrId, menuId) -> str:
        return True  # TODO:

    def getMenuId(self, menuName) -> int:
        menuRcs = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT id FROM ik_menu WHERE menu_nm=' + dbUtils.toSqlField(menuName))
            menuRcs = cursor.fetchall()
        if menuRcs is None or len(menuRcs) == 0:
            raise IkValidateException('Menu [%s] is not found.' % str(menuName))
        menuId = menuRcs[0][0]
        return menuId

    def getMenuName(self, menuId) -> str:
        menuRcs = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT menu_nm FROM ik_menu WHERE id=%s' % str(menuId))
            menuRcs = cursor.fetchall()
        if menuRcs is None or len(menuRcs) == 0:
            raise IkValidateException('Menu ID [%s] is not found.' % str(menuId))
        menuName = menuRcs[0][0]
        return menuName

    def getMenuCaption(self, menuId) -> str:
        menuRcs = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT menu_caption FROM ik_menu WHERE id=%s' % str(menuId))
            menuRcs = cursor.fetchall()
        if menuRcs is None or len(menuRcs) == 0:
            raise IkValidateException('Menu ID [%s] is not found.' % str(menuId))
        menuName = menuRcs[0][0]
        return menuName

    def getParentMenuId(self, menuName: str) -> int:
        menuRcs = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT parent_menu_id FROM ik_menu WHERE menu_nm=' + dbUtils.toSqlField(menuName))
            menuRcs = cursor.fetchall()
        if menuRcs is None or len(menuRcs) == 0:
            raise IkValidateException('Menu [%s] is not found.' % str(menuName))
        parentMenuId = menuRcs[0][0]
        return parentMenuId

    def getParentMenuId(self, menuID: int) -> int:
        menuRcs = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT parent_menu_id FROM ik_menu WHERE id=%s' % menuID)
            menuRcs = cursor.fetchall()
        if menuRcs is None or len(menuRcs) == 0:
            raise IkValidateException('Menu ID[%s] is not found.' % str(menuID))
        parentMenuId = menuRcs[0][0]
        return parentMenuId

    # YL.ikyo, 2023-02-10
    # get user all have permission menus (Top & Level1 & Level2 & Level3 menus)
    def getUserAclMenus(self, usrId, parentMenuId=None) -> list:
        usrAclMenuIDs = []
        # 1. get all user have permission menus (remove offline menus,  remove parent menus(will add later if sub menus has permission))
        groups_ids = ikModels.UserGroup.objects.filter(usr_id=usrId).values_list('grp_id', flat=True)
        menu_ids = ikModels.GroupMenu.objects.filter(grp__in=groups_ids).values_list('menu_id', flat=True)
        usrAclMenusQs = ikModels.Menu.objects.filter(Q(is_free_access=True) | Q(id__in=menu_ids)).exclude(menu_nm='Menu').order_by('order_no')
        # If specified Top Menu should just get all Top Menu's sub menu(loop to level3 menus)
        if parentMenuId is not None:
            allSubMenuIDs = []
            sql = "SELECT t.id AS top_menu_id, t.menu_caption AS top_menu_caption,"
            sql += " l1.id AS l1_menu_id, l1.menu_caption AS l1_menu_caption,"
            sql += " l2.id AS l2_menu_id, l2.menu_caption AS l2_menu_caption,"
            sql += " l3.id AS l3_menu_id, l3.menu_caption AS l3_menu_caption"
            sql += " FROM ik_menu t LEFT JOIN ik_menu l1 ON t.id=l1.parent_menu_id"
            sql += " LEFT JOIN ik_menu l2 ON l1.id=l2.parent_menu_id LEFT JOIN ik_menu l3 ON l2.id=l3.parent_menu_id"
            sql += " WHERE t.id=" + str(parentMenuId) + " ORDER BY t.order_no, l1.order_no, l2.order_no, l3.order_no"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                menus = dbUtils.dictfetchall(cursor)
                for m in menus:
                    if m['top_menu_id'] is not None:
                        if (m['top_menu_id'] not in allSubMenuIDs):
                            allSubMenuIDs.append(m['top_menu_id'])
                        if (m['l1_menu_id'] not in allSubMenuIDs):
                            allSubMenuIDs.append(m['l1_menu_id'])
                        if (m['l2_menu_id'] not in allSubMenuIDs):
                            allSubMenuIDs.append(m['l2_menu_id'])
                        if (m['l3_menu_id'] not in allSubMenuIDs):
                            allSubMenuIDs.append(m['l3_menu_id'])
            if len(allSubMenuIDs) > 0:
                usrAclMenusQs = usrAclMenusQs.filter(parent_menu_id__in=allSubMenuIDs).order_by('order_no')
        # check user has menu permission
        for m in usrAclMenusQs:
            if m.parent_menu_id is not None and int(m.parent_menu_id) not in usrAclMenuIDs:
                usrAclMenuIDs.append(int(m.parent_menu_id))
            if m.id is not None and m.id not in usrAclMenuIDs:
                usrAclMenuIDs.append(m.id)

        # 2. auto get parent menu by user have permission sub menus(1)
        dbAllMenusDict = {}
        for menuDict in ikModels.Menu.objects.exclude(parent_menu_id__isnull=True).values('id', 'parent_menu_id'):
            dbAllMenusDict[menuDict['id']] = int(menuDict['parent_menu_id'])
        for menuDict in ikModels.Menu.objects.exclude(parent_menu_id__isnull=True).values('id', 'parent_menu_id'):
            dbAllMenusDict[menuDict['id']] = int(menuDict['parent_menu_id'])
        for menuID in [menuID for menuID in usrAclMenuIDs]:
            parentMenuID = dbAllMenusDict.get(menuID, None)
            while parentMenuID is not None:
                if parentMenuID not in usrAclMenuIDs:
                    usrAclMenuIDs.append(parentMenuID)
                parentMenuID = dbAllMenusDict.get(parentMenuID, None)

        usrMenuQs = ikModels.Menu.objects.filter(id__in=usrAclMenuIDs)
        if parentMenuId is None:
            usrMenuQs = usrMenuQs.filter(parent_menu_id__isnull=True)
        return usrMenuQs.order_by("order_no")

    def getMenuIdByScreenName(self, screenName) -> int:
        menuRcs = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT id FROM ik_menu WHERE screen_nm=' +
                           dbUtils.toSqlField(screenName))
            menuRcs = cursor.fetchall()
        if dbUtils.isEmpty(menuRcs):
            raise IkValidateException('Screen [%s] is not found.' % str(screenName))
        menuId = menuRcs[0][0]
        if len(menuRcs) > 1:
            logger.debug('Too many manus found for screen [%s], please check. System use the first menu(%s) instead.' % (screenName, menuId))
            # raise IkValidateException('Too many manus found for screen [%s], please check.' % str(screenName))
        return menuId

    def __getScreenName(self, classInstance) -> str:
        className = classInstance.__class__.__name__
        return className

    def getScreen2(self, request, classInstance, menuName=None, subScreenNm=None) -> Screen:
        screenName = self.__getScreenName(classInstance)

        menuID = None
        if menuName is None:
            menuID = self.getMenuIdByScreenName(screenName)
            if menuID is None:
                raise IkValidateException('Screen menu [%s] is not found.' % screenName)
        else:
            menuInfo = self.getUserMenuByMenuName(menuName)
            if menuInfo is None:
                raise IkValidateException('Menu [%s] is not found.' % menuName)
            menuID = menuInfo['id']

        acl = self.getUserMenuAcl(request.user.id, menuID)

        screen = IkUI.getScreen(screenName, subScreenNm=subScreenNm)
        if screen is None:
            logger.error('Screen spreadsheet is not found: screenName=%s', screenName)

        if acl is None or acl == ACL_DENY:
            logger.error('Permission deny. User=%s, screenName=%s, menuName=%s' % (request.user.usr_nm, screenName, menuName))
            raise IkValidateException('Permission deny.')
        # YL.ikyo, 2022-08-15, BUGFIX screen sometime is None - start
        elif screen is not None:
            if acl == ACL_READ:
                screen.editable = False
            elif acl == ACL_WRITE:
                screen.editable = True
        # YL.ikyo, 2022-08-15 - end
        return screen

    def getIkScreens(self) -> list:
        '''
            return ik_menu.screen_nm
        '''
        sql = "select distinct screen_nm from ik_menu where screen_nm is not null order by screen_nm"
        rcs = None
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rcs = dbUtils.dictfetchall(cursor)
        screenNames = []
        for r in rcs:
            screenNames.append(r['screen_nm'])
        return screenNames

    def getTopMenu(self, menu: ikModels.Menu):
        if menu is None:
            return None

        while True:
            if menu.parent_menu_id is None:
                return menu
            else:
                menu = ikModels.Menu.objects.filter(id=menu.parent_menu_id).first()

    def isSubMenus(self, menuID1, menuID2, max_loop=10):
        if menuID1 == menuID2:
            return 1

        menu = None
        subLevel = 1
        while True:
            menu = ikModels.Menu.objects.filter(id=menuID1).first()
            subLevel += 1
            if menu is not None:
                menuID1 = menu.parent_menu_id

            if not menu or menu.parent_menu_id is None:
                return 0
            if menu and menu.parent_menu_id == menuID2:
                return subLevel
            if subLevel > max_loop:
                raise IkValidateException(
                    'Detected circular reference in menu hierarchy. A menu cannot be a sub-menu of its own indirect/direct sub-menus.')

    def getFullMenuName(self, menuID: int, withAcl: bool) -> str:
        menu_nm = self.getMenuCaption(menuId=menuID)
        full_menu_nm = menu_nm
        parent_menu_id = self.getParentMenuId(menuID)
        while (parent_menu_id is not None):
            menu_nm = self.getMenuCaption(parent_menu_id)
            full_menu_nm = menu_nm + " -> " + full_menu_nm
            parent_menu_id = self.getParentMenuId(parent_menu_id)
        return full_menu_nm

    # YL.ikyo 2023-11-28 get all menu full menu list - start
    def getAllFullName(self) -> list:
        data = []
        top_menus = ikModels.Menu.objects.filter(parent_menu_id__isnull=True).exclude(enable=False).exclude(
            Q(menu_nm__iexact='home') | Q(menu_nm__iexact='menu')).order_by('order_no')
        for top_menu in top_menus:
            data.extend(self.get_menu_hierarchy(top_menu, []))
        return data

    def get_menu_hierarchy(self, menu_item, hierarchy=[]):
        menu_full_nm = menu_item.menu_nm
        tmp_menu_item = menu_item
        while tmp_menu_item.parent_menu_id:
            tmp_menu_item = ikModels.Menu.objects.get(id=tmp_menu_item.parent_menu_id)
            menu_full_nm = tmp_menu_item.menu_caption + " -> " + menu_full_nm
        hierarchy.append({'id': menu_item.id, 'menu_nm': menu_full_nm})
        sub_menus = ikModels.Menu.objects.filter(parent_menu_id=menu_item.id).order_by('order_no')
        for sub_menu in sub_menus:
            self.get_menu_hierarchy(sub_menu, hierarchy)
        return hierarchy
    # YL.ikyo 2023-11-28 - end


MenuManager = __MenuManager()
