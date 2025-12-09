import hashlib
from collections import Counter
from typing import Any, Callable, List

from django.contrib.auth.hashers import make_password
from django.db.models import Q

import core.ui.ui as ikui
from core.core.http import *
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import *
from core.utils import model_utils, str_utils
from core.utils.lang_utils import isNotNullBlank, isNullBlank
from core.view.screen_view import ScreenAPIView
from iktools import IkConfig


class UsrMntView(ScreenAPIView):

    SESSION_KEY_USER_ID = "user_ID"
    SESSION_KEY_IS_NEW = "is_new"
    SESSION_KEY_USER_OLD_PASSWORD = "old_password"

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            user_id = self.getSessionParameter(self.SESSION_KEY_USER_ID)
            is_new = self.getSessionParameterBool(self.SESSION_KEY_IS_NEW, default=False)
            screen.setFieldGroupsVisible(fieldGroupNames=['schFg', 'usrListFg'], visible=isNullBlank(user_id) and not is_new)
            screen.setFieldGroupsVisible(fieldGroupNames=['usrDtlFg', 'groupFg', 'officeFg'], visible=isNotNullBlank(user_id) or is_new)
            screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttNew', visible=isNullBlank(user_id) and not is_new)
            screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttDelete', visible=isNotNullBlank(user_id) and not is_new)
            screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames=['bttBack', 'bttSave', 'bttSaveNew', 'bttReset'], visible=isNotNullBlank(user_id) or is_new)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def get_sch_rc(self):
        data = None
        sch_items = self.getSessionParameter('sch_items')
        if isNotNullBlank(sch_items):
            data = sch_items
        return data

    def search(self):
        sch_item = self.getRequestData().get('schFg', None)
        if all(v in [None, '', [], {}] for v in sch_item.values()):
            sch_item = None
        return self.setSessionParameters({'sch_items': sch_item})

    def get_status(self):
        return [{'value': True, 'display': 'Enable'}, {'value': False, 'display': 'Disable'}]

    def get_user_rcs(self):
        data = User.objects.all().order_by('usr_nm')
        sch_items = self.getSessionParameter('sch_items')
        if isNullBlank(sch_items):
            data = data.filter(active=True)
        else:
            status = sch_items.get('schStatus')
            keyword = sch_items.get('schKeyword')
            if isNotNullBlank(status):
                data = data.filter(active=status.strip().lower() == 'true')
            if isNotNullBlank(keyword):
                sub_query = (Q(usr_nm__icontains=keyword) | Q(rmk__icontains=keyword) | Q(usergroup__grp__grp_nm__icontains=keyword))
                data = data.filter(sub_query).distinct()
        return self.getPagingResponse(table_name="usrListFg", table_data=data)

    def usrListFg_EditIndexField_Click(self):
        return self.setSessionParameters({self.SESSION_KEY_USER_ID: self._getEditIndexField(), self.SESSION_KEY_IS_NEW: False})

    def get_user_rc(self):
        user_id = self.getSessionParameter(self.SESSION_KEY_USER_ID)
        is_new = self.getSessionParameter(self.SESSION_KEY_IS_NEW)
        data = {}
        if is_new:
            data['active'] = True
        elif isNotNullBlank(user_id):
            data = User.objects.filter(id=user_id).first()
            if isNullBlank(data):
                return IkErrJsonResponse(message='User does not exist!')
            self.setSessionParameters({self.SESSION_KEY_USER_OLD_PASSWORD: data.psw})
            data.psw = None
        return IkSccJsonResponse(data=data)

    def get_offices(self):
        return Office.objects.all().order_by('code')

    def get_groups(self):
        return Group.objects.all().order_by('grp_nm')

    def get_user_office_rcs(self):
        user_id = self.getSessionParameter(self.SESSION_KEY_USER_ID)
        data = None
        if isNotNullBlank(user_id):
            data = UserOffice.objects.filter(usr_id=user_id).order_by("seq")
        return IkSccJsonResponse(data=data)

    def get_user_group_rcs(self):
        user_id = self.getSessionParameter(self.SESSION_KEY_USER_ID)
        data = None
        if isNotNullBlank(user_id):
            data = UserGroup.objects.filter(usr_id=user_id)
        return IkSccJsonResponse(data=data)

    def new(self):
        self.deleteSessionParameters(nameFilters=[self.SESSION_KEY_USER_ID])
        return self.setSessionParameters({self.SESSION_KEY_IS_NEW: True})

    def back(self):
        return self.deleteSessionParameters(nameFilters=[self.SESSION_KEY_USER_ID, self.SESSION_KEY_IS_NEW, self.SESSION_KEY_USER_OLD_PASSWORD])

    def save(self):
        result = self._save()
        if result.value and isinstance(result.data, int):
            self.setSessionParameters({self.SESSION_KEY_USER_ID: result.data, self.SESSION_KEY_IS_NEW: False})
            self._addInfoMessage("Saved.")
            return self._setEditIndexFieldValue(value=result.data, fieldGroupName='usrListFg')
        return result.toIkJsonResponse1()

    def save_and_new(self):
        result = self._save()
        if result.value:
            self._addInfoMessage("Saved.")
            return self.new()
        return result.toIkJsonResponse1()

    def delete(self):
        user_id = self.getSessionParameter(self.SESSION_KEY_USER_ID)
        if isNullBlank(user_id):
            return IkSysErrJsonResponse()
        user_rc = User.objects.filter(id=user_id).first()
        if isNullBlank(user_rc):
            return IkErrJsonResponse(message="User does not exists.")
        if not user_rc.active:
            return IkErrJsonResponse(message="User[%s] has been deleted.")

        user_rc.active = False
        user_rc.ik_set_status_modified()
        pytrn = IkTransaction(self)
        pytrn.add(user_rc)
        b = pytrn.save()
        if not b.value:
            return IkErrJsonResponse(message="Delete user failed: " + b.dataStr)
        self.back()
        return IkSccJsonResponse(message='Deleted.')

    def reset(self):
        pass

    def _save(self) -> Boolean2:
        request_data = self.getRequestData()
        user_rc: User = request_data.get('usrDtlFg')
        user_office_rcs: list[UserOffice] = request_data.get('officeFg')
        user_group_rcs: list[UserGroup] = request_data.get('groupFg')
        if isNullBlank(user_rc) or isNullBlank(user_office_rcs) or isNullBlank(user_group_rcs):
            return Boolean2(False, 'System error, please ask administrator to check.')
        # check user fg is real modified
        if user_rc.ik_is_status_modified() and isNullBlank(user_rc.psw):
            user_rc_in_db = User.objects.get(id=user_rc.id)
            exclude_fields = {'id', 'version_no', 'psw'}
            user_model_fields = [field.name for field in User._meta.get_fields() if field.concrete and not field.auto_created and field.name not in exclude_fields]
            if model_utils.models_equal(user_rc, user_rc_in_db, user_model_fields):
                user_rc.ik_set_status_retrieve()
        if user_rc.ik_is_status_retrieve() and all(office.ik_is_status_retrieve() for office in user_office_rcs) and all(group.ik_is_status_retrieve() for group in user_group_rcs):
            return Boolean2(True, 'Nothing changed.')
        old_password = self.getSessionParameter(self.SESSION_KEY_USER_OLD_PASSWORD)

        # 1. User
        # name
        user_rc.usr_nm = user_rc.usr_nm.strip()
        same_name_rc = None
        if user_rc.ik_is_status_new():
            same_name_rc = User.objects.filter(usr_nm__iexact=user_rc.usr_nm).first()
        elif user_rc.ik_is_status_modified():
            same_name_rc = User.objects.filter(usr_nm__iexact=user_rc.usr_nm).exclude(id=user_rc.id).first()
        if isNotNullBlank(same_name_rc):
            return Boolean2(False, 'Duplicate user name [%s], please change. (e.g. add suffix)' % user_rc.usr_nm)

        # email
        if isNotNullBlank(user_rc.email):
            user_rc.email = user_rc.email.strip()
            if not str_utils.isEmail(user_rc.email):
                return Boolean2(False, 'Email is incorrect!')

        # password
        if isNullBlank(user_rc.psw):
            if user_rc.ik_is_status_new():
                return Boolean2(False, 'Password is mandatory!')
            elif user_rc.ik_is_status_modified():
                user_rc.psw = old_password
        else:
            user_rc.psw = user_rc.psw.strip()
            if len(user_rc.psw) < 6:
                return Boolean2(False, 'The password\'s length should be equal to or greater than 6 characters!')
            # encryption
            encryption_method = IkConfig.getSystem('password_encryption_method').lower()
            if encryption_method == 'md5':
                encrypted_password = hashlib.md5(user_rc.psw.encode("utf8")).hexdigest()
            elif encryption_method == 'pbkdf2':
                encrypted_password = make_password(user_rc.psw)
            else:
                return Boolean2(False, 'Unsupported password encryption method: [%s], please choose in [MD5/PBKDF2]' % encryption_method)
            user_rc.psw = encrypted_password

        # Validate
        # (1). check repeat
        # office
        boo = self._check_duplicates(records=user_office_rcs, key_func=lambda rc: rc.office.code, label="office")
        if not boo.value:
            return boo
        # group
        boo = self._check_duplicates(records=user_group_rcs, key_func=lambda rc: rc.grp.grp_nm, label="group")
        if not boo.value:
            return boo
        # (2). check default
        # office
        boo = self._check_default(records=user_office_rcs, field='is_default', label='default office')
        if not boo.value:
            return boo

        # 2. UserOffice
        for rc in filter(lambda x: x.ik_is_status_new(), user_office_rcs):
            rc.usr = user_rc
        # sort
        self._sort(user_office_rcs, ['-is_default', 'seq'])

        # 3. UserGroup
        for rc in filter(lambda x: x.ik_is_status_new(), user_group_rcs):
            rc.usr = user_rc

        pytrn = IkTransaction(self)
        pytrn.add(user_rc)
        pytrn.add(user_office_rcs)
        pytrn.add(user_group_rcs)
        b = pytrn.save()
        if not b.value:
            return Boolean2(False, b.dataStr)
        return Boolean2(True, user_rc.id)

    def _sort(self, records: list, sort_by: list[str] | str = 'seq', reorder_field: str = 'seq'):
        """
            Sort records by given field name, re-sort them to 1..n (excluding deleted),
            and mark as modified if existing and value changed.

        Args:
            records (list): List of model instances
            sort_by (str | list[str]): Field name(s) to sort by
            reorder_field (str): The field to re-number (default: 'seq')
        """
        if not records:
            return
        if isinstance(sort_by, str):
            sort_by = [sort_by]

        def sort_key(obj):
            result = []
            for field in sort_by:
                reverse = field.startswith('-')
                field_name = field[1:] if reverse else field
                value = getattr(obj, field_name, None)
                if value is None:
                    value = float('inf')  # None goes last
                result.append(-value if reverse and isinstance(value, (int, float, bool)) else (not value if reverse and isinstance(value, bool) else value))
            return tuple(result)

        records.sort(key=sort_key)

        seq = 1
        for rc in records:
            if rc.ik_is_status_delete():
                continue
            current_seq = getattr(rc, reorder_field, None)
            if seq != current_seq:
                setattr(rc, reorder_field, seq)
                if not rc.ik_is_status_new():
                    rc.ik_set_status_modified()
            seq += 1

    def _check_duplicates(self, records: List[Any], key_func: Callable[[Any], str], label: str = "Name"):
        """
            Generic function to check for duplicates in a list of objects.

        Args:
            records (List[Any]): A list of objects to check.
            key_func (Callable[[Any], str]): A function that extracts the comparison key from each object, e.g. lambda x: x.office.code.
            label (str, optional): A string label for the object type, used in the error message.

        Returns:
            Boolean2: Boolean2(True) if no duplicates, otherwise Boolean2(False, "There are duplicate ...")
        """
        filtered = [item for item in records if not item.ik_is_status_delete()]  # except delete status
        keys = [key_func(r) for r in filtered]
        counter = Counter(keys)
        duplicates = [k for k, c in counter.items() if c > 1]
        if duplicates:
            if isinstance(duplicates[0], int):
                return Boolean2(False, f"There are duplicate {label}")
            return Boolean2(False, f"There are duplicate {label}: {', '.join(duplicates)}")
        return Boolean2(True)

    def _check_default(self, records: List[Any], field: str = 'is_default', label: str = 'default item') -> Boolean2:
        """
            Check that exactly one item in the list has attr=True.

        Args:
            records (List[Any]): list of objects to check
            field (str, optional): field name to check for True (default: 'is_default')
            label (str, optional): name to show in the error message (default: 'default item')
        Returns:
            Boolean2: Boolean2(True) or Boolean2(False, message)
        """
        if not records:
            return Boolean2(True)  # Nothing to check
        filtered = [item for item in records if not item.ik_is_status_delete()]  # except delete status
        default_count = sum(1 for item in filtered if getattr(item, field, False))
        if default_count == 0:
            return Boolean2(False, f'Please set a {label}.')
        elif default_count > 1:
            return Boolean2(False, f'Only one {label} is allowed, please check.')
        return Boolean2(True)
