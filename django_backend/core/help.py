'''
Description: 
version: 
Author: YL
Date: 2024-01-30 14:33:38
'''
'''
    Help Controller
'''
import os
from pathlib import Path

from django.db.models import Q
from django.http.response import HttpResponse

import core.core.fs as ikfs
from core.log.logger import logger
from core.menu.menuManager import ACL_DENY, MenuManager
from core.models import *
from core.ui import ui
from core.utils.langUtils import isNullBlank
from core.view.authView import AuthAPIView


class ScreenHelpView(AuthAPIView):

    def __init__(self) -> None:
        super().__init__()

    def post(self, request, *args, **kwargs):
        viewID = kwargs.get('viewID', None)
        userID = self.getCurrentUserId()
        if isNullBlank(viewID):
            logger.error('viewID is no exists, then raise 404 error')
            return HttpResponse('Help page is not found.')

        screenRc = Screen.objects.filter(screen_sn__iexact=viewID).order_by("-rev").first()
        menuRc = Menu.objects.filter(menu_nm__iexact=screenRc.screen_sn).exclude(menu_nm__iexact='Menu', enable=False).first()
        if screenRc is None or menuRc is None:
            logger.error('Screen: %s is no exists at, then raise error.' % viewID)
            return HttpResponse('Screen[%s] does not exist.' % viewID)
        screenFileRc = ScreenFile.objects.filter(screen=screenRc.id).first()
        if screenFileRc is None:
            logger.info('Screen file: %s is no exists, then raise error.' % viewID)
            return HttpResponse('Screen File[%s] does not exist, please ask administrator to check.' % viewID)

        # check menu permission
        acl = MenuManager.getUserMenuAcl(usrID=userID, menuID=menuRc.id)
        if acl == ACL_DENY:
            logger.error('User have no permission for %s' % viewID)
            return HttpResponse('Permission Deny.')
        # get file path
        # 1. check app/resources folder
        fileFolder = Path(os.path.join(screenFileRc.file_path, ui.SCREEN_RESOURCE_FOLDER_PATH))
        pdfFileName = str(viewID) + ".pdf"
        pdfFilePath = ikfs.getLastRevisionFile(fileFolder, pdfFileName)
        htmlFileName = str(viewID) + ".html"
        htmlFilePath = ikfs.getLastRevisionFile(fileFolder, htmlFileName)

        # 2. check var/app folder
        if pdfFilePath is None and htmlFilePath is None:
            fileFolder = Path(os.path.join(ui.getRelativeScreenFileFolder(), screenFileRc.file_path))
            pdfFileName = str(viewID) + ".pdf"
            pdfFilePath = ikfs.getLastRevisionFile(fileFolder, pdfFileName)
            htmlFileName = str(viewID) + ".html"
            htmlFilePath = ikfs.getLastRevisionFile(fileFolder, htmlFileName)

        # .html & .pdf are exists
        if pdfFilePath is not None and Path(pdfFilePath).exists() and htmlFilePath is not None and Path(htmlFilePath).exists():
            # get higher version file
            pdfFileVersion = 0 if "-v" not in pdfFilePath.stem else pdfFilePath.stem.split("-v")[1]
            htmlFileVersion = 0 if "-v" not in htmlFilePath.stem else htmlFilePath.stem.split("-v")[1]
            if float(htmlFileVersion) >= float(pdfFileVersion):
                filePath = htmlFilePath
                fileType = htmlFilePath.suffix[1:]
            else:
                filePath = pdfFilePath
                fileType = pdfFilePath.suffix[1:]
        else:
            if pdfFilePath is not None and Path(pdfFilePath).exists():
                filePath = pdfFilePath
                fileType = pdfFilePath.suffix[1:]
            elif htmlFilePath is not None and Path(htmlFilePath).exists():
                filePath = htmlFilePath
                fileType = htmlFilePath.suffix[1:]
            else:
                logger.error("Help document: %s does not exist." % str(viewID))
                return HttpResponse('No help document found.')

        with open(filePath, 'rb') as f:
            fileData = f.read()
        response = HttpResponse(content_type='application/%s' % fileType)
        response['Content-Disposition'] = 'attachment; filename="file.%s"' % fileType
        response.write(fileData)
        return response
