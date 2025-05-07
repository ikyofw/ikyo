'''
Description: User Group Management
version: 
Author: XH.ikyo
Date: 2023-09-26 09:11:45
'''
from typing import Union

import core.ui.ui as ikui
from core.core.http import *
from core.db.transaction import IkTransaction
from core.menu.menuManager import MenuManager
from core.models import *
from core.user import UsrGrpMntManager, userManager
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.view.screenView import ScreenAPIView
from django.core.paginator import Paginator


class UsrGrpMntView(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            curGrpID = self.getSessionParameterInt("curGrpID")
            isNew = False if isNullBlank(self.getSessionParameterBool("isNew")) else self.getSessionParameterBool("isNew")

            if isNullBlank(curGrpID) and not isNew:
                screen.layoutParams = ''
                screen.setFieldGroupsVisible(
                    fieldGroupNames=['grpDtlFg', 'usrFg', 'scrFg', 'dtToolbar'], visible=False)
            else:
                screen.setFieldGroupsVisible(fieldGroupNames=['searchFg', 'toolbar1', 'grpListFg', 'toolbar2'], visible=False)
                if isNotNullBlank(curGrpID):
                    screen.setFieldsEditable(fieldGroupName="grpDtlFg", fieldNames="dNm", editable=False)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getSchRc(self):
        return self.getSessionParameter('schItems')

    def search(self):
        schItems = self.getRequestData().get('searchFg')
        return self.setSessionParameters({'schItems': schItems})

    def new(self):
        self.deleteSessionParameters(nameFilters=['curGrpID', 'newUserIDList'])
        self.setSessionParameters({'isNew': True})
        return IkSccJsonResponse()

    def getGrpListRcs(self):
        data = []
        grp_list = Group.objects.all().order_by('grp_nm')
        for grp in grp_list:
            # 1. get user list
            grp_usr_list = UserGroup.objects.filter(grp=grp)
            usr_list_str = ""
            index = 1
            for grp_usr in grp_usr_list:
                usr_list_str += ("\r\n" if isNotNullBlank(usr_list_str) else "") + str(index) + ". " + userManager.getUserName(grp_usr.usr.id)
                index += 1

            # 2. get menu list
            grp_menu_list = GroupMenu.objects.filter(grp=grp)
            menu_list_str = ""
            index = 1
            for grp_menu in grp_menu_list:
                menu_list_str += ("\r\n" if isNotNullBlank(menu_list_str) else "") + str(index) + ". " + \
                    MenuManager.getFullMenuName(grp_menu.menu.id, True) + " (" + grp_menu.acl + ")"
                index += 1
            data.append({'id': grp.id, 'grp_nm': grp.grp_nm, 'usrs': usr_list_str, 'menus': menu_list_str, 'rmk': grp.rmk})

        # search
        schItems = self.getSessionParameter('schItems')
        schKey = None
        if isNotNullBlank(schItems) and isNotNullBlank(schItems['schKey']):
            schKey = schItems['schKey']
            for d in data:
                if schKey.lower() not in d['grp_nm'].lower() and schKey.lower() not in d['usrs'].lower() \
                        and schKey.lower() not in d['menus'].lower() and schKey.lower() not in d['rmk'].lower():
                    data.remove(d)
        return IkSccJsonResponse(data=data)

    def showDtl(self):
        curGrpID = self._getEditIndexField()
        self.deleteSessionParameters(nameFilters='isNew')
        self.setSessionParameters({"curGrpID": curGrpID})
        return IkSccJsonResponse()

    def delete(self):
        deleteRcs: list = self.getRequestData().getSelectedTableRows('grpListFg')
        grpRcs = []
        for i in deleteRcs:
            grpRc = Group.objects.filter(id=i.id).first()
            if isNotNullBlank(grpRc):
                grpRc.ik_set_status_delete()
                grpRcs.append(grpRc)
        pytrn = IkTransaction(self)
        pytrn.add(grpRcs)
        b = pytrn.save()
        if not b.value:
            return IkErrJsonResponse(message=b.dataStr)
        return IkSccJsonResponse(message='Deleted.')

    def getCurGrpRc(self):
        curGrpID = self.getSessionParameter('curGrpID')
        data = {}
        if isNotNullBlank(curGrpID):
            data = Group.objects.filter(id=curGrpID).first()
        return IkJsonResponse(data=data)

    def getUsers(self):
        data = User.objects.filter(active=True).order_by('usr_nm')
        return IkJsonResponse(data=data)

    def getUsrRcs(self):
        curGrpID = self.getSessionParameter('curGrpID')
        data = UserGroup.objects.filter(grp_id=curGrpID).order_by('id')
        return IkJsonResponse(data=data)

    def getAcls(self):
        data = [{'acl': 'D', 'display_acl': 'Deny'}, {'acl': 'R', 'display_acl': 'Read'}, {'acl': 'W', 'display_acl': 'Write'}]
        return IkJsonResponse(data=data)

    def getMenuRcs(self):
        curGrpID = self.getSessionParameter('curGrpID')
        data = []
        if isNotNullBlank(curGrpID):
            data = GroupMenu.objects.filter(grp_id=curGrpID)
        return IkJsonResponse(data=data)

    def getMenus(self):
        nodeMenus = MenuManager.getNodeMenus()
        data = []
        for i in MenuManager.getAllFullName():
            if i['id'] not in nodeMenus:
                data.append(i)
        return IkJsonResponse(data=data)

    def save(self):
        saveUsrID = self.getCurrentUserId()
        curGrpID = self.getSessionParameterInt("curGrpID")
        isNew = self.getSessionParameterBool("isNew")
        requestData = self.getRequestData()

        b = UsrGrpMntManager.save(saveUsrID, curGrpID, isNew, requestData, self.__validate)
        if b.value:
            self.setSessionParameters({'curGrpID': b.data})
            return IkSccJsonResponse(message='Saved!')
        return b.toIkJsonResponse1()

    def refresh(self):
        return self.deleteSessionParameters(nameFilters=['newUserIDList', 'officeTeamFg'])

    def back(self):
        return self.deleteSessionParameters(nameFilters=['curGrpID', 'isNew', 'newUserIDList', 'officeTeamFg'])

    def __validate(self, rcs: list[Union[UserGroup, GroupMenu]], tableNm, fieldNm, now, groupID):
        saveUsrID = self.getCurrentUserId()
        records = list(rcs)
        ids = []

        for rc in records:
            id = getattr(rc, fieldNm)
            if isNullBlank(id):
                if rc.ik_is_status_new():
                    rcs.remove(rc)
                elif rc.ik_is_status_modified():
                    rc.ik_set_status_delete()
            else:
                if not rc.ik_is_status_delete():
                    if id in ids:
                        if rc.ik_is_status_new():
                            rcs.remove(rc)
                        else:
                            rc.ik_set_status_delete()
                    else:
                        ids.append(id)

        for rc in records:
            if not rc.ik_is_status_delete():
                if rc.ik_is_status_new():
                    rc.grp_id = groupID
