import logging
import traceback

from django.db.models import Q

import core.ui.ui as ikui
from core.core.code import MessageType
from core.core.http import *
from core.inbox import inbox_manager
from core.models import *
from core.sys.system_setting import SystemSetting
from core.user import user_manager
from core.utils.lang_utils import isNotNullBlank, isNullBlank
from core.view.screen_view import ScreenAPIView

logger = logging.getLogger('ikyo')


class InboxView(ScreenAPIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def beforeInitScreenData(self, screen: ikui.Screen):
        super().beforeInitScreenData(screen)
        if screen.subScreenName.lower() == ikui.MAIN_SCREEN_NAME.lower():  # main screen
            count = self.get_new_msg_count().data
            if count > 0:
                self._addInfoMessage("You have %s unread message%s." % (count, "s" if count > 1 else ""))

        self._addStaticResource(self.get_last_static_revision_file('inbox.css', 'core/css'))

    def search(self):
        sch_item = self.getRequestData().get('schFg', None)
        if all(v in [None, '', [], {}] for v in sch_item.values()):
            sch_item = None
        return self.setSessionParameters({'sch_item': sch_item})

    def get_sch_rc(self):
        return IkSccJsonResponse(data=self.getSessionParameter('sch_item'))

    def get_inbox_modules(self):
        """
            Inbox Module List
        """
        return list(IkInbox.objects.all().values_list("module", flat=True).distinct())

    def get_inbox_status(self):
        """ 
            Inbox Status List
        """
        return [value for value, _ in IkInbox.STATUS_CHOOSES if value != IkInbox.STATUS_DELETED]

    def get_inbox_rcs(self):
        """ 
            Inbox Table Data
        """
        data = IkInbox.objects.filter(owner__id=self.getCurrentUserId()).order_by('-id')
        sch_items = self.getSessionParameter('sch_item')
        if isNotNullBlank(sch_items):
            dt_from = sch_items['schDtFrom']
            dt_to = sch_items['schDtTo']
            module = sch_items['schModule']
            status = sch_items['schStatus']
            keyword = sch_items['schKeyword']
            if isNotNullBlank(dt_from):
                data = data.filter(send_dt__gte=dt_from)
            if isNotNullBlank(dt_to):
                data = data.filter(send_dt__lt=dt_to)
            if isNotNullBlank(module):
                data = data.filter(module__icontains=module)
            if isNotNullBlank(status):
                data = data.filter(sts=status)
            else:
                data = data.filter(~Q(sts=IkInbox.STATUS_DELETED))
            if isNotNullBlank(keyword):
                data = data.filter(Q(sender__usr_nm__icontains=keyword) | Q(module__icontains=keyword)
                                   | Q(summary__icontains=keyword) | Q(usr_rmk__icontains=keyword))
        else:
            data = data.filter(~Q(sts=IkInbox.STATUS_DELETED))

        def get_style_func(results):
            style = []
            for inbox in results:
                style.append({"row": inbox['id'], "class": inbox['sts']})
            return style
        return self.getPagingResponse(table_name="inboxFg", table_data=data, get_style_func=get_style_func)

    def post_pre_rmk(self):
        pre_rmk = self.getRequestData().get('row', {}).get('usr_rmk', '')
        return self.setSessionParameters({'pre_rmk': pre_rmk})

    def get_user_rmk_rc(self):
        pre_rmk = self.getSessionParameter('pre_rmk')
        data = {'usrRmkField': pre_rmk}
        self.deleteSessionParameters('usrRmkField')
        return IkSccJsonResponse(data=data)

    def update_user_rmk(self):
        """ 
            Update User Remark
        """
        request_data = self.getRequestData()
        inbox_id = request_data.get('id')

        if isNullBlank(inbox_id) or isNullBlank(request_data.get('usrRmkDialog', None)):
            return IkSysErrJsonResponse()
        user_rmk = request_data.get('usrRmkDialog', None).get('usrRmkField', None)
        if isNullBlank(user_rmk):
            return IkErrJsonResponse(message="Please input user remark at dialog.")

        inbox_id = int(inbox_id)
        inbox_rc = IkInbox.objects.filter(id=inbox_id).first()
        if isNullBlank(inbox_rc):
            return IkErrJsonResponse(message="Inbox ID: %s doesn't exists." % inbox_id)
        inbox_rc.usr_rmk = user_rmk
        inbox_rc.save()
        return IkSccJsonResponse()

    def open_screen(self):
        """ 
            Go to module
        """
        try:
            inbox_id = self.getRequestData().get('id')
            if isNotNullBlank(inbox_id):
                inbox_id = int(inbox_id)
                boo = inbox_manager.mark_read(self.getCurrentUserId(), [inbox_id])
                if boo.value:
                    # Open Menu
                    inbox_params = inbox_manager.get_link_params(inbox_id)
                    found_command = False
                    open_page_menu = None
                    open_page_params = {}
                    for key in inbox_params.keys():
                        if not found_command and key == inbox_manager.ACTION_COMMAND:
                            found_command = True
                            menuRc = Menu.objects.filter(id=inbox_params.get(key)).first()
                            open_page_menu = menuRc.screen_nm
                        value = inbox_params.get(key)
                        open_page_params.update({key: value})
                    open_page_params.update({inbox_manager.PARAMETER_FROM_MENU: inbox_manager.MENU_INBOX})
                    if found_command:
                        return self._openScreen(menuName=open_page_menu, parameters=open_page_params)
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
    def mark_read(self):
        """ 
            Mark Read Inbox(s)
        """
        selected_inboxes = self.getRequestData().getSelectedTableRows('inboxFg')
        inbox_ids = [inbox.id for inbox in selected_inboxes]
        try:
            if len(inbox_ids) > 0:
                boo = inbox_manager.mark_read(self.getCurrentUserId(), inbox_ids)
                if boo.value:
                    return IkSccJsonResponse(message="Read.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to read.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    def mark_unread(self):
        """ 
            Mark UnRead Inbox(s)
        """
        selected_inboxes = self.getRequestData().getSelectedTableRows('inboxFg')
        inbox_ids = [inbox.id for inbox in selected_inboxes]
        try:
            if len(inbox_ids) > 0:
                boo = inbox_manager.mark_unread(self.getCurrentUserId(), inbox_ids)
                if boo.value:
                    return IkSccJsonResponse(message="Unread.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to unread.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    def mark_complete(self):
        """ 
            Mark Complete Inbox(s)
        """
        selected_inboxes = self.getRequestData().getSelectedTableRows('inboxFg')
        inbox_ids = [inbox.id for inbox in selected_inboxes]
        try:
            if len(inbox_ids) > 0:
                boo = inbox_manager.mark_completed(self.getCurrentUserId(), inbox_ids)
                if boo.value:
                    return IkSccJsonResponse(message="Completed.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to complete.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    def mark_delete(self):
        """ Mark Delete Inbox(s)

        not real delete
        """
        selected_inboxes = self.getRequestData().getSelectedTableRows('inboxFg')
        inbox_ids = [inbox.id for inbox in selected_inboxes]
        try:
            if len(inbox_ids) > 0:
                boo = inbox_manager.mark_deleted(self.getCurrentUserId(), inbox_ids)
                if boo.value:
                    return IkSccJsonResponse(message="Deleted.")
                else:
                    return boo.toIkJsonResponse1()
            return IkSccJsonResponse(message="Please select inbox(s) to delete.", messageType=MessageType.INFO)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))

    def get_new_msg_count(self):
        """ 
            Get total new message for topTitle get has new message icon or no message icon
        """
        inbox_office_set = SystemSetting.get(name="INBOX_OFFICE")
        inbox_offices = []
        if isNotNullBlank(inbox_office_set):
            inbox_offices = inbox_office_set.split(",")
            inbox_offices = [part.strip() for part in inbox_office_set.split(",")]
        count = IkInbox.objects.filter(owner__id=self.getCurrentUserId(), sts=IkInbox.STATUS_NEW).count()
        user_office = user_manager.getUserDefaultOffice(self.getCurrentUserId())
        if len(inbox_offices) > 0 and user_office not in inbox_offices:
            count = 0
        return IkSccJsonResponse(data=count)
