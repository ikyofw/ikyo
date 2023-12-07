import random

import core.ui.ui as ikui
from core.core.http import responseFile
from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


class UploadAndDownloadDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getMessage(self):
        return ikui.DialogMessage.getSuccessResponse(message='message', title="message in backend")

    def getUploadRc1(self):
        return IkSccJsonResponse(data={})
    
    def getUploadRc2(self):
        return IkSccJsonResponse(data={})

    def uploadFile(self):
        data = self.getRequestData()
        uploadFile = data.getFiles('importFile1')
        return IkSccJsonResponse(message='uploaded')

    def downloadFile(self):
        f = './var/demo-files/HtmlDemo.html'
        return responseFile(f)
