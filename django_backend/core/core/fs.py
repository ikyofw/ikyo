import datetime
import logging
from typing import Union
import os
import platform
import shutil
import zipfile
from pathlib import Path

from core.core.lang import Boolean2
from core.utils.lang_utils import isNullBlank
from django_backend.settings import BASE_DIR

logger = logging.getLogger(__name__)

VAR_FOLDER_NAME = 'var'
VAR_FILE_PATH = VAR_FOLDER_NAME + '/file'  # used for iky_file table (var/file)
FILE_FOLDER = 'file'
IS_WINDOWS_OS = 'windows' in platform.system().lower()
PROJECT_FOLDER_NAME = "Project"


def getRootFolder() -> str:
    return BASE_DIR


def getVarFolder(subPath=None, withTimeStampFolders=False) -> Path:
    s = subPath
    if withTimeStampFolders:
        if s is None:
            s = toPath_Y_m_d_HMSf()
        else:
            s = os.path.join(s, toPath_Y_m_d_HMSf())
    return Path(os.path.join(getRootFolder(), VAR_FOLDER_NAME)) \
        if isNullBlank(s) else Path(os.path.join(getRootFolder(), VAR_FOLDER_NAME, s))


def getRelativeVarFolder(subPath=None, withTimeStampFolders=False) -> Path:
    s = subPath
    if withTimeStampFolders:
        if s is None:
            s = toPath_Y_m_d_HMSf()
        else:
            s = os.path.join(s, toPath_Y_m_d_HMSf())
    return str(Path(os.path.join(VAR_FOLDER_NAME))).replace('\\', '/') \
        if isNullBlank(s) else str(Path(os.path.join(VAR_FOLDER_NAME, s))).replace('\\', '/')


def getVarTempFolder(subPath=None) -> Path:
    s = 'tmp'
    if not isNullBlank(subPath):
        s = os.path.join(s, subPath)
    return getVarFolder(s)


def getRelativeVarTempFolder(subPath=None) -> Path:
    s = 'tmp'
    if not isNullBlank(subPath):
        s = os.path.join(s, subPath)
    return getRelativeVarFolder(s)


def getVarTempProjectFolder(projectNo, function, subPath=None, addTimestampPath: bool = True) -> Path:
    subFolder = None
    if subPath is None:
        if addTimestampPath:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function, toPath_Y_m_d_HMSf())
        else:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function)
    else:
        if addTimestampPath:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function, subPath, toPath_Y_m_d_HMSf())
        else:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function, subPath)
    return getVarTempFolder(subFolder)


def getVarProjectFolder(projectNo, function, subPath=None, addTimestampPath: bool = True) -> Path:
    subFolder = None
    if subPath is None:
        if addTimestampPath:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function, toPath_Y_m_d_HMSf())
        else:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function)
    else:
        if addTimestampPath:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function, subPath, toPath_Y_m_d_HMSf())
        else:
            subFolder = os.path.join(PROJECT_FOLDER_NAME, projectNo, function, subPath)
    return getVarFolder(subFolder)


def getVarFunctionFolder(function, subPath=None, addTimestampPath: bool = True) -> Path:
    subFolder = None
    if subPath is None:
        if addTimestampPath:
            subFolder = os.path.join('fns', function, toPath_Y_m_d_HMSf())
        else:
            subFolder = os.path.join('fns', function)
    else:
        if addTimestampPath:
            subFolder = os.path.join('fns', function, subPath, toPath_Y_m_d_HMSf())
        else:
            subFolder = os.path.join('fns', function, subPath)
    return getVarFolder(subFolder)


# YL.ikyo, 2022-11-24
# get WebTemplate folder
def getVarWebTemplatesFolder(subPath=None) -> Path:
    s = 'webTemplates'
    if not isNullBlank(subPath):
        s = os.path.join(s, subPath)
    return getVarFolder(s)


def toPath_Y_m_d(date=None) -> str:
    if date is None:
        date = datetime.datetime.now()
    return datetime.datetime.strftime(date, '%Y-%m-%d')


def toPath_Y_m_d_HMS(date=None) -> str:
    if date is None:
        date = datetime.datetime.now()
    return datetime.datetime.strftime(date, '%Y/%m/%d/%H%M%S')


def toPath_Y_m_d_HMSf(date=None) -> str:
    if date is None:
        date = datetime.datetime.now()
    return datetime.datetime.strftime(date, '%Y/%m/%d/%H%M%S%f')


def mkdirs(folder) -> None:
    Path(folder).mkdir(parents=True, exist_ok=True)


def mkParentDirs(folder) -> None:
    Path(Path(folder).parent).mkdir(parents=True, exist_ok=True)


def deleteFolder(folder) -> None:
    '''
        delete folder and its subfolders
    '''
    shutil.rmtree(folder)


def updateFilename(file, extendPart) -> str:
    p = Path(file)
    fn = p.stem + ('' if extendPart is None else extendPart) + p.suffix
    return os.path.join(p.parent.resolve(), fn)


# YL.ikyo, 2022-08-03
def getFile(file) -> str:
    p = Path(file)
    fn = p.stem + p.suffix
    return os.path.join(p.parent.resolve(), fn)


def getFileWithTimestamp(file) -> str:
    return updateFilename(file, '-' + datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S'))


def getLastRevisionFile(folder, filename) -> str:
    '''
        return None if file does not exist.
    '''
    p = Path(folder)
    if not p.is_dir():
        return None
    f = Path(os.path.join(folder, filename))
    stem = f.stem
    suffix = f.suffix

    # list all files
    lastRev = None
    lastFile = None
    for fn in os.listdir(folder):
        f = Path(os.path.join(folder, fn))
        if f.is_file() and f.stem.startswith(stem) and f.suffix == suffix:
            rev = f.stem[len(stem) + 1:].lower()  # abc-V1.txt -> v1 or abc v1.txt -> v1
            if len(rev) > 0 and rev[0] == 'v':
                rev = rev[1:]
                for index, char in enumerate(rev):
                    if not char.isdigit():
                        rev = rev[:index]
                        break
                if rev != '':
                    try:
                        rev = float(rev)
                        if lastRev is None or rev > lastRev:
                            lastRev = rev
                            lastFile = f
                    except:
                        pass
    # return last revision file if exists
    if lastFile is not None:
        return lastFile.resolve()
    # check revision file
    if Path(os.path.join(folder, filename)).is_file():
        return Path(os.path.join(folder, filename))
    return None  # file not found


def number2Path(number) -> str:
    '''
        E.g. 10283 will be parsed as a path to "10/28/3".
    '''
    numberStr = str(number)
    total = len(numberStr)
    path = ''
    for i in range(0, total, 2):
        path += numberStr[i]
        if i < total - 1:
            path += numberStr[i + 1]
        path += '/'
    return path


def getRelativeToVar(fullPath) -> str:
    p = str(Path(fullPath).relative_to(getVarFolder())).replace('\\', '/')
    if p == '.':
        p = ''
    return p

def is_under_dir(
    target: Union[str, Path],
    parent: Union[str, Path],
    direct_only: bool = False
) -> bool:
    """
    Check whether a file or directory is under a given parent directory.

    :param target: File or directory path to check
    :param parent: Parent directory path
    :param direct_only: 
        - True  -> only direct children (files or directories)
        - False -> any depth under parent
    :return: True if target is under parent according to the rule
    """
    target = Path(target).resolve()
    parent = Path(parent).resolve()

    # Parent must be a directory
    if not parent.is_dir():
        return False

    try:
        rel = target.relative_to(parent)
    except ValueError:
        return False

    if direct_only:
        # Direct child: exactly one path component
        return len(rel.parts) == 1

    # Any depth under parent
    return True

def is_under_var_dir(
    target: Union[str, Path],
    direct_only: bool = False
) -> bool:
    """
    Check whether a file or directory is under the var folder.

    :param target: File or directory path to check
    :param direct_only: 
        - True  -> only direct children (files or directories)
        - False -> any depth under var folder
    :return: True if target is under var folder according to the rule
    """
    return is_under_dir(target, getVarFolder(), direct_only)


def getFilePath(fileID, fileName=None) -> tuple:
    '''
        fileID: int. iky_file.id
        filename: str - optional. In the file system, we change the original filename to id + suffix. 
                    E.g. id=123 and filename is "abc.txt", in the file system, the file name is "123.txt".

        return (relative path (from root folder), absolute path), the file path use "/".

        E.g. fileID = 123456, fileName = a.txt
        return ('var/file/12/34/56/123456.txt', 'd:/ikyo/var/files/12/34/56/123456.txt')
    '''
    p = number2Path(fileID)
    rp = None
    if fileName is None:
        rp = os.path.join(VAR_FILE_PATH, p)
    else:
        idName = str(fileID) + Path(fileName).suffix
        rp = os.path.join(VAR_FILE_PATH, p, idName)
    ap = os.path.join(getRootFolder(), rp)
    return rp.replace('\\', '/'), ap.replace('\\', '/')


def deleteEmptyFolderAndParentFolder(p):
    """ YL.ikyo, 2022-12-13
    For delete file or folder, and up loop to delete empty parent folders

    Args:
        p: path with file name or folder path

    """

    folders = None
    if os.path.isfile(p):  # is file
        folders = os.path.dirname(p)
        os.remove(p)  # delete file
    elif os.path.isdir(p):  # is folder (delete sub folders and sub files)
        folders = p
        if len(os.listdir(folders)) == 0:  # empty folder
            os.removedirs(folders)
        else:  # not empty folder
            deleteFolder(folders)  # delete current folder and sub files & sub folders
        return
    # up loop to delete empty folders
    if folders is not None and len(os.listdir(folders)) == 0:
        os.removedirs(folders)


def deleteFileAndFolder(file: Path, folder: str) -> None:
    if file:
        file = Path(file)
        if file.is_file():
            file.unlink()

            # remote parent folder is it's empty
            p = file.parent
            while True:
                if p.name == folder:
                    break
                if not os.listdir(p.resolve()):
                    # empty folder, then delete it
                    try:
                        os.rmdir(p)
                        p = p.parent
                    except:
                        # the folder cannot be deleted or it's not empty
                        break
                else:
                    break


def zip(sourceFileList, outputFilePath, root_dir=None) -> Boolean2:
    """ YL.ikyo, 2022-12-13
    Zip files

    Args:
        sourceFileList: file list to zip
        outputFilePath: zipped file path
        root_dir: source root directory, default None

    Returns:
        Boolean2: If true, return outputFilePath, else return error message
    """
    try:
        outputFilePath = str(outputFilePath).replace("\\", "/")
        parentFolderPath = os.path.dirname(outputFilePath)

        # create if folder not exists
        if not os.path.exists(parentFolderPath):
            mkdirs(parentFolderPath)

        root_dir = str(root_dir).replace("\\", "/") if root_dir else None

        with zipfile.ZipFile(outputFilePath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for src in sourceFileList:
                src = str(src).replace("\\", "/")

                if root_dir:
                    # use relative path based on root_dir
                    arcname = os.path.relpath(src, root_dir).replace("\\", "/")
                else:
                    # keep original directory structure
                    arcname = src.lstrip("/")  # avoid absolute path in zip

                zipf.write(src, arcname)

        return Boolean2(True, outputFilePath)

    except Exception as e:
        logger.error(e, exc_info=True)
        deleteEmptyFolderAndParentFolder(outputFilePath)
        return Boolean2(False, e.args[0])


def getFileStorageVarFolder(app_nm: str) -> str:
    return getFileStorageFolder(app_nm + "/resources", None)


def get_upload_file_folder(app_nm: str) -> Path:
    '''
        [app_nm]/resources/file
    '''
    return Path(getFileStorageVarFolder(app_nm), FILE_FOLDER)


def getFileStorageFolder(path, defaultPath) -> str:
    if isNullBlank(path):
        return os.path.join(BASE_DIR, defaultPath)

    if IS_WINDOWS_OS:
        if os.path.isabs(path):
            return path
        return os.path.join(BASE_DIR, path)
    else:
        if isLinuxFullPath(path):
            return path
        return os.path.join(BASE_DIR, path)


def isWindowsFullPath(path: str):
    if len(path) >= 2 and path[1] == ':':
        driver = path[0]
        return (driver >= 'a' and driver <= 'z') or (driver >= 'A' and driver <= 'Z')
    return False


def isLinuxFullPath(path: str):
    return not isNullBlank(path) and path.startswith("/")


def getFileExtension(file: str) -> str:
    return Path(file).suffix[1:]


def getFileNameWithoutExtension(filename: str) -> str:
    return Path(filename).stem
