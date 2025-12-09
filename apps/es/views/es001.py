import logging

from django.db.models import Q

from core.core.exception import IkValidateException
from core.core.http import IkErrJsonResponse
from core.log.logger import logger
from core.models import Setting, UserOffice
from core.utils.lang_utils import isNotNullBlank, isNullBlank

from ..core import const, setting
from ..core.office import get_user_offices
from ..models import (Accounting, Approver, Group, Payee,
                      PettyCashExpenseAdmin, User, UserRole)
from .es_base import ESAPIView

logger = logging.getLogger('ikyo')


class ES001A(ESAPIView):
    """ES001A - Payment Method
    """
    pass


class ES001B(ESAPIView):
    """ES001B - Payee
    """

    def getPayeeRcs(self):
        """Get payee records"""
        queryData = self.getSearchData(fieldGroupName='schFg')
        schOfficeID = queryData.get('schOffice', None) if queryData else None
        schContent = queryData.get('schContent', None) if queryData else None
        payeeFilter = Payee.objects
        if not isNullBlank(schOfficeID):
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            if int(schOfficeID) not in officeIDs:
                logger.error(
                    "You don't have permission to access to this office. ID=" % schOfficeID)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            payeeFilter = payeeFilter.filter(office=schOfficeID)
        elif not self.isAdministrator():
            # limit the office
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            payeeFilter = payeeFilter.filter(office__in=officeIDs)
        if isNotNullBlank(schContent):
            schContent = schContent.strip()
            payeeFilter = payeeFilter.filter(Q(payee__icontains=schContent)
                                             | Q(bank_info__icontains=schContent)
                                             | Q(rmk__icontains=schContent))
        return payeeFilter.order_by('office__name', 'payee')

    def save(self):
        payee_rcs = self.getRequestData().get('payeeFg')
        user_office = get_user_offices(self.getCurrentUser())
        for rc in payee_rcs:
            rc: Payee

            if rc.ik_is_status_delete():
                continue
            if isNullBlank(rc.office_id) and len(user_office) == 1:
                rc.office_id = user_office[0].id
                
        return super()._BIFSave()


class ES001C(ESAPIView):
    """ES001C - Finance Personnel
    """

    def getFpRcs(self):
        """Get Finance Personnel records"""
        queryData = self.getSearchData(fieldGroupName='schFg')
        schOfficeID = queryData.get('schOffice', None) if queryData else None
        schDefault = queryData.get('schDefault', None) if queryData else None
        schContent = queryData.get('schContent', None) if queryData else None
        fpFilter = Accounting.objects
        if isNotNullBlank(schOfficeID):
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            if int(schOfficeID) not in officeIDs:
                logger.error(
                    "You don't have permission to access to this office. ID=" % schOfficeID)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            fpFilter = fpFilter.filter(office=schOfficeID)
        elif not self.isAdministrator():
            # limit office
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            fpFilter = fpFilter.filter(office__in=officeIDs)
        if isNotNullBlank(schDefault):
            fpFilter = fpFilter.filter(is_default=True if schDefault == 'Y' else False)
        if isNotNullBlank(schContent):
            schContent = schContent.strip()
            fpFilter = fpFilter.filter(Q(usr__usr_nm__icontains=schContent)
                                       | Q(rmk__icontains=schContent))
        # update the display fields, please reference to screen definition.
        fpRcs = fpFilter.order_by('office__name', 'usr__usr_nm')
        for rc in fpRcs:
            rc.usr_id = rc.usr.usr_nm
        return fpRcs

    # overwrite
    def _BIFSave(self):
        fpRcs = self.getRequestData().get('fpFg')
        defaultFPs = {}
        for rc in fpRcs:
            rc: Accounting

            if rc.ik_is_status_delete():
                continue

            if isNotNullBlank(rc.usr_id):
                userRc = User.objects.filter(
                    usr_nm=str(rc.usr_id).strip()).first()
                if not userRc:
                    return IkErrJsonResponse(message="User [%s] doesn't exist. Please check." % rc.usr_id)
                rc.usr = userRc

            if rc.is_default:
                if rc.office.id in defaultFPs.keys():
                    return IkErrJsonResponse(message="Each office only allow has one default finance person. Please check the office [%s]." % rc.office.name)
                defaultFPs[rc.office.id] = rc.usr.id
        return super()._BIFSave()


class ES001D(ESAPIView):
    """ES001D - Approver
    """

    def getApproverRcs(self):
        """Get Approver records"""
        queryData = self.getSearchData(fieldGroupName='schFg')
        schOfficeID = queryData.get('schOffice', None) if queryData else None
        schContent = queryData.get('schContent', None) if queryData else None
        fpFilter = Approver.objects
        if isNotNullBlank(schOfficeID):
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            if int(schOfficeID) not in officeIDs:
                logger.error(
                    "You don't have permission to access to this office. ID=" % schOfficeID)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            fpFilter = fpFilter.filter(office=schOfficeID)
        elif not self.isAdministrator():
            # limit office
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            fpFilter = fpFilter.filter(office__in=officeIDs)
        if isNotNullBlank(schContent):
            schContent = schContent.strip()
            fpFilter = fpFilter.filter(Q(claimer__usr_nm__icontains=schContent)
                                       | Q(claimer_grp__grp_nm__icontains=schContent)
                                       | Q(approver__usr_nm__icontains=schContent)
                                       | Q(approver_grp__grp_nm__icontains=schContent)
                                       | Q(approver_assistant__usr_nm__icontains=schContent)
                                       | Q(approver_assistant_grp__grp_nm__icontains=schContent)
                                       | Q(approver2__usr_nm__icontains=schContent)
                                       | Q(approver2_grp__grp_nm__icontains=schContent)
                                       | Q(rmk__icontains=schContent))
        # update the display fields, please reference to screen definination.
        fpRcs = fpFilter.order_by('office__name', 'claimer__usr_nm', 'claimer_grp__grp_nm', 'approver__usr_nm')
        for rc in fpRcs:
            # claimer
            if rc.claimer is not None:
                rc.claimer_id = rc.claimer.usr_nm
            if rc.claimer_grp is not None:
                rc.claimer_grp_id = rc.claimer_grp.grp_nm
            # approver
            if rc.approver is not None:
                rc.approver_id = rc.approver.usr_nm
            if rc.approver_grp is not None:
                rc.approver_grp_id = rc.approver_grp.grp_nm
            # approver assistant
            if rc.approver_assistant is not None:
                rc.approver_assistant_id = rc.approver_assistant.usr_nm
            if rc.approver_assistant_grp is not None:
                rc.approver_assistant_grp_id = rc.approver_assistant_grp.grp_nm
            # 2nd approver
            if rc.approver2 is not None:
                rc.approver2_id = rc.approver2.usr_nm
            if rc.approver2_grp is not None:
                rc.approver2_grp_id = rc.approver2_grp.grp_nm
        return fpRcs

    # overwrite
    def _BIFSave(self):
        approverRcs = self.getRequestData().get('approverFg')
        officeApproverIDs = {}
        for rc in approverRcs:
            rc: Approver

            if rc.ik_is_status_delete():
                continue

            # Convert string name to User object. (The xxx_id is account name, need to convert to User object.)
             # 1) Claimer
            if isNotNullBlank(rc.claimer_id):
                userRc = User.objects.filter(
                    usr_nm=str(rc.claimer_id).strip()).first()
                if not userRc:
                    return IkErrJsonResponse(message="Claimer [%s] doesn't exist. Please check." % rc.claimer_id)
                rc.claimer = userRc
                if UserOffice.objects.filter(office=rc.office, usr=rc.claimer).first() is None:
                    return IkErrJsonResponse(message="Claimer [%s] doesn't exist in office [%s]. Please check." % (rc.claimer_id, rc.office.name))
            # 2) Claimer group
            if isNotNullBlank(rc.claimer_grp_id):
                grpRc = Group.objects.filter(grp_nm=str(
                    rc.claimer_grp_id).strip()).first()
                if not grpRc:
                    return IkErrJsonResponse(message="Claimer Group [%s] doesn't exist. Please check." % rc.claimer_grp_id)
                rc.claimer_grp = grpRc
            # 3) Approver
            if isNotNullBlank(rc.approver_id):
                userRc = User.objects.filter(
                    usr_nm=str(rc.approver_id).strip()).first()
                if not userRc:
                    return IkErrJsonResponse(message="Approver [%s] doesn't exist. Please check." % rc.approver_id)
                rc.approver = userRc
            # 4) Approver group
            if isNotNullBlank(rc.approver_grp_id):
                grpRc = Group.objects.filter(grp_nm=str(
                    rc.approver_grp_id).strip()).first()
                if not grpRc:
                    return IkErrJsonResponse(message="Approver Group [%s] doesn't exist. Please check." % rc.approver_grp_id)
                rc.approver_grp = grpRc
            # 5) approver assistant
            if isNotNullBlank(rc.approver_assistant_id) and type(rc.approver_assistant_id) != int:
                userRc = User.objects.filter(usr_nm=str(
                    rc.approver_assistant_id).strip()).first()
                if not userRc:
                    return IkErrJsonResponse(message="Approver Assistant [%s] doesn't exist. Please check." % rc.approver_assistant_id)
                rc.approver_assistant = userRc
            # 6) approver assistant group
            if isNotNullBlank(rc.approver_assistant_grp_id):
                grpRc = Group.objects.filter(grp_nm=str(
                    rc.approver_assistant_grp_id).strip()).first()
                if not grpRc:
                    return IkErrJsonResponse(message="Approver Assistant Group [%s] doesn't exist. Please check." % rc.approver_assistant_grp_id)
                rc.approver_assistant_grp = grpRc
            # 7) the 2nd approver
            if isNotNullBlank(rc.approver2_id) and type(rc.approver2_id) != int:
                userRc = User.objects.filter(
                    usr_nm=str(rc.approver2_id).strip()).first()
                if not userRc:
                    return IkErrJsonResponse(message="The 2nd Approver [%s] doesn't exist. Please check." % rc.approver2_id)
                rc.approver2 = userRc
            # 8) the 2nd approver group
            if isNotNullBlank(rc.approver2_grp_id):
                grpRc = Group.objects.filter(grp_nm=str(
                    rc.approver2_grp_id).strip()).first()
                if not grpRc:
                    return IkErrJsonResponse(message="The 2nd Approver Group [%s] doesn't exist. Please check." % rc.approver2_grp_id)
                rc.approver2_grp = grpRc

            # validate
            if rc.approver is None and rc.approver_grp is None:
                return IkErrJsonResponse(message="Either an Approver or an Approver Group must be provided!")
            thisOfficeApprovers = officeApproverIDs.get(rc.office.name, [])
            approver_key = "%s-%s-%s-%s" % (
                rc.claimer.id if rc.claimer is not None else "",
                rc.claimer_grp.id if rc.claimer_grp is not None else "",
                rc.approver.id if rc.approver is not None else "",
                rc.approver_grp.id if rc.approver_grp is not None else "")
            if approver_key in thisOfficeApprovers:
                return IkErrJsonResponse(message="Approver is unique in an office. Plelse check office [%s]. Approver [%s], approver group [%s]."
                                         % (rc.office.name, rc.approver.usr_nm if rc.approver is not None else "", rc.approver_grp.grp_nm if rc.approver_grp is not None else ""))
            thisOfficeApprovers.append(approver_key)
            officeApproverIDs[rc.office.name] = thisOfficeApprovers
            # approver assistant
            if rc.approver_assistant is not None and rc.approver is not None and rc.approver_assistant.id == rc.approver.id:
                return IkErrJsonResponse(message="Approver Assistant cannot the same as Approver. Plelse check approver [%s]." % rc.approver.usr_nm)
            if rc.approver_assistant_grp is not None and rc.approver_grp is not None and rc.approver_assistant_grp == rc.approver_grp.id:
                return IkErrJsonResponse(message="Approver Assistant Group cannot the same as Approver Group. Plelse check approver [%s]." % rc.approver_grp.grp_nm)
            # 2nd approver
            if rc.approver2 is not None:
                if rc.approver2.id == rc.approver.id:
                    return IkErrJsonResponse(message="The 2nd Approver [%s] Cannot be the same as the first approver. Please check." % rc.approver2.usr_nm)
                elif rc.approver2_min_amount is None:
                    return IkErrJsonResponse(message="The second approver's minimum approved limit is mandatory. Please check the second approver [%s] in office [%s]."
                                             % (rc.approver2.usr_nm, rc.office.name))
            if rc.approver2 is None and isNotNullBlank(rc.approver2_min_amount):
                return IkErrJsonResponse(message="The second approver's minimum approved limit should be empty when the second approver is blank. Please check approver [%s] in office [%s]."
                                         % (rc.approver.usr_nm, rc.office.name))
            if (type(rc.approver2_min_amount) == int or type(rc.approver2_min_amount) == float) and rc.approver2_min_amount <= 0:
                return IkErrJsonResponse(message="The second approver's minimum approved limit should be greater than 0. Please check the second approver [%s] in office [%s]."
                                         % (rc.approver2.usr_nm, rc.office.name))
        return super()._BIFSave()


class ES001E(ESAPIView):
    """ES001E - Petty Expense
        # TODO: validate the admin is belong to selected office or not
    """

    def getPettyAdminRcs(self):
        """Get Approver records"""
        query_data = self.getSearchData(fieldGroupName='schFg')
        sch_office_id = query_data.get(
            'schOffice', None) if query_data else None
        sch_content = query_data.get(
            'schContent', None) if query_data else None
        fp_filter = PettyCashExpenseAdmin.objects
        if isNotNullBlank(sch_office_id):
            office_ids = [item['id'] for item in self.getOfficeRcs()]
            if int(sch_office_id) not in office_ids:
                logger.error(
                    "You don't have permission to access to this office. ID=" % sch_office_id)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            fp_filter = fp_filter.filter(office=sch_office_id)
        elif not self.isAdministrator():
            # limit office
            office_ids = [item['id'] for item in self.getOfficeRcs()]
            fp_filter = fp_filter.filter(office__in=office_ids)
        if isNotNullBlank(sch_content):
            schContent = schContent.strip()
            fp_filter = fp_filter.filter(Q(admin__usr_nm__icontains=sch_content)
                                         | Q(admin_payee__payee__icontains=sch_content)
                                         | Q(rmk__icontains=sch_content))
        # update the display fields, please reference to screen definination.
        fpRcs = fp_filter.order_by('office__name', 'admin__usr_nm')
        for rc in fpRcs:
            rc.admin_id = rc.admin.usr_nm
            rc.admin_payee_id = rc.admin_payee.payee
        return fpRcs

    # overwrite
    def _BIFSave(self):
        petty_admin_rcs = self.getRequestData().get('pettyAdminFg')
        office_petty_admin_ids = {}
        for rc in petty_admin_rcs:
            rc: PettyCashExpenseAdmin

            if rc.ik_is_status_delete():
                continue

            if PettyCashExpenseAdmin(rc.admin_id):
                user_rc = User.objects.filter(
                    usr_nm=str(rc.admin_id).strip()).first()
                if not user_rc:
                    return IkErrJsonResponse(message="Admin [%s] doesn't exist. Please check." % rc.admin_id)
                rc.admin = user_rc
            if PettyCashExpenseAdmin(rc.admin_payee_id):
                payee_rc = Payee.objects.filter(
                    office=rc.office, payee=str(rc.admin_payee_id).strip()).first()
                if not payee_rc:
                    return IkErrJsonResponse(message="Payee [%s] doesn't exist. Please check office [%s]." % (rc.admin_payee_id, rc.office.name))
                rc.admin_payee = payee_rc

            admin_ids = office_petty_admin_ids.get(rc.office.id, [])
            if rc.admin_payee.id in admin_ids:
                return IkErrJsonResponse(message="Petty Admin is unique. Please check office [%s], administrator [%s]." % (rc.office.name, rc.admin.usr_nm))
            admin_ids.append(rc.admin_payee.id)
            office_petty_admin_ids[rc.office.id] = admin_ids

        return super()._BIFSave()


class ES001F(ESAPIView):
    """ES001F - User Roles
    """

    def getUserRoleRcs(self):
        user_role_rcs = UserRole.objects.order_by('usr__usr_nm', 'office__name')
        # update display columns
        for rc in user_role_rcs:
            if rc.usr is not None:
                rc.usr_id = rc.usr.usr_nm
            if rc.usr_grp is not None:
                rc.usr_grp_id = rc.usr_grp.grp_nm
            if rc.target_usr is not None:
                rc.target_usr_id = rc.target_usr.usr_nm
            if rc.target_usr_grp is not None:
                rc.target_usr_grp_id = rc.target_usr_grp.id
        return user_role_rcs

    def getRoles(self):
        return [{'value': item[0], 'name': item[1]} for item in UserRole.ROLE_CHOICES]

    # overwrite
    def _BIFSave(self):
        user_role_rcs = self.getRequestData().get('userRoleFg')
        row_keys = set()
        for rc in user_role_rcs:
            rc: UserRole
            if not rc.ik_is_status_delete():
                # validate "User" column
                user_name = rc.usr_id  # reference to screen definition
                user_rc = None
                if isNotNullBlank(user_name):
                    user_rc = User.objects.filter(usr_nm=user_name).first()
                    if user_rc is None:
                        raise IkValidateException(
                            "User [%s] doesn't exist." % user_name)
                rc.usr = user_rc

                # validate "Group" column
                group_name = rc.usr_grp_id  # reference to screen definition
                group_rc = None
                if isNotNullBlank(group_name):
                    group_rc = Group.objects.filter(grp_nm=group_name).first()
                    if group_rc is None:
                        raise IkValidateException(
                            "Group [%s] doesn't exist." % group_rc)
                rc.usr_grp = group_rc

                if rc.usr is None and rc.usr_grp is None:
                    raise IkValidateException(
                        "User and User Group cannot both be blank at the same time.")

                # office
                office_id = rc.office.id if rc.office is not None else None

                # validate target user
                target_user_name = rc.target_usr_id  # reference to screen definition
                if isNotNullBlank(target_user_name):
                    target_user_rc = User.objects.filter(
                        usr_nm=target_user_name).first()
                    if target_user_rc is None:
                        raise IkValidateException(
                            "Target User [%s] doesn't exist." % target_user_name)
                    rc.target_usr = target_user_rc
                else:
                    rc.target_usr = None

                # validate target user group
                target_user_group_name = rc.target_usr_grp_id  # reference to screen definition
                target_group_rc = None
                if isNotNullBlank(target_user_group_name):
                    target_group_rc = Group.objects.filter(grp_nm=target_user_group_name).first()
                    if target_group_rc is None:
                        raise IkValidateException(
                            "Group [%s] doesn't exist." % target_user_group_name)
                rc.target_usr_grp = target_group_rc

                # unique check
                row_key = '%s`%s`%s`%s`%s`%s' % (rc.usr.usr_nm if rc.usr is not None else "",
                                                 rc.usr_grp.grp_nm if rc.usr_grp is not None else "",
                                                 rc.office.name if rc.office is not None else "",
                                                 rc.target_usr.usr_nm if rc.target_usr is not None else "",
                                                 rc.target_usr_grp.grp_nm if rc.target_usr_grp is not None else "",
                                                 rc.prj_nm if rc.prj_nm is not None else "")
                if row_key in row_keys:
                    raise IkValidateException("User, User Group, Office, Target User, Target User group are unique. User=[%s], User Group=[%s], Office=[%s], Target User=[%s], Target User Group=[%s], Project=[%s]."
                                              % (rc.usr.usr_nm if rc.usr is not None else None,
                                                 rc.usr_grp.grp_nm if rc.usr_grp is not None else None,
                                                 rc.office.name if rc.office is not None else None,
                                                 rc.target_usr.usr_nm if rc.target_usr is not None else None,
                                                 rc.target_usr_grp.grp_nm if rc.target_usr_grp is not None else None,
                                                 rc.prj_nm if rc.prj_nm is not None else None))
                row_keys.add(row_key)

                # project
                if isNullBlank(rc.prj_nm):
                    rc.prj_nm = None
                else:
                    rc.prj_nm = rc.prj_nm.strip()
                # description
                if isNullBlank(rc.dsc):
                    rc.dsc = None
                else:
                    rc.dsc = rc.dsc.strip()
        return super()._BIFSave()


class ES001G(ESAPIView):
    """ES001G - Settings
    """

    def getSettingRcs(self):
        return Setting.objects.filter(Q(cd=const.APP_CODE) & Q(Q(key=setting.ALLOW_ACCOUNTING_TO_REJECT) | Q(key=setting.ENABLE_DEFAULT_EMAIL_NOTIFICATION)
                                                               | Q(key=setting.ENABLE_DEFAULT_INBOX_NOTIFICATION) | Q(key=setting.ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL))).order_by('key')

    # overwrite
    def _BIFSave(self):
        setting_rcs = self.getRequestData().get('settingFg')
        change_logs = []
        for rc in setting_rcs:
            rc: Setting
            if rc.key in (setting.ALLOW_ACCOUNTING_TO_REJECT, setting.setting.ENABLE_DEFAULT_EMAIL_NOTIFICATION, setting.ENABLE_DEFAULT_INBOX_NOTIFICATION, setting.ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL):
                if rc.ik_is_status_modified():
                    value = rc.value
                    if isNullBlank(value):
                        raise IkValidateException("Value is mandatory for name [%s]." % rc.key)
                    value = value.strip().lower()
                    if value not in ['true', 'false']:
                        raise IkValidateException("Value should be 'true' or 'false' for name [%s]." % rc.key)
                    rc.value = value
                    # validate the settings
                    db_setting_rc = Setting.objects.filter(Q(cd=const.APP_CODE) & Q(key=rc.key)).first()
                    if db_setting_rc is not None:
                        if db_setting_rc.value != rc.value:
                            # add logs
                            change_logs.append("%s change the key [%s] value from [%s] to [%s]" % (self.getCurrentUserName(), rc.key, db_setting_rc.value, value))
                    if isNullBlank(rc.rmk):
                        rc.rmk = None
                    else:
                        rc.rmk = rc.rmk.strip()
                elif rc.ik_is_status_delete():
                    raise IkValidateException("You don't have permission to delete the setting records.")
        b = super()._BIFSave()
        if b.isSuccess():
            for log_str in change_logs:
                logger.info(log_str)
        return b
