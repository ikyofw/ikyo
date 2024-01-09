import logging
from core.models import Setting

logger = logging.getLogger('ikyo')

DEFAULT_SETTING_CODE = 'IKYO'


class __SystemSetting:
    serverProperties = None

    def __init__(self):
        pass

    def _init(self, serverProperties):
        self.serverProperties = serverProperties

    def get(self, name: str, code: str = DEFAULT_SETTING_CODE, default: str = None) -> str:
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
        return s.lower() == "true" if s is not None else False

    def getInteger(self, name: str, code: str = DEFAULT_SETTING_CODE, default: int = None) -> int:
        v = self.get(name, code, default)
        return int(v) if v else None


SystemSetting = __SystemSetting()
