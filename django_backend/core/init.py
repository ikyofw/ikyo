import logging
import os

logger = logging.getLogger('backend')

__hasInit = False


def initIk():
    global __hasInit
    if __hasInit:
        return
    __hasInit = True

    try:
        pass
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.info('System is shutting down caused by previous error.')
        os._exit(0)
