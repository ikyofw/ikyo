'''
Description: User Management
version: 
Author: XH.ikyo
Date: 2023-09-18 13:16:34
'''
from django.core.paginator import Paginator
from django.forms import model_to_dict

import core.ui.ui as ikui
from core.core.http import *
from core.db.transaction import IkTransaction
from core.models import *
from core.user import UsrMntManager
from core.view.screenView import ScreenAPIView


class UsrMntView(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            currentUsrID = self.getSessionParameterInt("currentUsrID")
            isNew = False if isNullBlank(self.getSessionParameterBool("createNew")) else self.getSessionParameterBool("createNew")

            screen.setFieldGroupsVisible(fieldGroupNames=['usrDtlFg', 'grpFg', 'officeFg', 'dtToolbar'], visible=isNotNullBlank(currentUsrID) or isNew)
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
        usrRcs = UsrMntManager.getUsrList(schItems)

        def format_res_func(results):
            data = [model_to_dict(instance) for instance in results]
            for i in data:
                i['grps'] = self.__getGroups(usr_id=i['id'])
                # i['company'] = self.__getCompany(usr_id=i['id'])
            return data
        return self.getPagingResponse(table_name="usrListFg", table_data=usrRcs, format_res_func=format_res_func)

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
            data['active'] = True
        data['psw'] = ''
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

    def getOfficeRcs(self):
        data = [
            {"id": office.id, "code": f'{office.code} - {office.name}'}
            for office in Office.objects.all().order_by('code')
        ]
        return IkSccJsonResponse(data=data)

    def getUsrOfficeRcs(self):
        currentUsrID = self.getSessionParameter('currentUsrID')
        data = []
        if isNotNullBlank(currentUsrID):
            data = UserOffice.objects.filter(usr_id=currentUsrID).order_by("seq")
        return IkSccJsonResponse(data=data)

    def back(self):
        return self.deleteSessionParameters(nameFilters=['currentUsrID', 'createNew'])

    def save(self):
        saveUsrID = self.getCurrentUserId()
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        oldPsw = self.getSessionParameter('oldPsw')
        requestData = self.getRequestData()

        b = UsrMntManager.save(saveUsrID, currentUsrID, createNew, requestData, oldPsw)
        if b.value:
            self.deleteSessionParameters(nameFilters='createNew')
            self.setSessionParameters({'currentUsrID': b.data})
            return IkSccJsonResponse(message='Saved.')
        return b.toIkJsonResponse1()

    def saveAndCreate(self):
        saveUsrID = self.getCurrentUserId()
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        oldPsw = self.getSessionParameter('oldPsw')
        requestData = self.getRequestData()

        b = UsrMntManager.save(saveUsrID, currentUsrID, createNew, requestData, oldPsw)
        if b.value:
            self.setSessionParameter('createNew', True)
            self._addInfoMessage("Saved.")
            return self.addUser()
        return b.toIkJsonResponse1()

    def delete(self):
        currentUsrID = self.getSessionParameter('currentUsrID')
        createNew = self.getSessionParameter('createNew')
        if createNew:
            self.back()
        elif isNotNullBlank(currentUsrID):
            usrRc = User.objects.filter(id=currentUsrID).first()
            if isNullBlank(usrRc) or usrRc.active == False:
                self.back()
            usrRc.active = False
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
