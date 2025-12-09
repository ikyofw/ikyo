from typing import Union
from datetime import datetime as datetime_

import core.ui.ui as ikui
from core.core.lang import Boolean2
from core.core.http import *
from core.db.transaction import IkTransaction
from core.menu.menu_manager import MenuManager
from core.user import user_manager
from core.utils.lang_utils import isNotNullBlank, isNullBlank
from core.view.screen_view import ScreenAPIView

from core.models import Group, User, GroupMenu, UserGroup


class UsrGrpMntView(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            cur_grp_id = self.getSessionParameterInt("cur_grp_id")
            is_new = False if isNullBlank(self.getSessionParameterBool("is_new")) else self.getSessionParameterBool("is_new")

            if isNullBlank(cur_grp_id) and not is_new:
                screen.layoutParams = ''
                screen.setFieldGroupsVisible(
                    fieldGroupNames=['grpDtlFg', 'usrFg', 'scrFg', 'dtToolbar'], visible=False)
            else:
                screen.setFieldGroupsVisible(fieldGroupNames=['searchFg', 'toolbar1', 'grpListFg', 'toolbar2'], visible=False)
                if isNotNullBlank(cur_grp_id):
                    screen.setFieldsEditable(fieldGroupName="grpDtlFg", fieldNames="dNm", editable=False)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getSchRc(self):
        return self.getSessionParameter('sch_items')

    def search(self):
        sch_items = self.getRequestData().get('searchFg')
        return self.setSessionParameters({'sch_items': sch_items})

    def new(self):
        self.deleteSessionParameters(nameFilters=['cur_grp_id', 'new_user_id_list'])
        self.setSessionParameters({'is_new': True})
        return IkSccJsonResponse()

    def getGrpListRcs(self):
        cur_grp_id = self.getSessionParameter('cur_grp_id')
        is_new = False if isNullBlank(self.getSessionParameterBool("is_new")) else self.getSessionParameterBool("is_new")
        if isNotNullBlank(cur_grp_id) or is_new:
            return IkSccJsonResponse(data=[])

        data = []
        grp_list = Group.objects.all().order_by('grp_nm').prefetch_related('usergroup_set', 'groupmenu_set__menu')
        for grp in grp_list:
            # 1. Get user list
            usr_list_str = ""
            for index, grp_usr in enumerate(grp.usergroup_set.all(), start=1):
                usr_list_str += ("" if not usr_list_str else "\r\n") + f"{index}. {user_manager.getUserName(grp_usr.usr_id)}"

            # 2. Get menu list
            menu_list_str = ""
            for index, grp_menu in enumerate(grp.groupmenu_set.all(), start=1):
                menu_full_name = MenuManager.get_full_menu_name(grp_menu.menu.id)
                menu_list_str += ("" if not menu_list_str else "\r\n") + f"{index}. {menu_full_name} ({grp_menu.acl})"

            data.append({
                'id': grp.id,
                'grp_nm': grp.grp_nm,
                'usrs': usr_list_str,
                'menus': menu_list_str,
                'rmk': grp.rmk
            })

        # Search filter
        sch_items = self.getSessionParameter('sch_items')
        if isNotNullBlank(sch_items) and isNotNullBlank(sch_items.get('schKey')):
            sch_key = sch_items['schKey'].lower()
            data = [
                d for d in data
                if sch_key in d['grp_nm'].lower()
                or sch_key in d['usrs'].lower()
                or sch_key in d['menus'].lower()
                or sch_key in (d['rmk'] or "").lower()
            ]
        return IkSccJsonResponse(data=data)

    def grpListFg_EditIndexField_Click(self):
        cur_grp_id = self._getEditIndexField()
        self.deleteSessionParameters(nameFilters='is_new')
        self.setSessionParameters({"cur_grp_id": cur_grp_id})
        return IkSccJsonResponse()

    def delete(self):
        delete_rcs: list = self.getRequestData().getSelectedTableRows('grpListFg')
        if len(delete_rcs) == 0:
            return IkErrJsonResponse(message='Please select at least one record to delete.')
        grp_rcs = []
        for delete_rc in delete_rcs:
            grp_rc = Group.objects.filter(id=delete_rc.id).first()
            if isNotNullBlank(grp_rc):
                grp_rc.ik_set_status_delete()
                grp_rcs.append(grp_rc)
        pytrn = IkTransaction(self)
        pytrn.add(grp_rcs)
        b = pytrn.save()
        if not b.value:
            return IkErrJsonResponse(message=b.dataStr)
        return IkSccJsonResponse(message='Deleted.')

    def getCurGrpRc(self):
        cur_grp_id = self.getSessionParameter('cur_grp_id')
        data = {}
        if isNotNullBlank(cur_grp_id):
            data = Group.objects.filter(id=cur_grp_id).first()
        return IkJsonResponse(data=data)

    def getUsrRcs(self):
        cur_grp_id = self.getSessionParameter('cur_grp_id')
        data = UserGroup.objects.filter(grp_id=cur_grp_id).order_by('id')
        return IkJsonResponse(data=data)

    def getUsers(self):
        active_users = User.objects.filter(active=True).order_by('usr_nm')
        leaved_users = User.objects.filter(active=False).order_by('usr_nm')
        data = [{'id': user.id, 'usr_nm': user.usr_nm} for user in active_users]
        for leaved_user in leaved_users:
            data.append({'id': leaved_user.id, 'usr_nm': f"{leaved_user.usr_nm} - Leaved"})
        return IkJsonResponse(data=data)

    def getMenuRcs(self):
        cur_grp_id = self.getSessionParameter('cur_grp_id')
        data = []
        if isNotNullBlank(cur_grp_id):
            data = GroupMenu.objects.filter(grp_id=cur_grp_id)
        return IkJsonResponse(data=data)

    def getMenus(self):
        node_menus = MenuManager.getNodeMenus()
        data = []
        for i in MenuManager.getAllFullName():
            if i['id'] not in node_menus:
                data.append(i)
        return IkJsonResponse(data=data)

    def getAcls(self):
        data = [{'acl': 'D', 'display_acl': 'Deny'}, {'acl': 'R', 'display_acl': 'Read'}, {'acl': 'W', 'display_acl': 'Write'}]
        return IkJsonResponse(data=data)

    def save(self):
        usr_id = self.getCurrentUserId()
        cur_grp_id = self.getSessionParameterInt("cur_grp_id")
        is_new = self.getSessionParameterBool("is_new")
        request_data = self.getRequestData()

        b = save(usr_id, cur_grp_id, is_new, request_data, self.__validate)
        if b.value:
            self.deleteSessionParameters('is_new')
            self.setSessionParameters({'cur_grp_id': b.data})
            return IkSccJsonResponse(message='Saved!')
        return b.toIkJsonResponse1()

    def refresh(self):
        return self.deleteSessionParameters(nameFilters=['new_user_id_list'])

    def back(self):
        self._deleteEditIndexFieldValue()
        return self.deleteSessionParameters(nameFilters=['cur_grp_id', 'is_new', 'new_user_id_list'])

    def __validate(self, rcs: list[Union[UserGroup, GroupMenu]], table_nm, field_nm, now, group_id):
        records = list(rcs)
        ids = []

        for rc in records:
            id = getattr(rc, field_nm)
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
                    rc.grp_id = group_id


def save(save_usr_id, cur_grp_id, is_new, request_data, validate) -> Boolean2:
    now = datetime_.now()
    grp_rc: Group = request_data.get('grpDtlFg')
    usr_rcs: list[UserGroup] = request_data.get('usrFg')
    scr_rcs: list[GroupMenu] = request_data.get('scrFg')

    group_name = grp_rc.grp_nm.strip()
    if isNullBlank(group_name):
        return Boolean2(False, "Group Name is mandatory.")
    grp_rc.grp_nm = group_name

    if isNullBlank(cur_grp_id) and isNullBlank(is_new):
        return Boolean2(False, "Save error, the id of the group to be modified was not found.")
    elif isNotNullBlank(cur_grp_id):
        saved_group_rcs = Group.objects.filter(grp_nm__iexact=group_name).exclude(id=cur_grp_id).first()
    else:
        saved_group_rcs = Group.objects.filter(grp_nm__iexact=group_name).first()
    if isNotNullBlank(saved_group_rcs):
        return Boolean2(False, "Group Name is unique, please check.")

    if isNotNullBlank(is_new):
        grp_rc.assignPrimaryID()

    group_id = grp_rc.id

    usr_rcs = [usr_rc for usr_rc in usr_rcs if usr_rc.usr.active]
    
    validate(usr_rcs, 'usrFg', 'usr_id', now, group_id)
    validate(scr_rcs, 'scrFg', 'menu_id', now, group_id)

    pytrn = IkTransaction(userID=save_usr_id)
    pytrn.add(grp_rc)
    pytrn.add(usr_rcs)
    pytrn.add(scr_rcs)
    b = pytrn.save()
    if not b.value:
        return Boolean2(False, b.dataStr)
    return Boolean2(True, group_id)
