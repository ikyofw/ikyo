from django.db.models import Q

from core.core.exception import IkValidateException
from core.log.logger import logger
from core.models import Setting
from core.utils.langUtils import isNullBlank

from ..core import const, setting
from .es_base_views import ESAPIView


class ES001G(ESAPIView):
    """ES001G - Settings
    """

    def getSettingRcs(self):
        return Setting.objects.filter(Q(cd=const.APP_CODE) & Q(Q(key=setting.ALLOW_ACCOUNTING_TO_REJECT) | Q(key=setting.ENABLE_DEFAULT_INBOX_NOTIFICATION)
                                                               | Q(key=setting.ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL))).order_by('key')

    # overwrite
    def _BIFSave(self):
        setting_rcs = self.getRequestData().get('settingFg')
        change_logs = []
        for rc in setting_rcs:
            rc: Setting
            if rc.key in (setting.ALLOW_ACCOUNTING_TO_REJECT, setting.ENABLE_DEFAULT_INBOX_NOTIFICATION, setting.ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL):
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
