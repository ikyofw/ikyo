from datetime import datetime
from ..log.logger import logger

def JobExample01(prm1, prm2, prm3):
    '''
        Job SQL: INSERT INTO ik_cron_job(cre_usr_id,verson_no,second,task,args,enable,dsc) 
                values(-1, 0, '*/5', 'core.cron.examples.JobExample01', 'aa bb cc', true, 'Cron example job 01: run every 5 seconds');
        prm1 = aa
        prm2 = bb
        prm3 = cc
    '''
    ts = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
    logger.info('%s JobExample01 Parameters: prm1=%s, prm2=%s, prm3=%s' % (ts, prm1, prm2, prm3))


def JobExample02():
    '''
        Job SQL: INSERT INTO ik_cron_job(cre_usr_id,version_no,second,task,args,enable,dsc) 
                values(-1, 0, '0', 'core.cron.examples.JobExample02', NULL, true, 'Cron example job 02: run at 0 second');
    '''
    ts = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
    logger.info('%s JobExample02' % (ts))