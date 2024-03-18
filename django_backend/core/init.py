import logging
import os
from core.db.db import executeSqlFiles
from core.ui.ui import IkUI

logger = logging.getLogger('ikyo')

__hasInit = False

def initIk():
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
