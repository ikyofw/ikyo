from typing import Union
import sys

from django.core.paginator import Paginator
from django.forms import model_to_dict

import core.ui.ui as ikui
from core.manager import ugmm, umm
from core.auth.index import hasLogin
from core.core.http import *
from core.db.transaction import IkTransaction
from core.init import initIk
from core.menu.menuManager import MenuManager
from core.user import userManager
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.view.screenView import ScreenAPIView
from iktools import IkConfig

from .models import *

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
if 'runserver' in sys.argv: # makemigrations and migrate don'et need to parse screen files.
    initIk()


class UsrMnt(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            currentUsrID = self.getSessionParameterInt("currentUsrID")
            isNew = False if isNullBlank(self.getSessionParameterBool("createNew")) else self.getSessionParameterBool("createNew")

            screen.setFieldGroupsVisible(fieldGroupNames=['usrDtlFg', 'grpFg', 'dtToolbar'], visible=isNotNullBlank(currentUsrID) or isNew)
            screen.setFieldGroupsVisible(fieldGroupNames=['schFg', 'schToolbar', 'usrListFg'], visible=isNullBlank(currentUsrID) and not isNew)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getSchRc(self):
        schItems = self.getSessionParameter('schItems')
        data = {}
        if isNullBlank(schItems):  # before click search
            data = {'schEnb': True}
        else:
            data = schItems
        return data

    def search(self):
        requestData = self.getRequestData()
        return self.setSessionParameters({"schItems": requestData.get("schFg")})

    def addUser(self):
        self.deleteSessionParameters(nameFilters=['currentUsrID', 'externalIOCorrectUsrFlag'])
        self.setSessionParameters({'createNew': True})
        return IkSccJsonResponse()

    def getUserListRcs(self):
        schItems = self.getSessionParameter('schItems')
        usrRcs = umm.getUsrList(schItems)
        pageSize = self._getPaginatorPageSize("usrListFg")  # screen
        pageNum = self._getPaginatorPageNumber("usrListFg")  # from client

        totalLen = usrRcs.count()
        paginator = Paginator(usrRcs, pageSize)
        results = paginator.get_page(pageNum)

        data = [model_to_dict(instance) for instance in results]
        for i in data:
            i['grps'] = self.__getGroups(usr_id=i['id'])
            # i['company'] = self.__getCompany(usr_id=i['id'])
        return IkSccJsonResponse(data={"usrListFg": data, "__dataLen__": totalLen})

    def showDtl(self):
        currentUsrID = self._getEditIndexField()
        self.deleteSessionParameters(nameFilters='createNew')
        self.setSessionParameters({"currentUsrID": currentUsrID})
        return IkSccJsonResponse()

    def getCurrentUsrRc(self):
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        data = {}
        if isNotNullBlank(currentUsrID):
            usrRc = User.objects.filter(id=currentUsrID).first()
            if isNullBlank(usrRc):
                return IkErrJsonResponse(message='User does not exist!')
            data = model_to_dict(usrRc)
            self.setSessionParameters({'oldPsw': data['psw']})
        elif createNew:
            data['enable'] = 'Y'
        return IkSccJsonResponse(data=data)

    def getGrpNm(self):
        data = Group.objects.filter(id__gt=0).order_by('grp_nm')
        return IkSccJsonResponse(data=data)

    def getUsrGrpRcs(self):
        currentUsrID = self.getSessionParameter('currentUsrID')
        data = []
        if isNotNullBlank(currentUsrID):
            grpIds = Group.objects.all().values_list('id', flat=True)
            data = UserGroup.objects.filter(usr_id=currentUsrID, grp_id__in=grpIds)
        return IkSccJsonResponse(data=data)

    def back(self):
        return self.deleteSessionParameters(nameFilters=['currentUsrID', 'createNew'])

    def save(self):
        saveUsrID = self.getCurrentUserId()
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        oldPsw = self.getSessionParameter('oldPsw')
        requestData = self.getRequestData()

        b = umm.save(saveUsrID, currentUsrID, createNew, requestData, oldPsw)
        if b.value:
            self.deleteSessionParameters(nameFilters='createNew')
            self.setSessionParameters({'currentUsrID': b.data})
            return IkSccJsonResponse(message='Saved!')
        return b.toIkJsonResponse1()

    def delete(self):
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        if createNew:
            self.back()
        elif isNotNullBlank(currentUsrID):
            usrRc = User.objects.filter(id=currentUsrID).first()
            if isNullBlank(usrRc) or usrRc.enable == 'N':
                self.back()
            usrRc.enable = 'N'
            usrRc.ik_set_status_modified()
            pytrn = IkTransaction(self)
            pytrn.add(usrRc)
            b = pytrn.save()
            if not b.value:
                return IkErrJsonResponse(message="disable user failed: " + b.dataStr)
            self.back()
            return IkSccJsonResponse(message='Disable user success.')

    def reset(self):
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        if createNew:
            return self.addUser()
        elif isNotNullBlank(currentUsrID):
            return self.deleteSessionParameters(nameFilters='createNew')

    def __getGroups(self, usr_id):
        groupIds = UserGroup.objects.filter(usr_id=usr_id).values_list('grp_id', flat=True)
        groups = Group.objects.filter(id__in=groupIds).order_by('grp_nm')
        return "\n".join([f"{idx + 1}. {group.grp_nm}" for idx, group in enumerate(groups)])


class UsrGrpMnt(ScreenAPIView):

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
        schKeyRst = []
        if isNotNullBlank(schItems) and isNotNullBlank(schItems['schKey']):
            schKey = schItems['schKey']
            for d in data:
                if schKey.lower() not in d['grp_nm'].lower() and schKey.lower() not in d['usrs'].lower() \
                        and schKey.lower() not in d['menus'].lower() and schKey.lower() not in d['rmk'].lower():
                    data.remove(d)
        pageSize = self._getPaginatorPageSize("grpListFg")
        pageNum = self._getPaginatorPageNumber("grpListFg")
        totalLen = len(data)
        paginator = Paginator(data, pageSize)
        results = paginator.get_page(pageNum)
        return IkSccJsonResponse(data={"grpListFg": results.object_list, "__dataLen__": totalLen})

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
        usrRcs = User.objects.filter(enable='Y').order_by('usr_nm')
        data = []
        for i in usrRcs:
            data.append({'usr_id': i.id, 'usr_nm': i.usr_nm})
        return IkJsonResponse(data=data)

    def getUsers(self):
        data = User.objects.filter(enable='Y').order_by('usr_nm')
        return IkJsonResponse(data=data)

    def getUsrRcs(self):
        curGrpID = self.getSessionParameter('curGrpID')
        data = UserGroup.objects.filter(grp_id=curGrpID).order_by('id')
        return IkJsonResponse(data=data)

    def getAcls(self):
        data = [{'acl': 'N', 'display_acl': 'None'}, {'acl': 'R', 'display_acl': 'Read'}, {'acl': 'W', 'display_acl': 'Write'}]
        return IkJsonResponse(data=data)

    def getMenuRcs(self):
        curGrpID = self.getSessionParameter('curGrpID')
        data = []
        if isNotNullBlank(curGrpID):
            data = GroupMenu.objects.filter(grp_id=curGrpID)
        return IkJsonResponse(data=data)

    def getMenus(self):
        return IkJsonResponse(data=MenuManager.getAllFullName())

    def save(self):
        saveUsrID = self.getCurrentUserId()
        curGrpID = self.getSessionParameterInt("curGrpID")
        isNew = self.getSessionParameterBool("isNew")
        requestData = self.getRequestData()

        b = ugmm.save(saveUsrID, curGrpID, isNew, requestData, self.__validate)
        if b.value:
            self.setSessionParameters({'curGrpID': b.data})
            return IkSccJsonResponse(message='Saved!')
        return b.toIksonResponse1()

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
                        if tableNm == 'scrFg':
                            if rc.acl not in ['W', 'R']:
                                rc.ik_set_status_delete()
                            else:
                                ids.append(id)
                        else:
                            ids.append(id)

        for rc in records:
            if not rc.ik_is_status_delete():
                if rc.ik_is_status_new():
                    rc.grp_id = groupID
