from django.db.models import Q

from .. import models as core_models
from ..core.http import *
from ..db.transaction import IkTransaction
from ..ui import ui as ikui
from ..view.screen_view import ScreenAPIView

SESSION_KEY_PERM_ID = "permission_control_id"
SESSION_KEY_IS_NEW = "is_new"


class PermissionControl(ScreenAPIView):
    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            perm_id = self.getSessionParameter(SESSION_KEY_PERM_ID)
            is_new = self.getSessionParameterBool(SESSION_KEY_IS_NEW, default=False)
            screen.setFieldGroupsVisible(fieldGroupNames=['schFg', 'dataFg'], visible=isNullBlank(perm_id) and not is_new)
            screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames=['bttNew', 'bttDelete'], visible=isNullBlank(perm_id) and not is_new)
            screen.setFieldGroupsVisible(fieldGroupNames=['dtlFg', 'dtlUsrFg', 'dtlGrpFg'], visible=isNotNullBlank(perm_id) or is_new)
            screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames=['bttBack', 'bttSave'], visible=isNotNullBlank(perm_id) or is_new)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def get_users(self):
        users = core_models.User.objects.all().order_by('-active', 'usr_nm')
        for user in users:
            if not user.active:
                user.usr_nm = f"{user.usr_nm} - Leaved"
        return users

    def get_groups(self):
        return core_models.Group.objects.all().order_by('grp_nm')

    def get_sch_rc(self):
        sch_item = self.getSessionParameter('sch_item')
        return IkSccJsonResponse(data=sch_item)

    def search(self):
        sch_item = self.getRequestData().get('schFg', None)
        if all(v in [None, '', [], {}] for v in sch_item.values()):
            sch_item = None
        return self.setSessionParameters({'sch_item': sch_item})

    def get_perm_rcs(self):
        data = core_models.PermissionControl.objects.all().order_by('id')
        sch_item = self.getSessionParameter('sch_item')
        if isNotNullBlank(sch_item):
            keyword = sch_item.get('keyword', None)
            if isNotNullBlank(keyword):
                data = data.filter(Q(name__icontains=keyword) | Q(rmk__icontains=keyword) | Q(permission_control_users__user__usr_nm__icontains=keyword))
        return IkSccJsonResponse(data=data)

    def dataFg_EditIndexField_Click(self):
        permission_control_id = self._getEditIndexField()
        return self.setSessionParameters({SESSION_KEY_PERM_ID: permission_control_id})

    def get_perm_rc(self):
        data = None
        permission_control_id = self.getSessionParameter(SESSION_KEY_PERM_ID)
        if isNotNullBlank(permission_control_id):
            data = core_models.PermissionControl.objects.filter(id=permission_control_id).first()
        return IkSccJsonResponse(data=data)

    def get_perm_user_rcs(self):
        data = None
        permission_control_id = self.getSessionParameter(SESSION_KEY_PERM_ID)
        if isNotNullBlank(permission_control_id):
            data = core_models.PermissionControlUser.objects.filter(permission_control_id=permission_control_id, user_id__isnull=False)
        return IkSccJsonResponse(data=data)

    def get_perm_grp_rcs(self):
        data = None
        permission_control_id = self.getSessionParameter(SESSION_KEY_PERM_ID)
        if isNotNullBlank(permission_control_id):
            data = core_models.PermissionControlUser.objects.filter(permission_control_id=permission_control_id, group_id__isnull=False)
        return IkSccJsonResponse(data=data)

    def new(self):
        return self.setSessionParameter(SESSION_KEY_IS_NEW, True)

    def back(self):
        self._deleteEditIndexFieldValue()
        return self.deleteSessionParameters(nameFilters=[SESSION_KEY_IS_NEW, SESSION_KEY_PERM_ID])

    def save(self):
        dtl_rc = self.getRequestData().get('dtlFg')
        user_rcs = self.getRequestData().get('dtlUsrFg')
        group_rcs = self.getRequestData().get('dtlGrpFg')
        if isNullBlank(dtl_rc) or isNullBlank(user_rcs) or isNullBlank(group_rcs):
            return IkSysErrJsonResponse()
        if dtl_rc.ik_is_status_retrieve() and all(user.ik_is_status_retrieve() for user in user_rcs) and all(group.ik_is_status_retrieve() for group in group_rcs):
            return IkSccJsonResponse(message="Nothing changed.")
        for rc in user_rcs:
            if rc.ik_is_status_new() or rc.ik_is_status_modified():
                if rc.ik_is_status_new():
                    rc.permission_control = dtl_rc
                if not core_models.User.objects.get(id=rc.user_id).active:
                    return IkErrJsonResponse(message=f"{rc.user.usr_nm} does leaved.")
        for rc in group_rcs:
            if rc.ik_is_status_new():
                rc.permission_control = dtl_rc

        ptrn = IkTransaction(self)
        ptrn.add(dtl_rc)
        ptrn.add(user_rcs)
        ptrn.add(group_rcs)
        b = ptrn.save()
        if b.value:
            self.setSessionParameters({SESSION_KEY_IS_NEW: False, SESSION_KEY_PERM_ID: dtl_rc.id})
        return b.toIkJsonResponse1()

    def delete(self):
        select_rcs = self._getTableSelectedRecords()
        if isNullBlank(select_rcs) or len(select_rcs) == 0:
            return self._addInfoMessage("Please select something to delete.")
        for rc in select_rcs:
            rc.ik_set_status_delete()

        ptrn = IkTransaction(self)
        ptrn.add(select_rcs)
        b = ptrn.save()
        if b.value:
            return IkSccJsonResponse(message="Deleted.")
        return b.toIkJsonResponse1()
