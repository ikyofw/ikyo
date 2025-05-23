import os
import logging
import json
import hashlib
from threading import Lock
from datetime import datetime
from pathlib import Path
from django.db import connection
from iktools import getAppNames
from core.core.exception import IkException

logger = logging.getLogger('ikyo')


NEW_SQL_FILE_FOLDER = 'new'
PROCESSED_SQL_FILE_FOLDER = 'processed'

__EXECUTE_SQL_FILE_LOCK = Lock()


def get_sql_file_folder() -> list[Path]:
    sql_folders = []
    app_nms = getAppNames()
    for app_nm in app_nms:
        sql_folder = Path(os.path.join(app_nm, 'resources/database'))
        if sql_folder.is_dir():
            sql_folders.append(sql_folder)
    return sql_folders


def get_sql_file_file(app_nm: str, file_path: str) -> Path:
    return Path(os.path.join(app_nm, 'resources/database', file_path))


def executeSqlFiles(specifiedSqlFile: object = None) -> None:
    '''
        run the sql files in app_nm/resources/database folder if not specified
    '''
    __EXECUTE_SQL_FILE_LOCK.acquire()
    try:
        if specifiedSqlFile:
            specifiedSqlFile = Path(specifiedSqlFile)
            if not specifiedSqlFile.is_file():
                logger.error('Specified sql file [%s] is exists.' % specifiedSqlFile)

        sql_dirs = get_sql_file_folder()
        processed_file_no = 0
        for sql_dir in sql_dirs:
            if not sql_dir.is_dir():
                continue
            # 1. get sql files
            allSqlFiles = [specifiedSqlFile] if specifiedSqlFile else __getSqlFiles(sql_dir)
            if len(allSqlFiles) == 0:
                continue

            # 2. read processed files
            sqlFileData = {}
            processFile = Path(os.path.join(sql_dir.resolve(), 'sql.json'))
            if processFile.is_file():
                with open(processFile, 'r') as json_file:
                    sqlFileData = json.load(json_file)
            else:
                logger.debug('SQL process file [%s] is not exists.' % processFile.resolve())

            # 3. get the new sql files
            newSqlFiles = []
            executedSqlFiles = sqlFileData.get('executed', [])
            processedFileMD5s = {}
            for pf in executedSqlFiles:
                processedFileMD5s[pf['name']] = pf['md5']
            for f in allSqlFiles:
                fp = Path(f)
                if fp.name.startswith('_'):  # ignore the file starts with "_"
                    logger.info('Ignore sql file [%s]' % fp)
                    continue
                if fp.name not in processedFileMD5s.keys():
                    newSqlFiles.append(fp)
                elif fp.is_file():
                    fileMD5 = __fileMD5(f)
                    if fileMD5 != processedFileMD5s[fp.name]:  # file changed
                        logger.info("File [%s] changed. Please DON'T updated the executed file." % fp.name)

            # 4. process each new sql file
            if len(newSqlFiles) == 0:
                if specifiedSqlFile:
                    logger.info("Specified sql file has been executed.")
                continue
            processed_file_no += len(newSqlFiles)
            for newSqlFile in newSqlFiles:
                try:
                    # execute sql
                    # 1) read sql from file
                    sqlContent = None
                    sqlFilename = Path(newSqlFile).name
                    with open(newSqlFile, 'r', encoding='utf-8') as rf:
                        sqlContent = rf.read()
                    if not sqlContent or len(sqlContent.strip()) == 0:
                        logger.info('Sql file [%s] is empty.' % newSqlFile)
                    else:
                        # remove comment lines starts with "--"
                        lines = sqlContent.split('\n')
                        sqlContent = ''
                        for line in lines:
                            if not line.strip().startswith('--'):
                                sqlContent += '%s\n' % line
                            else:
                                logger.debug("%s ignore comment line: %s" % (sqlFilename, line))
                        sqlContent = sqlContent.strip()
                        # execute sql
                        with connection.cursor() as cursor:
                            cursor.execute(sqlContent)
                        # update .processed file
                        newSqlFile = Path(newSqlFile)
                        modifyTime = os.path.getmtime(newSqlFile)
                        modifyTime = datetime.fromtimestamp(modifyTime).strftime('%Y-%m-%d %H:%M:%S')
                        fileMD5 = __fileMD5(newSqlFile)
                        fileData = {'name': newSqlFile.name, 'filemtime': modifyTime,
                                    'executetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'md5': fileMD5}
                        executedSqlFiles.append(fileData)

                        # overwrite the json file
                        sqlFileData['executed'] = executedSqlFiles
                        with open(processFile, "w") as jsonFile:
                            json.dump(sqlFileData, jsonFile, indent=4)
                except Exception as e:
                    logger.error(e, exc_info=True)
                    raise IkException('Process sql file [%s] failed: %s' % (newSqlFile, str(e)))
        logger.info('Processed [%s] sql file(s).' % processed_file_no)
    finally:
        __EXECUTE_SQL_FILE_LOCK.release()


def __getSqlFiles(sqlFilePath):
    fileList = []
    for root, directories, files in os.walk(sqlFilePath):
        for filename in files:
            if filename.lower().endswith('.sql'):
                if filename in fileList:
                    raise IkException('Sql filename is unique. Please check [%s].' % str(os.path.join(root, filename)))
                fileList.append(os.path.join(root, filename))
    sortedFiles = sorted(fileList, key=lambda x: (os.path.getmtime(x), os.path.basename(x)))
    return sortedFiles


def __fileMD5(file: Path) -> str:
    with open(file, 'rb') as f:
        md5_hash = hashlib.md5()
        while True:
            data = f.read(8192)
            if not data:
                break
            md5_hash.update(data)
    return md5_hash.hexdigest()
