"""ES file class model.

"""
import hashlib
import os
from datetime import datetime
from enum import Enum, unique
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile

import core.core.doc_reader as doc_reader
import core.core.fs as ikfs
from core.core.exception import IkValidateException
from core.db.transaction import IkTransaction
from core.log.logger import logger

from .. import models as esModels
from . import const

ALLOW_FILE_TYPES = ("PDF", "PNG", "JPG", "JPEG")

FOLDER_ES = 'es'
FOLDER_FILE = 'file'
# NO_INVOICE_FILE_TEMPLATE = 'noInvoice.jpg'

FILE_ROOT_DIR = ikfs.getVarFolder(subPath=const.APP_CODE)
FILE_TEMP_DIR = ikfs.getVarTempFolder(subPath=const.APP_CODE)


def get_not_exist_file_template() -> Path:
    return doc_reader.get_not_exist_file_template()


def get_blank_page_file_template() -> Path:
    return doc_reader.get_blank_page_file_template()


@unique
class FileCategory(Enum):
    """Sequence types
    """

    INVOICE = "invoice"
    PAYMENT_RECORD = "payment record"
    EXCHANGE_RATE_RECEIPT = "exchange receipt"  # TODO: no need
    SUPPORTING_DOCUMENT = "supporting document"
    PO = "po"


class ESFile:
    """ES file class.

    Attributes:
        filename (str): File name.
        file (:obj:`pathlib.Path`): File's full path.

    """

    def __init__(self, filename: str = None, file: Path = None):
        self.filename = filename
        self.file = file


def getRootFolder() -> Path:
    '''
        var/ES
    '''
    return Path(ikfs.getFileStorageVarFolder(FOLDER_ES))


# def getNoInvoiceTemplateFile() -> Path:
#     return Path(os.path.join(getRootFolder().resolve(), NO_INVOICE_FILE_TEMPLATE))


def getUploadFileFolder() -> Path:
    '''
        es/resources/file
    '''
    return Path(os.path.join(getRootFolder().resolve(), FOLDER_FILE))


def getUploadFileAbsolutePath(relativePath: str, filename: str) -> Path:
    if relativePath.startswith("/"):
        relativePath = relativePath[1:]
    if filename.startswith("/"):
        filename = filename[1:]
    return Path(os.path.join(getUploadFileFolder().resolve(), relativePath, filename))


def getTempFolder(subFolder: str = None) -> Path:
    return ikfs.getVarTempFolder(FOLDER_ES) if subFolder is None else \
        Path(os.path.join(ikfs.getVarTempFolder(FOLDER_ES).resolve(), subFolder))


def getReallyFile(fileRc: esModels.File) -> Path:
    # YL, 2023-05-30 bugfix: os.path.join(1, 2, 3) - 2 & 3 Arguments cannot start with "/" or they won't be spliced 1
    tmpFilePath = fileRc.file_path[1:] if fileRc.file_path.startswith(
        "/") else fileRc.file_path
    path = tmpFilePath.replace("\\", "/")
    filename = fileRc.file_nm
    folder = getUploadFileFolder()
    return Path(os.path.join(str(folder), path, filename))


def getESFile(file_rc: int | esModels.File) -> ESFile:  # TODO: use File instead int
    '''
        null if not found
    '''
    fileRc = esModels.File.objects.filter(id=file_rc).first() if type(file_rc) == int else file_rc
    if not fileRc:
        return None
    ef = ESFile()
    ef.file = getReallyFile(fileRc)
    ef.filename = fileRc.file_original_nm
    return ef


def getIdFile(fileID: int, filename: str) -> Path:
    relativePath = ikfs.number2Path(fileID)
    return getUploadFileAbsolutePath(relativePath, filename)


def validateUploadFileType(file: Path | str) -> bool:
    if file is None:
        raise IkValidateException('Parameter [file] is mandatory.')
    fileType = (file if isinstance(file, Path) else Path(file)).suffix[1:]
    return fileType.upper() in ALLOW_FILE_TYPES


def deleteESFileAndFolder(file: Path | int) -> None:
    ikfs.deleteFileAndFolder(file=file, folder=FOLDER_FILE)


def getFile(fileID: int) -> Path:
    esFile = getESFile(fileID)
    return None if esFile is None else esFile.file


def deleteFileRecord(fileID) -> bool:
    return rollbackFileRecord(fileID)


def rollbackFileRecord(operator_id: int, file_id: int = None, file_rc: esModels.File = None) -> bool:
    if file_id is None and file_rc is None:
        raise IkValidateException('Parameter [file_id] or [file_rc] is mandatory.')
    file_rc = esModels.File.objects.filter(id=file_id).first() if file_rc is None else file_rc
    if file_rc is None:
        logger.info('File [%s] does not exist.' % file_id)
        return True
    try:
        # 1. delete file record from database
        if not file_rc.ik_is_status_new() and not file_rc.ik_is_status_delete():
            file_rc.ik_set_status_delete()
            ptrn = IkTransaction(userID=operator_id)
            ptrn.add(file_rc)
            b = ptrn.save()
            if not b.value:
                logger.error('Delete file [%s] failed: %s' % (file_id, b.dataStr))
                return False

        # 2. delete file and its parent folder
        file_path = getESFile(file_rc).file
        deleteESFileAndFolder(file_path)
        return True
    except Exception as e:
        logger.error(
            'Delete file [%s] failed. Exception=%s' % (file_id, str(e)))
        logger.error(e, exc_info=True)


def calculateFileHash(filePath: any, hashAlgorithm: str = 'sha256'):
    with open(filePath, 'rb') as file:
        hash_function = hashlib.new(hashAlgorithm)
        while True:
            data = file.read(65536)
            if not data:
                break
            hash_function.update(data)
    return hash_function.hexdigest()


def save_uploaded_really_file(uploaded_file: InMemoryUploadedFile, category: str, username: str) -> Path:
    """Saved uploaded temp file.
    """
    if not validateUploadFileType(uploaded_file.name):
        raise IkValidateException('Unsupport file [%s]. Only %s allowed.' % (uploaded_file.name, ALLOW_FILE_TYPES))
    destination = Path(os.path.join(FILE_TEMP_DIR, 'upload', category, '%s-%s' % (username, datetime.strftime(datetime.now(), '%Y%m%d%H%M%S%f')), uploaded_file.name))
    if destination.is_file():
        raise IkValidateException('Temp file [%s] is exists!' % destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with default_storage.open(destination, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return destination


def delete_really_file(file_path: Path) -> None:
    """Delete the temp file and its parent folder. Please reference to method "save_uploaded_really_file".
    """
    try:
        if file_path is not None:
            if file_path.is_file():
                os.remove(file_path)
            if file_path.parent.is_dir():
                ikfs.deleteFolder(file_path.parent)
    except Exception as e:
        logger.error('Delete temp file [%s] failed: %s' % (file_path, e), e)
