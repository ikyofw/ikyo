from threading import Lock

import core.user.userManager as UserManager
from core.db.transaction import IkTransaction
from core.log.logger import logger
from core.models import Setting

from . import const

# Lock to ensure thread-safe initialization of settings
__INIT_LOCK = Lock()

# Setting name for allowing accounting to reject expenses and cash advances
ALLOW_ACCOUNTING_TO_REJECT = "Allow accounting to reject expenses and cash advances"

# Setting name for enabling default email notification
ENABLE_DEFAULT_EMAIL_NOTIFICATION = "Enable email notification"

# Setting name for enabling default inbox notification
ENABLE_DEFAULT_INBOX_NOTIFICATION = "Enable inbox notification"

# Setting name for enabling default inbox notification
ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL = "Enable automatic settlement upon approval"


def is_accounting_rejectable() -> bool:
    """
    Check if accounting is allowed to reject expenses and cash advances.

    Returns:
        bool: True if accounting rejection is allowed, otherwise False.
    """
    return __get_bool_setting(ALLOW_ACCOUNTING_TO_REJECT, True)


def is_enable_email_notification() -> bool:
    return __get_bool_setting(ENABLE_DEFAULT_EMAIL_NOTIFICATION, True)


def is_enable_default_inbox_message() -> bool:
    return __get_bool_setting(ENABLE_DEFAULT_INBOX_NOTIFICATION, True)


def is_enable_automatic_settlement_upon_approval() -> bool:
    return __get_bool_setting(ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL, True)


def __get_bool_setting(name: str, default_value: bool = False) -> bool:
    """
    Retrieve the value of a boolean setting from the database.

    Args:
        name (str): The name of the setting.
        default_value (bool): The default value to return if the setting is not found or invalid.

    Returns:
        bool: The value of the setting, or the default value if not found or invalid.
    """
    rc = Setting.objects.filter(cd=const.APP_CODE, key=name).first()
    if rc is None:
        logger.warning("Setting [%s] doesn't exist." % (name))
    if rc.value is None:
        # Return the default value
        return default_value
    value = rc.value.strip().lower()
    if value not in ['true', 'false']:
        logger.error(
            "Setting [%s]'s value should be \"true\" or \"false\"." % (name))
        return default_value
    return value == 'true'


def init_settings() -> None:
    """
    Initialize default settings in the database.
    Ensures that required settings are present with default values.
    """
    __INIT_LOCK.acquire()
    try:
        __add_setting(ALLOW_ACCOUNTING_TO_REJECT, 'true',
                      "Options: true, false. Default is true.")
        __add_setting(ENABLE_DEFAULT_EMAIL_NOTIFICATION, 'true',
                      "Options: true, false. Default is true.")
        __add_setting(ENABLE_DEFAULT_INBOX_NOTIFICATION, 'true',
                      "Options: true, false. Default is true.")
        __add_setting(ENABLE_AUTOMATIC_SETTLEMENT_UPON_APPROVAL, 'true',
                      "Options: true, false. Default is true.")
    finally:
        __INIT_LOCK.release()


def __add_setting(name: str, default_value: str, description: str) -> None:
    """
    Add a new setting to the database if it does not already exist.

    Args:
        name (str): The name of the setting.
        default_value (str): The default value of the setting.
        description (str): A description of the setting.
    """
    try:
        rc = Setting.objects.filter(cd=const.APP_CODE, key=name).first()
        if rc is None:
            # Create the setting if it doesn't exist
            rc = Setting(cd=const.APP_CODE, key=name,
                         value=default_value, rmk=description)
            trn = IkTransaction(userID=UserManager.SYSTEM_USER_ID)
            trn.add(rc)
            b = trn.save()
            if b.value:
                logger.info("Add setting success: name=%s, default value=%s" % (
                    name, default_value))
            else:
                logger.error("Add setting failed: name=%s, default value=%s, error=%s" % (
                    name, default_value, b.dataStr))
    except Exception as e:
        logger.error("Add setting failed: name=%s, default value=%s, exception=%s" % (
            name, default_value, str(e)))
    except Exception as e:
        logger.error("Add setting failed: name=%s, default value=%s, exception=%s" % (
            name, default_value, str(e)))
