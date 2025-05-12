from core.log.logger import logger
from core.core.exception import IkValidateException
from core.utils.langUtils import isNotNullBlank, isNullBlank
from .es_base_views import ESAPIView
from ..models import User, Group, UserRole


class ES001F(ESAPIView):
    """ES001F - User Roles
    """

    def getUserRoleRcs(self):
        user_role_rcs = UserRole.objects.order_by('usr__usr_nm','office__name')
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
                user_name = rc.usr_id  # reference to screen definiatioin
                user_rc = None
                if isNotNullBlank(user_name):
                    user_rc = User.objects.filter(usr_nm=user_name).first()
                    if user_rc is None:
                        raise IkValidateException(
                            "User [%s] doesn't exist." % user_name)
                rc.usr = user_rc

                # validate "Group" column
                group_name = rc.usr_grp_id  # reference to screen definiatioin
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
                target_user_name = rc.target_usr_id  # reference to screen definiatioin
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
                target_user_group_name = rc.target_usr_grp_id  # reference to screen definiatioin
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
