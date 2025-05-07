import logging
from core.models import Setting
from core.core.exception import IkException

logger = logging.getLogger('ikyo')

DEFAULT_SETTING_CODE = 'IKYO'


class __SystemSetting:
    """
        Update the Setting model.
    """

    def get(self, name: str, code: str = DEFAULT_SETTING_CODE, default: any = None) -> str:
        '''
            get value from ik_setting table
        '''
        if not code:
            code = DEFAULT_SETTING_CODE
        if not name:
            return None
        rc = Setting.objects.filter(cd=code).filter(key=name).first()
        v = None if rc is None else rc.value
        if v is None:
            v = default
        return v

    def getBoolean(self, name: str, code: str = DEFAULT_SETTING_CODE, default: bool = None) -> bool:
        s = self.get(name, code, default)
        if type(s) == bool:
            return s
        return str(s).lower() == "true" if s is not None else False

    def getInteger(self, name: str, code: str = DEFAULT_SETTING_CODE, default: int = None) -> int:
        v = self.get(name, code, default)
        if type(v) == int:
            return v
        return int(v) if v else None

    def update(self, name: str, value: any, remarks: str = None, code: str = DEFAULT_SETTING_CODE, operator_id: int = None) -> Setting:
        """Update the Setting model. If record doesn't exist, then create a new one.

        Return:
            record id if success.
        """
        if not code:
            code = DEFAULT_SETTING_CODE
        if not name:
            return None
        if value is not None and type(value) != str:
            value = str(value)
        rc = Setting.objects.filter(cd=code).filter(key=name).first()
        updated = False
        isNew = False
        if rc is not None:
            if rc.value != value or rc.rmk != remarks:
                rc.value = value
                rc.rmk = remarks
                updated = True
        else:
            isNew = True
            rc = Setting(cd=code, key=name, value=value, rmk=remarks)
        if updated or isNew:
            from core.db.transaction import IkTransaction
            trn = IkTransaction()
            if updated:
                trn.modify(rc)
            elif isNew:
                trn.add(rc)
            b = trn.save(operatorId=operator_id)
            if not b.value:
                raise IkException(b.data)
        return rc

    def delete(self, name: str, code: str = DEFAULT_SETTING_CODE, operator_id: int = None) -> Setting:
        if not code:
            code = DEFAULT_SETTING_CODE
        if not name:
            return None
        rc = Setting.objects.filter(cd=code).filter(key=name).first()
        if rc is not None:
            from core.db.transaction import IkTransaction
            trn = IkTransaction()
            trn.delete(rc)
            b = trn.save(operatorId=operator_id)
            if not b.value:
                raise IkException(b.data)
        return rc


SystemSetting = __SystemSetting()
