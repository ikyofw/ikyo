import logging
import os

import core.utils.db as dbUtils
from django.db import connection

OFFICE_CODE_SINGAPORE = "SG"
OFFICE_CODE_HONGKONG = "HK"
OFFICE_CODE_CHINA_WUHAN = "WH"
OFFICE_CODE_CHINA_SHENZHEN = "SZ"
OFFICE_CODE_MALAYSIA = "MY"

DEFAULT_OFFICE = OFFICE_CODE_SINGAPORE

logger = logging.getLogger('ikyo')


class SystemSetting:
    serverProperties = None

    def __init__(self):
        pass

    def init(self, serverProperties):
        self.serverProperties = serverProperties

    def getFromServerPropertiesFile(self, name: str):
        if self.serverProperties is None:
            raise ValueError("Server properties not initialized")

        return self.serverProperties.get(name) if self.serverProperties else None

    def getBoolean(self, name: str) -> bool:
        s = self.get(name)
        return s.lower() == "true" if s is not None else False

    def getInteger(self, name: str) -> int:
        v = self.get(name)
        if v is None:
            return int(self.getFromServerPropertiesFile(name))
        return int(v)

    def getMathematicaServerHost(self):
        return self.get("MATHEMATICA_HOST")

    def getMathematicaServerServicePort(self):
        return self.getInteger("MATHEMATICA_SERVICE_PORT")

    def getAcadServerHost(self):
        return self.get("AUTOCAD_SERVICE_HOST")

    def getAcadServerServicePort(self) -> int:
        return self.getInteger("AUTOCAD_SERVICE_PORT")

    def getRevitServerHost(self, office):
        key = "REVIT_SERVICE_HOSE"
        if office is not None and office.upper() != DEFAULT_OFFICE:
            key += "." + office.upper()
        return self.get(key)

    def getRevitServerServicePort(self, office):
        key = "REVIT_SERVICE_PORT"
        if office is not None and office.upper() != DEFAULT_OFFICE:
            key += "." + office.upper()
        return self.getInteger(key)

    def isSaveUserLoginPasswordHistory(self):
        return self.getBoolean("SYS-Save-User-Login-Password")

    def getSocketServicePort(self):
        port = self.get("SOCKET-SERVICE-PORT")
        return int(port) if port is not None else 9900
