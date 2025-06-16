'''
Description: Mail Manager
version:
Author: YL
Date: 2024-11-06 14:52:13
'''
import logging
import os
import smtplib
import threading
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from threading import Lock

import core.core.fs as ikfs
import core.utils.djangoUtils as du
from core.core.exception import IkException, IkValidateException
from core.core.lang import Boolean2
from core.models import Mail, MailAddr, MailAttch
from core.sys.systemSetting import SystemSetting
from core.utils import strUtils, templateManager
from core.utils.langUtils import isNotNullBlank, isNullBlank
from django.db import DatabaseError, transaction
from iktools import IkConfig

logger = logging.getLogger('ikyo')


class EmailAddress:
    '''
        Name <email address> or  email address
        E.g.
         abc@test.com
         Abc efg <abc.efg@test.com>
    '''

    def __init__(self, email, name=None) -> None:
        self.email = email
        self.name = name

    def __str__(self) -> str:
        name = getEmailAddressName(self.email) if self.name is None else self.name
        if not isinstance(name, str):
            name = name.encode("utf-8")
        return u'%s <%s>' % (name, self.email)


def getEmailName(name) -> str:
    if name is None:
        return None
    if "wci" in name.lower() or "reply" in name.lower():
        mailFromName = SystemSetting.get("mail.from.name")
        if isNullBlank(mailFromName):
            mailFromName = IkConfig.get("Email", "mail.from.name")
        return mailFromName
    s = name.replace('_', ' ').replace('-', ' ').replace('.', ' ')
    s2 = ''
    for r in s.split(' '):
        s2 += ' ' + r.title()
    return s2[1:]


def getEmailAddressName(emailAddress):
    '''
        Get user name from email address.
        E.g.
         abc@test.com -> Abc
          abc.efg@test.com -> Abc Efg
           abc-efg@test.com -> Abc Efg
            abc_efg@test.com -> Abc Efg
    '''
    name = emailAddress[0:emailAddress.index("@")]
    return getEmailName(name)


def toEmailAddressList(addressStr) -> list:
    addressList = []
    if strUtils.isEmpty(addressStr):
        return addressList
    addrArr = addressStr.split(";")
    for addr in addrArr:
        addr = addr.strip()
        if not strUtils.isEmpty(addr):
            name = addr[:addr.index("<")].strip()
            email = addr[addr.index("<") + 1:len(addr) - 1].strip()
            addressList.append(convert2EmailAddress(email) if strUtils.isEmpty(name) else EmailAddress(email, name))
    return addressList


def convert2EmailAddress(emailAddress) -> EmailAddress:
    if emailAddress is None or len(emailAddress) == 0:
        return None
    name, addr = None, None
    if '<' in emailAddress:
        i = emailAddress.index('<')
        name = emailAddress[0:i].strip()
        name = getEmailName(name)
        addr = emailAddress[i + 1:].strip()
        if addr[-1] == '>':
            addr = addr[0:-1].strip()
    else:
        addr = emailAddress.strip()
    if name is None or len(name) == 0:
        name = getEmailAddressName(addr)
        name = getEmailName(name)
    return EmailAddress(email=addr, name=name)


def standardEmailAddress(emailAddress) -> EmailAddress:
    '''
        return Name<Email>
    '''
    if not isinstance(emailAddress, EmailAddress):
        emailAddress = convert2EmailAddress(emailAddress)
    return emailAddress


EMAIL_ADDRESS_FILTER = []


class _Mailer():
    def __init__(self) -> None:
        self.smtp_host = SystemSetting.get(name='SMTP Host', default=IkConfig.get("Email", "mail.smtp"))
        self.smtp_port = int(SystemSetting.get(name='SMTP Port', default=IkConfig.get("Email", "mail.smtp.port")))
        self.smtp_use_ssl = SystemSetting.get(name='SMTP With SSL', default=IkConfig.get("Email", "mail.smtp.ssl")).lower() == 'yes'
        self.smtp_account = SystemSetting.get(name='SMTP Account', default=IkConfig.get("Email", "mail.username"))  # address
        self.smtp_password = SystemSetting.get(name='SMTP Password', default=IkConfig.get("Email", "mail.password"))
        self.sender_address = SystemSetting.get(name='SMTP Sender Address', default=IkConfig.get("Email", "mail.from"))
        self.sender_name = SystemSetting.get(name='SMTP Sender Name', default=IkConfig.get("Email", "mail.from.name"))
        if isNullBlank(self.sender_name) and isNotNullBlank(self.sender_address):
            self.sender_name = getEmailAddressName(self.sender_address)
        if isNotNullBlank(self.sender_name) and isNotNullBlank(self.sender_address):
            self.sender = formataddr(pair=(self.sender_name, self.sender_address))

        self.__bcc = self._get_default_mail_sender()

    # get default email sender
    def _get_default_mail_sender(self) -> EmailAddress:
        return EmailAddress(email=self.sender_address, name=self.sender_name)

    def _send(self, subject: str, content: str, to: list[EmailAddress], cc: list[EmailAddress], bcc: list[EmailAddress] = [], content_type='plain', attachments: list[MailAttch] = None) -> tuple:
        '''
            contentType=plain / html. Default is plain
            to/cc/bcc/attachments: list
        '''
        if content_type not in ('plain', 'html'):
            raise IkException('Parameter [content_type] should be "plain" or "html".')
        if to is None or len(to) == 0:
            raise IkException('Parameter [to] is mandatory.')

        server = None
        try:
            # filter disable receiver
            to_list = []
            for addr in to:
                if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                    for filter in EMAIL_ADDRESS_FILTER:
                        if filter(str(addr.email)):
                            to_list.append(str(addr))
                        else:
                            logger.info("Email recipient [%s] has been filtered." % str(addr.email))
                else:
                    to_list.append(str(addr))
            cc_list = []
            for addr in cc:
                if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                    for filter in EMAIL_ADDRESS_FILTER:
                        if filter(str(addr.email)):
                            if str(addr) not in to_list:
                                cc_list.append(str(addr))
                        else:
                            logger.info("Email recipient [%s] has been filtered." % str(addr.email))
                else:
                    cc_list.append(str(addr))
            bcc_list = []
            if isNotNullBlank(bcc):
                for addr in bcc:
                    if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                        for filter in EMAIL_ADDRESS_FILTER:
                            if filter(str(addr.email)):
                                if str(addr) not in to_list and str(addr) not in cc_list:
                                    bcc_list.append(str(addr))
                            else:
                                logger.info("Email recipient [%s] has been filtered." % str(addr.email))
                    else:
                        bcc_list.append(str(addr))
            bcc_list.append(str(self.__bcc))

            # prepare message
            msg = MIMEMultipart()
            msg['subject'] = subject
            if content_type == "html":
                msg.attach(MIMEText(content, _subtype='html', _charset='utf-8'))
            else:
                txt = MIMEText(content, 'plain', 'utf-8')
                msg.attach(txt)

            # attachments
            if isNotNullBlank(attachments) and len(attachments) > 0:
                for attachment in attachments:
                    file_path = attachment.file
                    file_name = os.path.basename(file_path)
                    part = MIMEApplication(open(file_path, 'rb').read())
                    part.add_header('Content-Disposition', 'attachment', filename=file_name)
                    msg.attach(part)
            # attachments - end

            # message receivers
            msg['From'] = str(standardEmailAddress(self._get_default_mail_sender()))
            msg['To'] = ','.join(to_list)
            if cc_list and len(cc_list) > 0:
                msg['Cc'] = ','.join(cc_list)
            if bcc_list and len(bcc_list) > 0:
                msg['Bcc'] = ','.join(bcc_list)
            if isNotNullBlank(cc_list) and len(cc_list) > 0:
                to_list = to_list + cc_list
            if isNotNullBlank(bcc_list) and len(bcc_list) > 0:
                to_list = to_list + bcc_list

            # send
            timeout = 30  # seconds
            connect_exception = None
            for i in range(2):
                try:
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=timeout) if self.smtp_use_ssl else smtplib.SMTP(
                        self.smtp_host, self.smtp_port, timeout=timeout)
                    connect_exception = None
                except Exception as e:
                    connect_exception = e
                    time.sleep(3)
            if connect_exception is not None:
                raise connect_exception
            # server.ehlo()
            # server.starttls()
            server.login(self.smtp_account, self.smtp_password)
            server.sendmail(msg['From'], to_list, msg.as_string())
            return True, "sent"
        except Exception as e:
            logger.error('Send email error:%s' % str(e))
            return False, str(e)
        finally:
            if server is not None:
                server.close()


Mailer = None
import core.utils.djangoUtils as ikDjangoUtils

if ikDjangoUtils.isRunDjangoServer():
    Mailer = du.instanceClass(_Mailer)


class __MailManager:
    """mailer manager class.

    Only allow to create one instance.

    """
    SEND_FAILED_RETRY_TIMES = 5

    def __init__(self) -> None:
        self.__senderThread = threading.Thread(target=self.__sendMailFromDB, args=())
        self.__senderThread.start()
        self.__queueLock = Lock()
        self.attempts_counter = {}

    # send email

    def __sendEmail(self, mail: Mail, to_addresses: list[EmailAddress], cc_addresses: list[EmailAddress], bcc_addresses: list[EmailAddress] = None, attachments: list[MailAttch] = None) -> tuple:
        if isNullBlank(to_addresses):
            return False, "No receiver found."

        is_success, message = _Mailer()._send(subject=mail.subject, content=mail.content, to=to_addresses, cc=cc_addresses, bcc=bcc_addresses,
                                              content_type=mail.type if mail.type == "html" else "plain", attachments=attachments)
        return is_success, message

    # check email database
    def __sendMailFromDB(self) -> None:
        """Method to continuously check the database and send pending emails."""
        while True:
            # get all pending status email
            pending_mails = Mail.objects.filter(sts__in=[Mail.STATUS_PENDING, Mail.STATUS_IN_PROGRESS]).order_by("id")

            if isNullBlank(pending_mails) or len(pending_mails) == 0:
                # if no pending status email, sleep 1m
                # logger.info("No pending emails to send. Sleeping for 1 second.")
                time.sleep(1)
                continue

            for mail in pending_mails:
                with transaction.atomic():
                    mail = Mail.objects.select_for_update().get(id=mail.id)
                    if mail.sts not in [Mail.STATUS_PENDING, Mail.STATUS_IN_PROGRESS]:
                        continue

                    # get receivers
                    to_addresses = []
                    cc_addresses = []
                    bcc_addresses = []
                    for mail_addr in MailAddr.objects.filter(mail=mail, type=MailAddr.TYPE_TO).order_by("seq"):
                        to_addresses.append(EmailAddress(email=mail_addr.address, name=mail_addr.name))
                    for mail_addr in MailAddr.objects.filter(mail=mail, type=MailAddr.TYPE_CC).order_by("seq"):
                        cc_addresses.append(EmailAddress(email=mail_addr.address, name=mail_addr.name))
                    for mail_addr in MailAddr.objects.filter(mail=mail, type=MailAddr.TYPE_BCC).order_by("seq"):
                        bcc_addresses.append(EmailAddress(email=mail_addr.address, name=mail_addr.name))

                    if isNullBlank(to_addresses) or len(to_addresses) == 0:
                        logger.debug("Mail ID [%s] no receiver." % mail.id)
                        return

                    # get Attachments
                    mail_attchs = MailAttch.objects.filter(mail=mail).order_by("seq")

                    # send email start
                    mail.send_ts = datetime.now()
                    # save status to in_progress
                    mail.sts = Mail.STATUS_IN_PROGRESS
                    mail.duration = None
                    mail.save()
                    is_success, message = self.__sendEmail(mail=mail, to_addresses=to_addresses, cc_addresses=cc_addresses, bcc_addresses=bcc_addresses, attachments=mail_attchs)
                    end_time = datetime.now()

                    # update mail status
                    if is_success:
                        mail.sts = Mail.STATUS_COMPLETE
                        mail.duration = round((end_time - mail.send_ts).total_seconds() * 1000)
                        mail.save()
                        logger.info(f"Email ID [{mail.id}] sent successfully takes {mail.duration} ms.")
                        self.attempts_counter.pop(mail.id, None)
                    else:
                        logger.warning(f"Email ID [{mail.id}] sent {self.attempts_counter.get(mail.id, 1)} times failed: {message}")
                        if self.attempts_counter.get(mail.id, 1) < self.SEND_FAILED_RETRY_TIMES:
                            # if send failed, attempts counter = 1
                            self.attempts_counter.update({mail.id: self.attempts_counter.get(mail.id, 1) + 1})
                        else:
                            mail.send_ts = None
                            mail.sts = Mail.STATUS_ERROR
                            mail.error = message
                            mail.save()
                            self.attempts_counter.pop(mail.id, None)

    # API: send email & save result
    def send(self, sender, subject, to, cc=None, bcc=None, content=None, template_file=None, template_parameter=None, description=None, attachments=None,
             send_in_background: bool = True, send_one_by_one: bool = False, type=None) -> Boolean2:
        '''
            sender: str
            subject: str
            to/cc/bcc: str(xxx@xxx.com) | int(system user ID) | EmailAddress(abc <xxx@xxx.com>) | list
            content: str
            template_file: str
            template_parameter: dict
            description: str
            attachments: str | list
            send_in_background: bool
            send_one_by_one: bool
            type: str, for mail001 & mail002
        '''
        if isNullBlank(content) and isNullBlank(template_file):
            return Boolean2(False, 'Send email error, no content.')
        if isNullBlank(to) or (isinstance(to, list) and len(to) == 0):
            return Boolean2(False, 'The recipient of the email is mandatory.')

        # distinct
        if isinstance(to, list):
            to = list(dict.fromkeys(to))
        if isinstance(cc, list):
            cc = list(dict.fromkeys(cc))
        if isinstance(bcc, list):
            bcc = list(dict.fromkeys(bcc))

        mail_type = None
        try:
            if isNotNullBlank(type):
                if type == Mail.MAIL_TYPE_HTML:
                    mail_type = Mail.MAIL_TYPE_HTML
                    if isNullBlank(content):
                        content = templateManager.loadTemplateFile(template_file, template_parameter)
                else:
                    mail_type = Mail.MAIL_TYPE_TEXT
            else:
                if isNotNullBlank(template_file):  # 1. html email
                    mail_type = Mail.MAIL_TYPE_HTML
                    # read templates
                    content = templateManager.loadTemplateFile(template_file, template_parameter)
                else:  # 2. text mail
                    mail_type = Mail.MAIL_TYPE_TEXT

            # get to & cc information
            to_dict_list = self.__getEmailAddressList(to)
            cc_dict_list = self.__getEmailAddressList(cc)
            bcc_dict_list = self.__getEmailAddressList(bcc)
            if isNullBlank(to_dict_list) or len(to_dict_list) == 0:
                logger.info("Send pass, to_dict_list is empty. to : %s" % str(to))
                return Boolean2(False, "Send email failure, To [%s] has been filtered." % str(to).replace("[", " ").replace("]", " "))

            if send_in_background:  # run background, save to database
                if send_one_by_one and isinstance(to_dict_list, list) and len(to_dict_list) > 1:  # split to
                    b = None
                    for to_obj in to_dict_list:
                        b = self.__add(sender=sender, subject=subject, content=content, template_file=template_file,
                                       template_parameter=template_parameter, to=to_obj, cc=cc_dict_list, bcc=bcc_dict_list, description=description, attachments=attachments)
                    return b
                else:
                    return self.__add(sender=sender, subject=subject, content=content, template_file=template_file, template_parameter=template_parameter, to=to_dict_list, cc=cc_dict_list, bcc=bcc_dict_list, description=description, attachments=attachments)

            to_dict_list_str = [str(address) for address in to_dict_list]
            cc_dict_list_str = [str(address) for address in cc_dict_list]
            bcc_dict_list_str = [str(address) for address in bcc_dict_list]

            # Use transactions to store Mail and MailAddr
            # send email and save
            if send_one_by_one:  # split to send
                for to_dict_obj in to_dict_list:
                    # get email & email attachment
                    mail_record, mail_attchs = self.__newMailAndAttchs(sender=sender, subject=subject, content=content, type=mail_type,
                                                                       sts=Mail.STATUS_PENDING, dsc=description, queue=send_in_background, attachments=attachments)
                    mail_record.send_ts = datetime.now()
                    # 1. send
                    is_success, message = self.__sendEmail(mail=mail_record, to_addresses=[to_dict_obj],
                                                           cc_addresses=cc_dict_list, bcc_addresses=bcc_dict_list_str, attachments=mail_attchs)
                    if is_success:
                        mail_record.sts = Mail.STATUS_COMPLETE
                        mail_record.duration = round((datetime.now() - mail_record.send_ts).total_seconds() * 1000)
                        logger.info("Send mail [%s], to %s, cc %s, bcc %s successfully takes %s ms.", subject,
                                    to_dict_list_str, cc_dict_list_str, bcc_dict_list_str, mail_record.duration)
                    else:
                        mail_record.sts = Mail.STATUS_ERROR
                        mail_record.error = message
                        logger.warn("Send mail [%s], to %s, cc %s, bcc %s failed: %s", subject, to_dict_list_str, cc_dict_list_str, bcc_dict_list_str, message)

                    # 2. save send result
                    with transaction.atomic():
                        # create Mail record
                        mail_record.save()

                        # create MailAddr to records
                        for idx, email_addr in enumerate([to_dict_obj]):
                            MailAddr.objects.create(
                                mail=mail_record,
                                type=MailAddr.TYPE_TO,
                                name=email_addr.name,
                                address=email_addr.email,
                                seq=idx + 1
                            )

                        # create MailAddr cc records
                        for idx, email_addr in enumerate(cc_dict_list):
                            MailAddr.objects.create(
                                mail=mail_record,
                                type=MailAddr.TYPE_CC,
                                name=email_addr.name,
                                address=email_addr.email,
                                seq=idx + 1
                            )

                        # create MailAddr cc records
                        for idx, email_addr in enumerate(bcc_dict_list):
                            MailAddr.objects.create(
                                mail=mail_record,
                                type=MailAddr.TYPE_BCC,
                                name=email_addr.name,
                                address=email_addr.email,
                                seq=idx + 1
                            )

                        # create MailAttch records if have
                        if isNotNullBlank(mail_attchs):
                            for mail_attch in mail_attchs:
                                mail_attch.save()

                    logger.info("Save mail [%s], to %s, cc %s, bcc %s successfully.", subject, to_dict_list_str, cc_dict_list_str, bcc_dict_list_str)
            else:
                # get email & email attachment
                mail_record, mail_attchs = self.__newMailAndAttchs(sender=sender, subject=subject, content=content, type=mail_type,
                                                                   sts=Mail.STATUS_PENDING, dsc=description, queue=send_in_background, attachments=attachments)
                mail_record.send_ts = datetime.now()

                # 1. send
                is_success, message = self.__sendEmail(mail=mail_record, to_addresses=to_dict_list, cc_addresses=cc_dict_list,
                                                       bcc_addresses=bcc_dict_list_str, attachments=mail_attchs)
                if is_success:
                    mail_record.sts = Mail.STATUS_COMPLETE
                    mail_record.duration = round((datetime.now() - mail_record.send_ts).total_seconds() * 1000)
                    logger.info("Send mail [%s], to %s, cc %s, bcc %s successfully takes %s ms.", subject,
                                to_dict_list_str, cc_dict_list_str, bcc_dict_list_str, mail_record.duration)
                else:
                    mail_record.sts = Mail.STATUS_ERROR
                    mail_record.error = message
                    logger.warn("Send mail [%s], to %s, cc %s, bcc %s failed: %s", subject, to_dict_list_str, cc_dict_list_str, bcc_dict_list_str, message)

                # 2. save send result
                with transaction.atomic():
                    # create Mail record
                    mail_record.save()

                    # create MailAddr to records
                    for idx, email_addr in enumerate(to_dict_list):
                        MailAddr.objects.create(
                            mail=mail_record,
                            type=MailAddr.TYPE_TO,
                            name=email_addr.name,
                            address=email_addr.email,
                            seq=idx + 1
                        )

                    # create MailAddr cc records
                    for idx, email_addr in enumerate(cc_dict_list):
                        MailAddr.objects.create(
                            mail=mail_record,
                            type=MailAddr.TYPE_CC,
                            name=email_addr.name,
                            address=email_addr.email,
                            seq=idx + 1
                        )

                    # create MailAddr cc records
                    for idx, email_addr in enumerate(bcc_dict_list):
                        MailAddr.objects.create(
                            mail=mail_record,
                            type=MailAddr.TYPE_BCC,
                            name=email_addr.name,
                            address=email_addr.email,
                            seq=idx + 1
                        )

                    # create MailAttch records if have
                    if isNotNullBlank(mail_attchs):
                        for mail_attch in mail_attchs:
                            mail_attch.save()

                logger.info("Save mail [%s], to %s, cc %s, bcc %s successfully.", subject, to_dict_list_str, cc_dict_list_str, bcc_dict_list_str)
            return Boolean2(True, mail_record)
        except DatabaseError as e:
            logger.error("Save mail [%s] failed: %s", subject, str(e))
            logger.fatal(e, exc_info=True)
        except Exception as e:
            logger.error("Send mail [%s] failed: %s", subject, str(e))
            logger.fatal(e, exc_info=True)
        return Boolean2(False, "Send email failed.")

    # just save mail information to queue
    def __add(self, sender, subject, content, template_file, template_parameter, to, cc, bcc, description=None, attachments=None) -> Boolean2:
        '''
            sender: str
            subject: str
            content: str
            template_file: str
            template_parameter: dict
            to/cc/bcc: str(xxx@xxx.com) | int(system user ID) | EmailAddress(abc <xxx@xxx.com>) | list
            description: str
            attachments: str | list
        '''
        if isNullBlank(content) and isNullBlank(template_file):
            return Boolean2(False, 'send email error, no content.')

        mail_type = None
        if isNotNullBlank(template_file):  # 1. html email
            mail_type = Mail.MAIL_TYPE_HTML
            # read templates
            content = templateManager.loadTemplateFile(template_file, template_parameter)
        else:  # 2. text mail
            mail_type = Mail.MAIL_TYPE_TEXT

        return self.__saveEmail(sender, subject, content, mail_type, to, cc, bcc, description, attachments)

    def __saveEmail(self, sender, subject, content, mail_type: str, to, cc, bcc=None, description: str = None, attachments=None) -> Boolean2:
        '''
            sender: str
            subject: str
            content: str
            mail_type: str
            to/cc/bcc: str(xxx@xxx.com) | int(system user ID) | EmailAddress(abc <xxx@xxx.com>) | list
            description: str
            attachments: str | list
        '''
        # get to & cc information
        if isNullBlank(to) and len(to) == 0 and isNullBlank(cc) and len(cc) == 0:
            return Boolean2(False, 'The recipient of the email is mandatory.')

        to_dict_list = self.__getEmailAddressList(to)
        cc_dict_list = self.__getEmailAddressList(cc)
        bcc_dict_list = self.__getEmailAddressList(bcc)
        if isNullBlank(to_dict_list) or len(to_dict_list) == 0:
            logger.info("__saveEmail pass , to_dict_list is empty. to : %s" % str(to))
            return Boolean2(False, "Save email failure, To [%s] has been filtered." % str(to).replace("[", " ").replace("]", " "))

        # remove same in to, cc, bcc
        to_dict_set = set([str(email) for email in to_dict_list])
        cc_dict_list = [email for email in cc_dict_list if str(email) not in to_dict_set]
        to_and_cc_set = set([str(email) for email in to_dict_list + cc_dict_list])
        bcc_dict_list = [email for email in bcc_dict_list if str(email) not in to_and_cc_set]

        # Use transactions to store Mail and MailAddr
        try:
            self.__queueLock.acquire()
            # 1. save database
            mail_record = None
            with transaction.atomic():
                # create Mail record
                mail_record = Mail(
                    sender=sender,
                    request_ts=datetime.now(),
                    subject=subject,
                    content=content,
                    type=mail_type,
                    sts=Mail.STATUS_PENDING,
                    queue=True,
                    dsc=description
                )
                mail_record.save()

                # create MailAddr to records
                for idx, email_addr in enumerate(to_dict_list):
                    MailAddr.objects.create(
                        mail=mail_record,
                        type=MailAddr.TYPE_TO,
                        name=email_addr.name,
                        address=email_addr.email,
                        seq=idx + 1
                    )

                # create MailAddr cc records
                for idx, email_addr in enumerate(cc_dict_list):
                    MailAddr.objects.create(
                        mail=mail_record,
                        type=MailAddr.TYPE_CC,
                        name=email_addr.name,
                        address=email_addr.email,
                        seq=idx + 1
                    )

                # create MailAddr bcc records
                for idx, email_addr in enumerate(bcc_dict_list):
                    MailAddr.objects.create(
                        mail=mail_record,
                        type=MailAddr.TYPE_BCC,
                        name=email_addr.name,
                        address=email_addr.email,
                        seq=idx + 1
                    )

                # create MailAttch records if have
                mail_attchs = None
                if isNotNullBlank(attachments):
                    mail_attchs = []
                    if not isinstance(attachments, list):
                        attachments = [attachments]
                    import core.core.fs as ikfs
                    for idx, file_path in enumerate(attachments):
                        ab_file_path = file_path  # 1. attachments is abstract path
                        # 2. attachments is relative path
                        if ":" not in file_path and not file_path.startswith("/"):
                            ab_file_path = os.path.join(ikfs.getRootFolder(), file_path)

                        file_size = os.path.getsize(ab_file_path)
                        mail_attchs.append(MailAttch.objects.create(
                            mail=mail_record,
                            file=file_path,
                            size=file_size,
                            seq=idx + 1
                        ))

            to_dict_list_str = [str(address) for address in to_dict_list]
            cc_dict_list_str = [str(address) for address in cc_dict_list]
            bcc_dict_list_str = [str(address) for address in bcc_dict_list]
            logger.info("Save mail [%s], to %s, cc %s, bcc %s successfully.", subject, to_dict_list_str, cc_dict_list_str, bcc_dict_list_str)
            return Boolean2(True, mail_record)
        except DatabaseError as e:
            logger.error("Save mail [%s] failed: %s", subject, str(e))
            logger.fatal(e, exc_info=True)
            return Boolean2(False, "Save mail failure.")
        finally:
            self.__queueLock.release()

    def __newMailAndAttchs(self, sender, subject, content, type, sts, queue, dsc=None, attachments=None) -> tuple:
        attch_limit_size = None if isNullBlank(SystemSetting.get("EMAIL_ATTACH_TOTAL_SIZE_LIMIT")) else int(SystemSetting.get("EMAIL_ATTACH_TOTAL_SIZE_LIMIT"))
        mail_record = Mail(
            sender=sender,
            request_ts=datetime.now(),
            subject=subject,
            content=content,
            type=type,
            sts=sts,
            queue=queue,
            dsc=dsc
        )
        # attachment
        mail_attchs = None
        if isNotNullBlank(attachments):
            mail_attchs = []
            if not isinstance(attachments, list):
                attachments = [attachments]
            total_file_size = 0
            for idx, file_path in enumerate(attachments):
                ab_file_path = file_path  # 1. attachments is abstract path
                # 2. attachments is relative path
                if ":" not in file_path and not file_path.startswith("/"):
                    ab_file_path = os.path.join(ikfs.getRootFolder(), file_path)

                file_size = os.path.getsize(ab_file_path)
                total_file_size += file_size
                mail_attchs.append(MailAttch(
                    mail=mail_record,
                    file=file_path,
                    size=file_size,
                    seq=idx + 1
                ))
            if isNotNullBlank(attch_limit_size) and attch_limit_size < (total_file_size / (1024 * 1024)):
                raise IkValidateException("The total attachment size can only be less than %s MB, total has %s MB.", (str(attch_limit_size), str(total_file_size / (1024 * 1024))))
        return mail_record, mail_attchs

    def __getEmailAddressList(self, obj) -> list:
        email_addr_dict = []
        if isNotNullBlank(obj):
            if isinstance(obj, list):  # user id list or address list
                for addr in obj:
                    if isinstance(addr, EmailAddress):
                        if isNullBlank(addr.email):
                            logger.error("The email of %s is empty." % str(addr))
                            continue
                        if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                            for filter in EMAIL_ADDRESS_FILTER:
                                if filter(str(addr.email)):
                                    email_addr_dict.append(addr)
                                else:
                                    logger.info("Email recipient [%s] has been filtered." % str(addr.email))
                        else:
                            email_addr_dict.append(addr)
                    elif isinstance(addr, int) or addr.isdigit():  # user id
                        from core.user.userManager import getUserEmailAddress
                        email_addr = getUserEmailAddress(addr)
                        if isNullBlank(email_addr.email):
                            logger.error("The email of %s is empty." % str(email_addr))
                            continue
                        if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                            for filter in EMAIL_ADDRESS_FILTER:
                                if filter(str(email_addr.email)):
                                    email_addr_dict.append(email_addr)
                                else:
                                    logger.info("Email recipient [%s] has been filtered." % str(email_addr.email))
                        else:
                            email_addr_dict.append(email_addr)
                    elif isinstance(addr, str):  # str list
                        for ad in addr.split(','):  # '1, 2, 3'
                            if isinstance(ad, int) or ad.isdigit():  # user id
                                from core.user.userManager import \
                                    getUserEmailAddress
                                email_addr = getUserEmailAddress(ad)
                                if isNullBlank(email_addr.email):
                                    logger.error("The email of %s is empty." % str(email_addr))
                                    continue

                                if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                                    for filter in EMAIL_ADDRESS_FILTER:
                                        if filter(str(email_addr.email)):
                                            email_addr_dict.append(email_addr)
                                        else:
                                            logger.info("Email recipient [%s] has been filtered." % str(email_addr.email))
                                else:
                                    email_addr_dict.append(email_addr)
                            else:
                                if isNullBlank(standardEmailAddress(ad).email):
                                    logger.error("The email of %s is empty." % str(standardEmailAddress(ad)))
                                    continue
                                if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                                    for filter in EMAIL_ADDRESS_FILTER:
                                        if filter(str(ad)):
                                            email_addr_dict.append(standardEmailAddress(ad))
                                        else:
                                            logger.info("Email recipient [%s] has been filtered." % str(ad))
                                else:
                                    email_addr_dict.append(standardEmailAddress(ad))

            elif isinstance(obj, EmailAddress):
                if isNullBlank(obj.email):
                    logger.error("The email of %s is empty." % str(obj))
                    return
                if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                    for filter in EMAIL_ADDRESS_FILTER:
                        if filter(str(obj.email)):
                            email_addr_dict = [obj]
                        else:
                            logger.info("Email recipient [%s] has been filtered." % str(obj.email))
                else:
                    email_addr_dict = [obj]
            elif isinstance(obj, int) or obj.isdigit():  # user id
                from core.user.userManager import getUserEmailAddress
                email_addr = getUserEmailAddress(obj)
                if isNullBlank(email_addr.email):
                    logger.error("The email of %s is empty." % str(email_addr))
                    return

                if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                    for filter in EMAIL_ADDRESS_FILTER:
                        if filter(str(email_addr.email)):
                            email_addr_dict = [email_addr]
                        else:
                            logger.info("Email recipient [%s] has been filtered." % str(email_addr.email))
                else:
                    email_addr_dict = [email_addr]
            elif isinstance(obj, str):  # str list
                for addr in obj.split(','):  # '1, 2, 3'
                    addr = addr.strip()
                    if isinstance(addr, int) or addr.isdigit():  # user id
                        from core.user.userManager import getUserEmailAddress
                        email_addr = getUserEmailAddress(addr)
                        if isNullBlank(email_addr.email):
                            logger.error("The email of %s is empty." % str(email_addr))
                            continue
                        if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                            for filter in EMAIL_ADDRESS_FILTER:
                                if filter(str(email_addr.email)):
                                    email_addr_dict.append(email_addr)
                                else:
                                    logger.info("Email recipient [%s] has been filtered." % str(email_addr.email))
                        else:
                            email_addr_dict.append(email_addr)
                    else:
                        if isNullBlank(standardEmailAddress(addr).email):
                            logger.error("The email of %s is empty." % str(standardEmailAddress(addr)))
                            continue
                        if EMAIL_ADDRESS_FILTER and len(EMAIL_ADDRESS_FILTER) > 0:
                            for filter in EMAIL_ADDRESS_FILTER:
                                if filter(str(addr)):
                                    email_addr_dict.append(standardEmailAddress(addr))
                                else:
                                    logger.info("Email recipient [%s] has been filtered." % str(addr))
                        else:
                            email_addr_dict.append(standardEmailAddress(addr))
            else:
                raise IkException('Unknown email address: %s' % obj)
        return email_addr_dict


# create one instance only
MailManager = du.instanceClass(__MailManager)
