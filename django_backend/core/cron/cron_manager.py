'''
    2022-11-23

APS Scheduler
    https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html#module-apscheduler.triggers.cron
    https://coderslegacy.com/python/apscheduler-tutorial-advanced-scheduler/

    Values: (https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html#module-apscheduler.triggers.cron)
        year (int|str) - 4-digit year
        month (int|str) - month (1-12)
        day (int|str) - day of month (1-31)
        week (int|str) - ISO week (1-53)
        day_of_week (int|str) - number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
        hour (int|str) - hour (0-23)
        minute (int|str) - minute (0-59)
        second (int|str) - second (0-59)
        start_date (datetime|str) - earliest possible date/time to trigger on (inclusive)
        end_date (datetime|str) - latest possible date/time to trigger on (inclusive)
        timezone (datetime.tzinfo|str) - time zone to use for the date/time calculations (defaults to scheduler timezone)
        jitter (int|None) - delay the job execution by jitter seconds at most

'''

import time
import logging
from typing import Optional
from importlib import import_module
from datetime import datetime
from threading import Lock, Thread
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from ..models import CronJob

logger = logging.getLogger(__name__)
REFRESH_JOB_INTERVAL = 10
'''
    Refresh database tasks interval in second(s). Default is 10 seconds.
'''

class JobData:
    def __init__(self, cron_job: CronJob, job: Job) -> None:
        self.__cron_job = cron_job
        self.__job = job
        self.__date = datetime.now()

    @property
    def cron_job(self) -> CronJob:
        return self.__cron_job

    @property
    def job(self) -> Job:
        return self.__job

    @property
    def date(self) -> datetime:
        return self.__date


class __CronManager:
    def __init__(self) -> None:
        self.__sched = BackgroundScheduler()
        self.__schedLock = Lock()
        self.__is_running = False
        self.__currentJobs = {}
        self.__refreshInterval = REFRESH_JOB_INTERVAL
        '''
            {cron_job.id, JobData}
        '''
        # refresh the tasks in the backuground
        def refresh_in_background():
            while True:
                if self.is_running():
                    self.__refresh()
                time.sleep(self.__refreshInterval)
        t = Thread(target=refresh_in_background, args=(), name='Cron Manager Refresh Thread', daemon=True)
        t.start()

    def is_running(self) -> bool:
        return self.__is_running

    def start(self):
        with self.__schedLock:
            if not self.__is_running:
                logger.info('Starting cron schedule ...')
                self.__sched = BackgroundScheduler()
                self.__is_running = True
                self.__sched.start()
                logger.info('Starting cron schedule done')
    
    def stop(self):
        with self.__schedLock:
            if self.__is_running:
                logger.info('Stopping cron schedule ...')
                self.__sched.shutdown(wait=True)
                self.__is_running = False
                logger.info('Stopping cron schedule done')

    @property
    def refresh_job_interval(self) -> int:
        '''
            return (int): seconds
        '''
        return self.__refreshInterval

    def set_refresh_job_interval(self, interval) -> None:
        '''
            interval (int): seconds
        '''
        if interval < 0:
            raise Exception('Interval cannot less than 0.')
        self.__refreshInterval = interval

    def __refresh(self) -> bool:
        logger.debug('Refreshing jobs ...')
        with self.__schedLock:
            try:
                # get jobs from database
                logger.debug('Get jobs from database ...')
                cron_jobs = CronJob.objects.filter().order_by('id')
                logger.debug('Get %s jobs from database.' % len(cron_jobs))
                previous_job_ids = list(self.__currentJobs.keys())
                # 3.2 run the enabled jobs
                newJobs = 0
                errorJobs = 0
                disableJobs = 0
                updatedJobs = 0
                del_job_count = 0
                exists_job_ids = []
                for cj in cron_jobs:
                    rst = self.__add_schedule_task(cj)
                    if rst == 'added':
                        newJobs += 1
                    elif rst == 'updated':
                        updatedJobs += 1
                    elif rst == 'disabled':
                        disableJobs += 1
                    elif rst == 'error':
                        errorJobs += 1
                    exists_job_ids.append(cj.id)
                
                for job_id in previous_job_ids:
                    if job_id not in exists_job_ids:
                        # job is not exists in database, then remove it
                        job_data = self.__currentJobs[job_id]
                        job_data : JobData
                        logger.info('ID=%s, Task=%s is not exists in database, then remove it.' % (job_id, job_data.cron_job.task))
                        self.__sched.remove_job(job_data.job.id)
                        del self.__currentJobs[job_id]
                        del_job_count += 1
                logger.debug('Total %s jobs found. new=%s, updated=%s, failed=%s, disabled=%s, deleted=%s.' % (len(cron_jobs), newJobs, updatedJobs, errorJobs, disableJobs, del_job_count))
                #self.start()
                return True
            except Exception as e:
                logger.error(e)
                logger.error('Refresh cron task failed: %s.' % str(e))
                return False
    
    def __add_schedule_task(self, cron_job : CronJob) -> str:
        '''
            cron_job (CronJob)
            return error, added, updated, disabled. None means no change
        '''
        LG = 'ID=%s, Task=%s ' % (cron_job.id, cron_job.task) # logger header
        returnValue = None
        try:
            # 1. check the task is exists or not
            if cron_job.id in self.__currentJobs.keys():
                # This job is exists
                jobData = self.__currentJobs[cron_job.id]
                jobData : JobData
                if not cron_job.enable:
                    # job disabled
                    logger.info(LG + 'Disabled')
                    self.__sched.remove_job(jobData.job.id)
                    del self.__currentJobs[cron_job.id]
                elif self.__is_job_updated(jobData.cron_job, cron_job):
                    # task changed, then remove the old task first
                    logger.info(LG + 'Updated, going to remove the old job and then create a new job')
                    self.__sched.remove_job(jobData.job.id)
                    del self.__currentJobs[cron_job.id]
                    returnValue = 'updated'
                else:
                    # no change
                    return None
            if not cron_job.enable:
                returnValue = 'disabled'
            else:
                task = cron_job.task
                if task is None or task.strip() == '':
                    logger.error(LG + 'Task cannot be empty.')
                    return None
                if '.' not in task:
                    logger.error(LG + 'Task format is incorrect. It should be [model.]fileName.functionName.')
                    return None
                # reverse the string
                rev_task = task[::-1]
                # get last index of the req. character 
                i = len(rev_task) - rev_task.index(".") - 1
                modelName, fnName = task[0:i], task[i + 1 :]
                importedModel = import_module(modelName)
                jobFn = getattr(importedModel, fnName)

                args = []
                if cron_job.args is not None and cron_job.args.strip() != '':
                    argStr = cron_job.args.strip()
                    args = self.__get_job_paramters(argStr)

                logger.info(LG + 'Add job ...')
                job = self.__sched.add_job(jobFn, 'cron',
                            second = cron_job.second,
                            minute = cron_job.minute,
                            hour = cron_job.hour,
                            day = cron_job.day,
                            week = cron_job.week,
                            day_of_week = cron_job.day_of_week,
                            month = cron_job.month,
                            year = cron_job.year,
                            start_date = cron_job.start_date,
                            end_date = cron_job.end_date,
                            jitter = cron_job.jitter,
                            args = args)
                self.__currentJobs[cron_job.id] = JobData(cron_job, job)
                logger.info(LG + 'Added')
                if returnValue is None:
                    returnValue = 'added'
        except Exception as e:
            logger.error(e)
            logger.error(f'{LG}Error={str(e)}')
            returnValue = 'error'
        return returnValue


    def __is_job_updated(self, old_cron_job: CronJob, new_cron_job: CronJob) -> bool:
        '''
            old_cron_job (CronJob)
            new_cron_job (CronJob)
            return True if changed
        '''
        return self.__is_not_the_same(old_cron_job.second, new_cron_job.second) \
                or self.__is_not_the_same(old_cron_job.minute, new_cron_job.minute) \
                or self.__is_not_the_same(old_cron_job.hour, new_cron_job.hour) \
                or self.__is_not_the_same(old_cron_job.day, new_cron_job.day) \
                or self.__is_not_the_same(old_cron_job.week, new_cron_job.week) \
                or self.__is_not_the_same(old_cron_job.day_of_week, new_cron_job.day_of_week) \
                or self.__is_not_the_same(old_cron_job.month, new_cron_job.month) \
                or self.__is_not_the_same(old_cron_job.year, new_cron_job.year) \
                or self.__is_not_the_same(old_cron_job.start_date, new_cron_job.start_date) \
                or self.__is_not_the_same(old_cron_job.end_date, new_cron_job.end_date) \
                or self.__is_not_the_same(old_cron_job.jitter, new_cron_job.jitter) \
                or self.__is_not_the_same(old_cron_job.task, new_cron_job.task) \
                or self.__is_not_the_same(old_cron_job.args, new_cron_job.args)

    def __is_not_the_same(self, a, b) -> bool:
        if a is not None and type(a) == str and a.strip() == '':
            a = None
        if b is not None and type(b) == str and b.strip() == '':
            b = None
        return a != b

    def __get_job_paramters(self, args) -> list:
        '''
            '"a1 a2" bb     "c1"" c2" dd' -> ['a1 a2', 'bb', 'c1" c2', 'dd']

            'aa 22 cc    ' -> ['aa', '22', 'cc']
        '''
        arr = []
        p = ''
        doubleQuotationStart=False
        ignore = False
        for i in range(len(args)):
            if ignore:
                ignore = False
                continue
            c = args[i]
            if c == ' ':
                if doubleQuotationStart:
                    p += c
                elif p != '':
                    arr.append(p) # the end
                    p = ''
            elif c == '"':
                if doubleQuotationStart:
                    # check the next character if exists
                    if i < len(args) - 1:
                        if args[i + 1] == '"':
                            p += '"'
                            ignore = True
                    if not ignore:
                        arr.append(p) # the end
                        doubleQuotationStart = False
                        p = ''
                else:
                    doubleQuotationStart = True # start
                    p = ''
            else:
                p += c
        if doubleQuotationStart:
            raise Exception('Parameter format is incorrect: %s' % args)
        if p != '':
            arr.append(p)
        return arr



# allow to create on instance only
_manager: Optional[__CronManager] = None
_manager_lock = Lock()

def get_manager() -> __CronManager:
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = __CronManager()
    return _manager