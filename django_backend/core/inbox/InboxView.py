'''
Description: Inbox
version: 
Author: YL
Date: 2024-04-26 08:56:54
'''
import logging
import traceback

from django.db.models import Q

import core.ui.ui as ikui
from core.core.code import MessageType
from core.core.http import *
from core.inbox import InboxManager
from core.models import *
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.view.screenView import ScreenAPIView

logger = logging.getLogger('ikyo')


class InboxView(ScreenAPIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def beforeInitScreenData(self, screen: ikui.Screen):
        super().beforeInitScreenData(screen)

        if screen.subScreenName.lower() == ikui.MAIN_SCREEN_NAME.lower():  # main screen
            count = self.getNewMsgSize().data
            if count > 0:
                self._addInfoMessage("You have %s unread message%s." % (count, "s" if count > 1 else ""))

        self._addStaticResource('core/css/ib000-v1.css')

    def getInboxStatus(self):
        """ Inbox Status

        """
        return InboxManager.getInboxStatus()

    def getInboxModules(self):
        """ Inbox Module

        """
        return InboxManager.getInboxModules()

    def getInboxRcs(self):
        """ Inbox List Table Data

        """
        userId = self.getCurrentUserId()
        data = IkInbox.objects.filter(owner__id=userId).order_by('-id')
        schParams = self.getSearchData("schFg", None)
        schPageSize = None
        if isNotNullBlank(schParams):
            if isNotNullBlank(schParams['schFgDtFrom']):
                data = data.filter(send_dt__gte=schParams['schFgDtFrom'])
            if isNotNullBlank(schParams['schFgDtTo']):
                data = data.filter(send_dt__lt=schParams['schFgDtTo'])
            if isNotNullBlank(schParams['schFgModule']):
                data = data.filter(module__icontains=schParams['schFgModule'])
            if isNotNullBlank(schParams['schFgStatus']):
                data = data.filter(sts=schParams['schFgStatus'])
            else:
                data = data.filter(~Q(sts=IkInbox.STATUS_DELETED))
            if isNotNullBlank(schParams['schFgKeyword']):
                data = data.filter(Q(sender__usr_nm__icontains=schParams['schFgKeyword']) | Q(module__icontains=schParams['schFgKeyword'])
                                   | Q(summary__icontains=schParams['schFgKeyword']) | Q(usr_rmk__icontains=schParams['schFgKeyword']))
        else:
            data = data.filter(~Q(sts=IkInbox.STATUS_DELETED))

        def get_style_func(results):
            style = []
            for inbox in results:
                style.append({"row": inbox['id'], "class": inbox['sts']})
            return style
        return self.getPagingResponse(table_name="inboxFg", table_data=data, get_style_func=get_style_func)

    def postPreRmk(self):
        requestData = self.getRequestData()
        preRmk = requestData.get('row', {}).get('usr_rmk', '')
        return self.setSessionParameters({'preRmk': preRmk})

    def getRmkDialogRc(self):
        preRmk = self.getSessionParameter('preRmk')
        data = {'usrRmkField': preRmk}
        self.deleteSessionParameters('usrRmkField')
        return IkSccJsonResponse(data=data)

    def updateUserRmk(self):
        """ Update User Remark
        """
        requestData = self.getRequestData()
        inboxId = requestData.get('id')

        if isNullBlank(inboxId) or isNullBlank(requestData.get('usrRmkDialog', None)):
            return IkSysErrJsonResponse()
        usrRmk = requestData.get('usrRmkDialog', None).get('usrRmkField', None)
        if isNullBlank(usrRmk):
            return IkErrJsonResponse(message="Please input user remark at dialog.")

        inboxId = int(inboxId)
        inboxRc = IkInbox.objects.filter(id=inboxId).first()
        if isNullBlank(inboxRc):
            return IkErrJsonResponse(message="Inbox ID: %s doesn't exists." % inboxId)
        inboxRc.usr_rmk = usrRmk
        inboxRc.save()
        return IkSccJsonResponse()

    def openDetail(self):
        """ Go to module
        """
        userId = self.getCurrentUserId()
        requestData = self.getRequestData()
        try:
            inboxID = requestData.get('id')
            if isNotNullBlank(inboxID):
                inboxID = int(inboxID)
                boo = InboxManager.markRead(userId, [inboxID])
                if boo.value:
                    # Open Menu
                    IkInboxRc = IkInbox.objects.filter(id=inboxID).first()
                    inboxParams = InboxManager.getLinkParameters(inboxID)
                    foundCommand = False
                    openPageMenu = None
                    openPageParams = {}
                    for key in inboxParams.keys():
                        if not foundCommand and key == InboxManager.ACTION_COMMAND:
                            foundCommand = True
                            menuRc = Menu.objects.filter(id=inboxParams.get(key)).first()
                            openPageMenu = menuRc.screen_nm
                        else:
                            value = inboxParams.get(key)
                            openPageParams.update({key: value})
                    openPageParams.update({InboxManager.PARAMETER_FROM_MENU: InboxManager.MENU_INBOX})
                    if foundCommand:
                        return self._openScreen(menuName=openPageMenu, parameters=openPageParams)
                    else:
                        return IkErrJsonResponse(message="No link found")
                else:
                    return boo.toIkJsonResponse1()
            return IkSysErrJsonResponse()
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    # Toolbar buttons
    def markSelectedRead(self):
        """ Mark Read Inbox(s)
        """
        userId = self.getCurrentUserId()
        requestData = self.getRequestData()
        selectedInboxes = requestData.getSelectedTableRows('inboxFg')
        inboxIds = [inbox.id for inbox in selectedInboxes]
        try:
            if len(inboxIds) > 0:
                boo = InboxManager.markRead(userId, inboxIds)
                if boo.value:
                    return IkSccJsonResponse(message="Read.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to read.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    def markSelectedUnread(self):
        """ Mark UnRead Inbox(s)

        """
        userId = self.getCurrentUserId()
        requestData = self.getRequestData()
        selectedInboxes = requestData.getSelectedTableRows('inboxFg')
        inboxIds = [inbox.id for inbox in selectedInboxes]
        try:
            if len(inboxIds) > 0:
                boo = InboxManager.markUnread(userId, inboxIds)
                if boo.value:
                    return IkSccJsonResponse(message="Unread.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to unread.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    def markSelectedDelete(self):
        """ Mark Delete Inbox(s)

        not real delete
        """
        userId = self.getCurrentUserId()
        requestData = self.getRequestData()
        selectedInboxes = requestData.getSelectedTableRows('inboxFg')
        inboxIds = [inbox.id for inbox in selectedInboxes]
        try:
            if len(inboxIds) > 0:
                boo = InboxManager.markDeleted(userId, inboxIds)
                if boo.value:
                    return IkSccJsonResponse(message="Deleted.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to delete.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    # for topTitle get has new message icon or no message icon

    def getNewMsgSize(self):
        """ Get total new message for Home & inbox icon alert

        """
        count = IkInbox.objects.filter(owner__id=self.getCurrentUserId(), sts=IkInbox.STATUS_NEW).count()
        return IkSccJsonResponse(data=count)
