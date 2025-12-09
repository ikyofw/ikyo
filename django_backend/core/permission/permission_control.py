import logging

from ..core.exception import *
from ..models import PermissionControl, PermissionControlUser
from ..utils.lang_utils import isNotNullBlank, isNullBlank

logger = logging.getLogger('ikyo')


def is_exists(name: str, user_id: int) -> bool:
    if isNullBlank(name):
        raise IkValidateException("Group name is mandatory!")

    rc = PermissionControl.objects.filter(name=name).first()
    if isNullBlank(rc):
        logger.error("Permission Control does not exists. - %s" % name)
        return False
    return isNotNullBlank(PermissionControlUser.objects.filter(permission_control=rc, user_id=user_id).first())
