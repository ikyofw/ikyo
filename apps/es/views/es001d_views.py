import json
from django.db.models import Q
from core.log.logger import logger
from core.core.exception import IkValidateException
from core.core.http import IkErrJsonResponse
from core.utils.langUtils import isNotNullBlank
from ..models import Approver, User, Group, UserOffice
from .es_base_views import ESAPIView


class ES001D(ESAPIView):
    """ES001D - Approver
    """

    def getApproverRcs(self):
        """Get Approver records"""
        queryData = self.getSearchData(fieldGroupName='schFg')
        schOfficeID = queryData.get('schOffice', None) if queryData else None
        schClaimer = queryData.get('schClaimer', None) if queryData else None
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
        if isNotNullBlank(schClaimer):
            fpFilter = fpFilter.filter(Q(claimer__usr_nm__icontains=schClaimer)
                                       | Q(claimer_grp__grp_nm__icontains=schClaimer))
        if isNotNullBlank(schContent):
            fpFilter = fpFilter.filter(Q(claimer__usr_nm__icontains=schClaimer)
                                       | Q(claimer_grp__grp_nm__icontains=schClaimer)
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
            approver_key = "%s-%s" % (rc.approver.id if rc.approver is not None else "",
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
