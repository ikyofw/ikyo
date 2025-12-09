import logging
import traceback

from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.db.models import Case, When, Value, IntegerField, Q

import core.core.fs as ikfs
import core.user.user_manager as UserManager
from core.core.lang import Boolean2
from core.auth.index import hasLogin
from core.core.http import *
from core.core.mailer import MailManager, standardEmailAddress
from core.db.transaction import IkTransaction
from core.inbox import inbox_view
from core.menu import menu_view
from core.menu.menu_manager import MenuManager
from core.models import Currency as CurrencyModel
from core.models import Mail, MailAddr, MailAttch, User
from core.screen import app_view, screen_dfn_view, type_widget_view
from core.user import user_group_view, user_view
from core.utils.lang_utils import isNullBlank
from core.view.screen_view import ScreenAPIView

logger = logging.getLogger('ikyo')


def index(request):
    '''
        Used for
    '''
    return HttpResponse("Hello, Ikyo World!")


ROUTER_EXCLUDE_SCREENS = [
    'menu',
]


def getRouters(request):
    screenIDs, screenUrls = [], []
    if hasLogin(request):
        excludeScreens = [s.lower() for s in ROUTER_EXCLUDE_SCREENS]
        screenNames = MenuManager.getIkScreens()
        for screenName in screenNames:
            if screenName.lower() not in excludeScreens:
                sn = screenName.lower()
                screenIDs.append(sn)
                screenUrls.append(sn)
    return IkSccJsonResponse(data={"screenIDs": screenIDs, "paths": screenUrls})


class Menu(menu_view.Menu):
    def __init__(self) -> None:
        super().__init__()


class MenuMnt(menu_view.MenuMnt):
    def __init__(self) -> None:
        super().__init__()


class ScreenDfn(screen_dfn_view.ScreenDfnView):
    def __init__(self) -> None:
        super().__init__()


class AppMnt(app_view.AppMntView):
    def __init__(self) -> None:
        super().__init__()


class TypeWidgetMnt(type_widget_view.TypeWidgetMntView):
    def __init__(self) -> None:
        super().__init__()


class UsrGrpMnt(user_group_view.UsrGrpMntView):
    def __init__(self) -> None:
        super().__init__()


class UsrMnt(user_view.UsrMntView):
    def __init__(self) -> None:
        super().__init__()


class Inbox(inbox_view.InboxView):
    def __init__(self) -> None:
        super().__init__()


class Office(ScreenAPIView):
    """ Office
    """

    def getCcyRcs(self):
        data = [
            {"id": ccy.id, "code": f'{ccy.code} - {ccy.name}'}
            for ccy in CurrencyModel.objects.all().order_by('seq')
        ]
        return IkSccJsonResponse(data=data)

    def save(self):
        officeTable = self.getRequestData().get("officeTable", None)
        if isNullBlank(officeTable):
            return IkSysErrJsonResponse()
        try:
            pytrn = IkTransaction(userID=self.getCurrentUserId())
            pytrn.add(officeTable)
            b = pytrn.save()
            if not b.value:
                return IkErrJsonResponse(message=b.dataStr)
            return IkSccJsonResponse(message="Saved.")
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))


class Currency(ScreenAPIView):
    """ Currency
    """

    def save(self):
        ccyTable = self.getRequestData().get("ccyTable", None)
        if isNullBlank(ccyTable):
            return IkSysErrJsonResponse()

        ccyTable.sort(key=lambda o: o.seq)
        seq = 0
        for r in ccyTable:
            if r.ik_is_status_delete():
                continue
            seq += 1
            if seq != r.seq:
                r.seq = seq
                if not r.ik_is_status_new():
                    r.ik_set_status_modified()

        try:
            pytrn = IkTransaction(userID=self.getCurrentUserId())
            pytrn.add(ccyTable)
            b = pytrn.save()
            return b.toIkJsonResponse1()
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))


class Mail001(ScreenAPIView):
    def __init__(self) -> None:
        super().__init__()

    def beforeInitScreenData(self, screen) -> None:
        super().beforeInitScreenData(screen)
        current_mail_id = self.getSessionParameter('current_mail_id')
        screen.setFieldGroupsVisible(fieldGroupNames=['schFg', 'mailFg', 'deleteBar'], visible=isNullBlank(current_mail_id))
        screen.setFieldGroupsVisible(fieldGroupNames=['mailDtlFg', 'mailAddrFg', 'mailAttchFg', 'uploadFg', 'backBar'], visible=isNotNullBlank(current_mail_id))

    def getSchRc(self):
        return self.getSessionParameter('sch_items')

    def search(self):
        sch_items = self.getRequestData().get('schFg')
        return self.setSessionParameter("sch_items", sch_items)

    def getMailRcs(self):
        sch_items = self.getSessionParameter('sch_items')
        key = sch_items.get('keyField', "").strip().lower() if isNotNullBlank(sch_items) else None
        mail_rcs = Mail.objects.all().order_by('-request_ts')
        data = []
        for mail_rc in mail_rcs:
            mail_addr_rcs = MailAddr.objects.filter(mail_id=mail_rc.id).order_by('name')
            to_user_rcs = mail_addr_rcs.filter(type=MailAddr.TYPE_TO)
            cc_user_rcs = mail_addr_rcs.filter(type=MailAddr.TYPE_CC)
            to_user_strings = "\n ".join([f"{user.name} <{user.address}>" for user in to_user_rcs])
            cc_user_strings = "\n ".join([f"{user.name} <{user.address}>" for user in cc_user_rcs])
            mail_rc.to_user = to_user_strings
            mail_rc.cc_user = cc_user_strings
            if isNotNullBlank(key):
                def safe_lower(v):
                    return (v or "").lower()

                if isNotNullBlank(key):
                    k = key.lower()
                    if any(
                        k in safe_lower(getattr(mail_rc, name, ""))
                        for name in ("subject", "to_user", "cc_user", "sender", "dsc")
                    ):
                        data.append(mail_rc)
            else:
                data.append(mail_rc)
        return self.getPagingResponse(table_name="mailFg", table_data=data)

    def delete(self):
        select_rows = self.getRequestData().getSelectedTableRows('mailFg')
        if isNullBlank(select_rows) or len(select_rows) == 0:
            return IkErrJsonResponse(message="Please select at least one record to delete.")
        
        mail_rcs, mail_addr_rcs, mail_attch_rcs = [], [], []
        filter_mail_ids = []
        for select_row in select_rows:
            select_row: Mail
            if select_row.sts != Mail.STATUS_IN_PROGRESS:
                select_row.ik_set_status_delete()
                mail_rcs.append(select_row)
            else:
                filter_mail_ids.append(str(select_row.id))
        for mail_rc in mail_rcs:
            for mail_addr_rc in list(MailAddr.objects.filter(mail=mail_rc)):
                mail_addr_rc.ik_set_status_delete()
                mail_addr_rcs.append(mail_addr_rc)
            for mail_attch_rc in list(MailAttch.objects.filter(mail=mail_rc)):
                mail_attch_rc.ik_set_status_delete()
                mail_attch_rcs.append(mail_attch_rc)
        if len(select_rows) != len(mail_rcs):
            return IkErrJsonResponse(message='Mails with "in_progress" status cannot be deleted. Filtered ids: [' + ", ".join(filter_mail_ids) + ']')

        ptrn = IkTransaction()
        ptrn.add(mail_rcs)
        ptrn.add(mail_addr_rcs)
        ptrn.add(mail_attch_rcs)
        b = ptrn.save()
        if b.value:
            for mail_attch_rc in mail_attch_rcs:
                if os.path.isfile(mail_attch_rc.file):
                    ikfs.deleteFileAndFolder(file=mail_attch_rc.file, folder='file')
            return IkSccJsonResponse(message='Deleted.')
        else:
            return IkErrJsonResponse(message='Failed to delete: ' + b.dataStr)

    def cancel(self):
        select_rows = self.getRequestData().getSelectedTableRows('mailFg')
        if isNullBlank(select_rows) or len(select_rows) == 0:
            return IkErrJsonResponse(message="Please select at least one record to cancel.")
        
        mail_rcs, filter_mail_ids = [], []
        for select_row in select_rows:
            select_row: Mail
            if select_row.sts == Mail.STATUS_PENDING and select_row.queue == True:
                select_row.sts = Mail.STATUS_CANCELLED
                select_row.ik_set_status_modified()
                mail_rcs.append(select_row)
            else:
                filter_mail_ids.append(str(select_row.id))
        if len(select_rows) != len(mail_rcs):
            return IkErrJsonResponse(message='Only "pending" queue can be cancelled. Filtered ids: [' + ", ".join(filter_mail_ids) + ']')

        ptrn = IkTransaction()
        ptrn.add(mail_rcs)
        b = ptrn.save()
        if b.value:
            return IkSccJsonResponse(message='Cancelled.')
        else:
            return IkErrJsonResponse(message='Failed to cancel: ' + b.dataStr)

    def getContentTp(self):
        data = []
        for i in Mail.MAIL_TYPE_CHOOSES:
            data.append({'type': i[0]})
        return IkSccJsonResponse(data=data)

    def getMailRc(self):
        current_mail_id = self.getSessionParameter('current_mail_id')
        data = Mail.objects.filter(id=current_mail_id).first()
        return IkSccJsonResponse(data=data)

    def getAddressTp(self):
        data = []
        for i in MailAddr.TYPE_CHOOSES:
            data.append({'type': i[0]})
        return IkSccJsonResponse(data=data)

    def getMailAddrRcs(self):
        current_mail_id = self.getSessionParameter('current_mail_id')
        data = MailAddr.objects.filter(mail_id=current_mail_id).annotate(
            type_order=Case(
                When(type='to', then=Value(1)),
                When(type='cc', then=Value(2)),
                When(type='bcc', then=Value(3)),
                default=Value(99),
                output_field=IntegerField(),
            )
        ).order_by('type_order', 'seq')
        return IkSccJsonResponse(data=data)

    def getMailAttchRcs(self):
        current_mail_id = self.getSessionParameter('current_mail_id')
        attach_rcs = MailAttch.objects.filter(mail_id=current_mail_id).order_by('seq')
        data = []
        for attach_rc in attach_rcs:
            data.append({'id': attach_rc.id, 'file': Path(attach_rc.file).name, 'size': attach_rc.size})
        return IkSccJsonResponse(data=data)

    def download(self):
        requestData = self.getRequestData()
        attach_id = requestData.get('row', {}).get('id', None)
        if isNotNullBlank(attach_id):
            attach_rc = MailAttch.objects.get(id=int(attach_id))
            return self.downloadFile(file=attach_rc.file)
        return IkErrJsonResponse(message="File does not exist.")

    def mailFg_EditIndexField_Click(self):
        current_mail_id = self._getEditIndexField()
        return self.setSessionParameters({'current_mail_id': current_mail_id})

    def back(self):
        return self.deleteSessionParameters(['current_mail_id'])

    def save(self):
        current_mail_id = self.getSessionParameter('current_mail_id')
        request_data = self.getRequestData()
        mail_rc = request_data.get('mailDtlFg')
        mail_addr_rcs = request_data.get('mailAddrFg')
        mail_attch_rcs = request_data.get('mailAttchFg')
        upload_files = request_data.getFiles('uploadField')

        b = self.__check_mail_and_mail_addr(mail_rc, mail_addr_rcs)
        if not b.value:
            return b.toIkJsonResponse1()
        
        new_file_seq = 1
        for pre_file in mail_attch_rcs:
            pre_file: MailAttch
            if pre_file.ik_is_status_delete():
                if os.path.isfile(pre_file.file):
                    ikfs.deleteFileAndFolder(file=pre_file.file, folder='file')
            else:
                new_file_seq += 1
        for index, upload_file in enumerate(upload_files):
            file_path = Mail002.save_file(upload_file, mail_rc.id)
            file_size = os.path.getsize(file_path)
            mail_attch_rcs.append(MailAttch(mail_id=current_mail_id, file=file_path, size=file_size, seq=new_file_seq + index))

        ptrn = IkTransaction()
        ptrn.add(mail_rc)
        ptrn.add(mail_addr_rcs)
        ptrn.add(mail_attch_rcs)
        b = ptrn.save()
        if b.value:
            return IkSccJsonResponse(message='Saved.')
        else:
            return IkErrJsonResponse(message='Failed to save: ' + b.dataStr)
        
    def __check_mail_and_mail_addr(self, mail_rc: Mail, mail_addr_rcs: list[MailAddr]):
        current_mail_id = self.getSessionParameter('current_mail_id')
        if isNullBlank(mail_rc.sender):
            return Boolean2(False, "The sender of the email is mandatory.")
        if isNullBlank(mail_rc.subject):
            return Boolean2(False, "The subject of the email is mandatory.")
        if isNullBlank(mail_rc.content):
            return Boolean2(False, "The content of the email is mandatory.")

        to_user_num = 0
        seen = set()
        for addr_rc in mail_addr_rcs:
            addr_rc: MailAddr
            if addr_rc.ik_is_status_new() or addr_rc.ik_is_status_modified():
                addr_rc.mail_id = current_mail_id
                addr_rc.name = standardEmailAddress(addr_rc.address).name
            if not addr_rc.ik_is_status_delete() and addr_rc.type == 'to':
                to_user_num += 1
            key = (addr_rc.type, addr_rc.address)
            if key in seen:
                return Boolean2(False, "Duplicate recipient in this mail: type=%s, address=%s." % (addr_rc.type, addr_rc.address))
            seen.add(key)
        if to_user_num == 0:
            return Boolean2(False, 'The recipient of the email is mandatory.')
        return Boolean2(True)

    def send(self):
        return self.__send(False)

    def send_in_background(self):
        return self.__send(True)

    def __send(self, send_in_background):
        request_data = self.getRequestData()
        mail_rc = request_data.get('mailDtlFg')
        mail_addr_rcs = request_data.get('mailAddrFg')
        mail_attch_rcs = request_data.get('mailAttchFg')
        upload_files = request_data.getFiles('uploadField')

        b = self.__check_mail_and_mail_addr(mail_rc, mail_addr_rcs)
        if not b.value:
            return b.toIkJsonResponse1()
        
        to_email_addresses = [mail_addr_rc.address for mail_addr_rc in mail_addr_rcs if mail_addr_rc.type == 'to' and not mail_addr_rc.ik_is_status_delete()]
        cc_email_addresses = [mail_addr_rc.address for mail_addr_rc in mail_addr_rcs if mail_addr_rc.type == 'cc' and not mail_addr_rc.ik_is_status_delete()]
        bcc_email_addresses = [mail_addr_rc.address for mail_addr_rc in mail_addr_rcs if mail_addr_rc.type == 'bcc' and not mail_addr_rc.ik_is_status_delete()]

        attachments = []
        for pre_file in mail_attch_rcs:
            if pre_file.ik_is_status_delete():
                if os.path.isfile(pre_file.file):
                    ikfs.deleteFileAndFolder(file=pre_file.file, folder='file')
            else:
                attachments.append(pre_file.file)
        for upload_file in upload_files:
            file_path = Mail002.save_file(upload_file, mail_rc.id)
            attachments.append(file_path)

        result = MailManager.send(sender=mail_rc.sender, subject=mail_rc.subject, to=to_email_addresses, cc=cc_email_addresses, bcc=bcc_email_addresses,
                                  content=mail_rc.content, description=mail_rc.dsc, attachments=attachments, send_in_background=send_in_background, type=mail_rc.type)

        if result and result.value:
            mail_rc = result.data
            self.setSessionParameters({'current_mail_id': mail_rc.id})
            for addr in cc_email_addresses + bcc_email_addresses:
                if addr not in to_email_addresses:
                    to_email_addresses.append(addr)
            msg = 'Send email "%s" to [%s] success.' % (mail_rc.subject, ", ".join(to_email_addresses))
            return IkSccJsonResponse(message=msg + " success")
        else:
            return IkErrJsonResponse(message="Send email failed: " + result.dataStr)


class Mail002(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def beforeInitScreenData(self, screen) -> None:
        super().beforeInitScreenData(screen)
        select_type = self.getSessionParameter('select_type')
        screen.setFieldsVisible(fieldGroupName='sendMailFg', fieldNames=['contentField'], visible=isNullBlank(select_type) or select_type == 'text')
        screen.setFieldsVisible(fieldGroupName='sendMailFg', fieldNames=['customTemplateFileField', 'templateFilePramField'], visible=select_type == 'html')

    def getUsers(self):
        return User.objects.all().order_by('usr_nm').values('id', 'usr_nm')

    def getContentTp(self):
        data = []
        for i in Mail.MAIL_TYPE_CHOOSES:
            data.append({'type': i[0]})
        return IkSccJsonResponse(data=data)

    def changeType(self):
        data = self.getRequestData()
        select_type = data.get('sendMailFg')['type']
        return self.setSessionParameters({'select_type': select_type})

    def getMailRc(self):
        select_type = self.getSessionParameter('select_type')
        data = {'type': 'text' if isNullBlank(select_type) else select_type}
        return IkSccJsonResponse(data=data)

    def getTemplateFiles(self):
        data = [{'file_name': 'Template File 1'}, {'file_name': 'Template File 2'}]
        return IkSccJsonResponse(data=data)

    def send(self):
        return self.__send(False)

    def send_in_background(self):
        return self.__send(True)

    def __send(self, send_in_background):
        request_data = self.getRequestData()
        if isNullBlank(request_data['senderField']):
            return IkErrJsonResponse(message="The sender of the email is mandatory.")
        if isNullBlank(request_data['subjectField']):
            return IkErrJsonResponse(message="The subject of the email is mandatory.")
        if isNullBlank(request_data['toField']) and isNullBlank(request_data['customToField']):
            return IkErrJsonResponse(message='The recipient of the email is mandatory.')
        send_one_by_one = True if request_data['send1by1Field'].lower().strip() == 'true' else False
        to_email_addresses = self.__get_address_list(request_data['toField'], request_data['customToField'])
        cc_email_addresses = self.__get_address_list(request_data['ccField'], request_data['customCCField'])
        bcc_email_addresses = self.__get_address_list(request_data['bccField'], request_data['customBCCField'])
        attachments = []
        for i in range(5):
            attachment = request_data.getFiles('attachment' + str(i) + 'Field')
            if len(attachment) > 0:
                attachments.append(Mail002.save_file(attachment[0], is_tmp=True))

        content, template_file, template_parameter = '', '', ''
        if 'contentField' in request_data:
            content = request_data['contentField']
        if 'templateFilePramField' in request_data:
            template_parameter = request_data['templateFilePramField']
            if isinstance(template_parameter, str):
                return IkErrJsonResponse(message="Format of Template File Parameters is wrong.")
        if len(request_data.getFiles('customTemplateFileField')) > 0:
            template_file = Mail002.save_file(request_data.getFiles('customTemplateFileField')[0], is_tmp=True)
        if isNullBlank(content) and isNullBlank(template_file):
            return IkErrJsonResponse(message='Email content or template file is mandatory.')

        try:
            result = MailManager.send(sender=request_data['senderField'], subject=request_data['subjectField'], to=to_email_addresses, cc=cc_email_addresses, bcc=bcc_email_addresses,
                                      content=content, template_file=template_file, template_parameter=template_parameter, description=request_data['dscField'],
                                      attachments=attachments, send_in_background=send_in_background, send_one_by_one=send_one_by_one, type=request_data['type'])
            if result and result.value:
                for addr in cc_email_addresses + bcc_email_addresses:
                    if addr not in to_email_addresses:
                        to_email_addresses.append(addr)
                msg = 'Send email "%s" to [%s] success.' % (request_data['subjectField'], ", ".join(to_email_addresses))
                return IkSccJsonResponse(message=msg)
            else:
                return IkErrJsonResponse(message="Send email failed: " + result.dataStr)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            return IkErrJsonResponse(message=str(e))
        finally:
            for f in attachments:
                if os.path.isfile(f):
                    ikfs.deleteFileAndFolder(file=f, folder='var')
            if isNotNullBlank(template_file) and os.path.isfile(template_file):
                ikfs.deleteFileAndFolder(file=template_file, folder='var')

    def is_valid_json(self, json_str):
        if not isinstance(json_str, (str, bytes, bytearray)):
            return False
        try:
            json.loads(json_str)
            return True
        except (ValueError, TypeError):
            return False

    def __get_address_list(self, ids, custom_addr=None) -> []:
        id_list = ids.split(',') if isNotNullBlank(ids) else []
        address_list = []
        for user_id in id_list:
            address = UserManager.getUserEmailAddress(user_id).email
            if isNotNullBlank(address):
                address_list.append(address)
        if isNotNullBlank(custom_addr) and custom_addr.strip() not in address_list:
            address_list.append(custom_addr.strip())
        return address_list

    @staticmethod
    def save_file(file, mail_id=None, is_tmp=False):
        if is_tmp:
            file_parent = ikfs.getVarTempFolder(subPath='mail')
        else:
            file_parent = Path(os.path.join(ikfs.getVarFolder(subPath='mail'), str(mail_id)))
        if not file_parent.is_dir():
            file_parent.mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(file_parent, file.name)

        with default_storage.open(str(filepath), 'wb+') as dst:
            for chunk in file.chunks():
                dst.write(chunk)
        return str(filepath)
