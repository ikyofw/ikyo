import os
from .db.db import executeSqlFiles
from .ui.ui import IkUI
from .log.logger import logger
from .cron.cron_manager import get_manager; cron_mgr = get_manager()
from iktools import IK_CONFIG

__hasInit = False

def init_ik():
    global __hasInit
    if __hasInit:
        return
    __hasInit = True

    try:
        logger.info('Initialize SQL files ...')
        executeSqlFiles()
        logger.info('Initialize SQL files.')
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.info('System is shutting down caused by previous error.')
        os._exit(0)

    # Load screens.
    logger.info('Initialize UI ...')
    IkUI.refresh()
    logger.info('Initialized UI.')

    # start cron task
    if IK_CONFIG.getSystem(name='enableCron', defaultValue='false').lower() == 'true':
        logger.info('Init cron tasks ...')
        cron_mgr.start()
        logger.info('Init cron tasks completed')
    else:
        logger.info('Cron disabled.')
