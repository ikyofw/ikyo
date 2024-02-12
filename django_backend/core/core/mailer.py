import logging, time, os, threading
import smtplib
from threading import Lock
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from django.template import loader

from core.core.exception import IkException
from core.sys.systemSetting import SystemSetting
from core.utils import strUtils, templateManager
from core.utils.langUtils import validateEmail
from iktools import IkConfig

logger = logging.getLogger('ikyo')


def getEmailName(name) -> str:
    if name is None:
        return None
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


def toEmailAddressList(addrsStr) -> list:
    addressList = []
    if strUtils.isEmpty(addrsStr):
        return addressList
    addrArr = addrsStr.split(";")
    for addr in addrArr:
        addr = addr.strip()
        if not strUtils.isEmpty(addr):
            name = addr[:addr.index("<")].strip()
            email = addr[addr.index("<") + 1:len(addr) - 1].strip()
            addressList.append(convert2EmailAddress(email) if strUtils.isEmpty(name) else EmailAddress(email, name))
    return addressList


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


def standardEmailAddress(emailAddress) -> str:
    '''
        return Name<Email>
    '''
    if not isinstance(emailAddress, EmailAddress):
        emailAddress = convert2EmailAddress(emailAddress)
    return str(emailAddress)


class _Mailer():

    def __init__(self) -> None:
        self.smtpHost = SystemSetting.get(name='SMTP Host', default=IkConfig.get("Email", "mail.smtp"))
        self.smtpPort = int(SystemSetting.get(name='SMTP Port', default=IkConfig.get("Email", "mail.smtp.port")))
        self.smtpWithSSL = SystemSetting.get(name='SMTP With SSL', default=IkConfig.get("Email", "mail.smtp.ssl")).lower() == 'yes'
        self.smtpAccount = SystemSetting.get(name='SMTP Account', default=IkConfig.get("Email", "mail.username"))
        self.smtpPassword = SystemSetting.get(name='SMTP Password', default=IkConfig.get("Email", "mail.password"))
        self.senderAddress = SystemSetting.get(name='SMTP Sender Address', default=IkConfig.get("Email", "mail.from"))
        self.senderName = SystemSetting.get(name='SMTP Sender Name', default=IkConfig.get("Email", "mail.from,name"))
        if self.senderName is None or self.senderName.strip() == '' and self.senderAddress is not None:
            self.senderName = getEmailAddressName(self.senderAddress)
        self.sender = formataddr(pair=(self.senderName, self.senderAddress))

    # get default email sender
    def getDefaultMailSender(self) -> EmailAddress:
        mailFrom = SystemSetting.get("mail.from")
        mailFromName = SystemSetting.get("mail.from.name")
        if strUtils.isEmpty(mailFromName):
            mailFromName = "IKYO"
        return EmailAddress(mailFrom, mailFromName)

    def sendHtmlMail(self, subject='', content='', sendFrom=None, to=None, cc=None, attachments=None) -> bool:
        return self.send(subject=subject, content=content, contentType='html', sendFrom=sendFrom, to=to, cc=cc, attachments=attachments)

    def send(self, subject='', content='', contentType='plain', sendFrom=None, to=None, cc=None, attachments=None) -> bool:
        '''
            contentType=plain / html. Default is plain
            to/cc/attachments: str or a list
        '''
        if contentType not in ('plain', 'html'):
            raise Exception('Parameter [contentType] should be "plain" or "html".')
        if to is None or len(to) == 0:
            raise IkException('Parameter [to] is mandatory.')
        sendTo = []
        if isinstance(to, EmailAddress):
            sendTo.append(str(to))
        elif isinstance(to, str):
            for addr in to.split(','):
                sendTo.append(standardEmailAddress(addr))
        elif isinstance(to, list):
            for addr in to:
                if isinstance(addr, EmailAddress):
                    sendTo.append(str(addr))
                else:
                    sendTo.append(standardEmailAddress(addr))
        else:
            raise IkException('Unknown email address: %s' % to)
        ccTo = []
        if isinstance(cc, EmailAddress):
            ccTo.append(str(cc))
        elif cc is not None and len(cc) > 0:
            if isinstance(cc, str):
                for addr in cc.split(','):
                    ccTo.append(standardEmailAddress(addr))
            elif isinstance(cc, list):
                for addr in cc:
                    if isinstance(addr, EmailAddress):
                        ccTo.append(str(addr))
                    else:
                        ccTo.append(standardEmailAddress(addr))
            else:
                raise IkException('Unknown email address: %s' % cc)

        # prepare message
        msg = MIMEMultipart()
        msg['subject'] = subject
        if contentType == "html":
            msg.attach(MIMEText(content, _subtype='html', _charset='utf-8'))
        else:
            txt = MIMEText(content, 'plain', 'utf-8')
            msg.attach(txt)
        # attachments
        if attachments and len(attachments) > 0:
            if isinstance(attachments, list):
                for attachment in attachments:
                    file_path = attachment
                    file_name = os.path.basename(file_path)
                    part = MIMEApplication(open(file_path, 'rb').read())
                    part.add_header('Content-Disposition', 'attachment', filename=file_name)
                    msg.attach(part)
            else:
                file_path = attachments
                file_name = os.path.basename(file_path)
                part = MIMEApplication(open(file_path, 'rb').read())
                part.add_header('Content-Disposition', 'attachment', filename=file_name)
                msg.attach(part)
        # attachments - end

        # message receivers
        msg['From'] = standardEmailAddress(sendFrom) if sendFrom is not None else self.sender if self.sender is not None else self.getDefaultMailSender()
        msg['To'] = ','.join(sendTo)
        if ccTo and len(ccTo) > 0:
            msg['Cc'] = ','.join(ccTo)
        # send
        server = None
        try:
            server = smtplib.SMTP_SSL(self.smtpHost, self.smtpPort) if self.smtpWithSSL \
                else smtplib.SMTP(self.smtpHost, self.smtpPort)
            # server.ehlo()
            # server.starttls()
            server.login(self.smtpAccount, self.smtpPassword)
            server.sendmail(msg['From'], sendTo, msg.as_string())
            return True
        except Exception as e:
            logger.error('Send email error:%s' % e)
            return False
        finally:
            server.quit()

    def sendFromTemplate(self, subject, templateFile, templateParameters=None, contentType='plain', sendFrom=None, to=None, cc=None, attachments=None) -> bool:
        '''
            templateParameters: dict
            contentType=plain / html. Default is plain
            to/cc/attachments: str or a list
        '''
        if templateFile is None:
            raise IkException('Parameter [templateFile] is mandatory.')
        t = loader.get_template(templateFile)
        content = t.render({} if templateParameters is None else templateParameters)
        return self.send(subject=subject, content=content, contentType=contentType, sendFrom=sendFrom, to=to, cc=cc, attachments=attachments)


Mailer = _Mailer()


class _MailQueueData:
    """mail data class.

    Attributes:
        subject (str): Mail subject.
        toUserIDs (:obj:`list`): Send to users' IDs.
        ccUserIDs (:obj:`list`): CC to users' IDs.
        templateFilename (str): Mail content template file name.
        parameters (:obj:`dict`): Mail content template file parameters.

    """

    def __init__(self, subject, toUserIDs, ccUserIDs, templateFilename, parameters):
        self.subject = subject
        self._toUserIDs = toUserIDs
        self._ccUserIDs = ccUserIDs
        self._templateFilename = templateFilename
        self._parameters = parameters
        self.__bcc2Self = [EmailAddress(email=SystemSetting.get('mail.username'), name='Ikyo')]

        # get email to address
        errorMessage, send2EmailList = self.__getEmailAddresses(toUserIDs)
        if len(send2EmailList) == 0:
            raise IkException(errorMessage)
        self.send2EmailList = send2EmailList
        # get email cc to address
        cc2EmailList = None
        if ccUserIDs is not None and len(ccUserIDs) > 0:
            errorMessage2, cc2EmailList = self.__getEmailAddresses(ccUserIDs)
            if errorMessage == '' or errorMessage is None:
                errorMessage = errorMessage2
            else:
                errorMessage += errorMessage2
        if cc2EmailList is not None:
            cc2EmailList.extend(self.__bcc2Self)
        else:
            cc2EmailList = self.__bcc2Self
        self.cc2EmailList = cc2EmailList
        if errorMessage is not None and errorMessage != '':
            logger.warning(errorMessage)
        self.mailAddressErrorMessage = errorMessage if errorMessage else None

        # read templates
        self.mailContent = templateManager.loadTemplateFile(templateFilename, parameters)

    def __getEmailAddresses(self, userIDs) -> tuple:
        errorMessage = ''
        emails = UserManager.getUserEmailAddresses(userIDs)
        for i in range(len(emails)):
            email = emails[i]
            if emails is None or str(email).strip() == '':
                # no email
                if errorMessage != '':
                    errorMessage += ' '
                errorMessage += "%s's email is not define." % email.name
                emails[i] = None
            elif not validateEmail(email.email):
                # incorrect email
                if errorMessage != '':
                    errorMessage += ' '
                errorMessage += "%s's email [%s] is incorrect." % (email.name, email.email)
                emails[i] = None
        if errorMessage == '':
            return (None, emails)
        emails2 = []
        for email in emails:
            if email is not None:
                emails2.append(email)
        return (errorMessage, emails2)


class __MailQueue:
    """mailer queue class.

    Only allow to create one instance.

    """
    SEND_FAILED_RETRY_TIMES = 5

    def __init__(self) -> None:
        self.__mailFrom = SystemSetting.get(name='SMTP Sender Address', default=IkConfig.get("Email", "mail.from"))
        self.__bcc2Self = [EmailAddress(email=SystemSetting.get(name='SMTP Account', default=IkConfig.get("Email", "mail.username")), name='Ikyo')]
        self.__mailQueues = []
        self.__queueLock = Lock()
        self.__senderThread = threading.Thread(target=self.__sendMailFromPool, args=())
        self.__senderThread.start()

    def send(self, subject, toUserIDs, ccUserIDs, templateFilename, parameters) -> None:
        """Send mail

        Args:
            subject (str): Mail subject.
            toUserIDs (:obj:`list`): Receiver's IDs (int list).
            ccUserIDs (:obj:`list`): CC users' IDs (int list).
            templateFilename (str): Email template file name.
            parameters (dict): Email template file parameters.

        """
        self.__queueLock.acquire()
        try:
            self.__mailQueues.append(_MailQueueData(subject, toUserIDs, ccUserIDs, templateFilename, parameters))
        finally:
            self.__queueLock.release()

    @property
    def queueSize(self) -> int:
        """Get mail queue size.

        Returns:
            Return Mail queue's size.
        """
        return len(self.__mailQueues)

    @property
    def queue(self) -> list:
        """Get mail queue.
        
        Returns:
            Return Mail queue.
        """
        return self.__mailQueues

    def clearQueue(self) -> None:
        """Clean mail queue.
        
        """
        try:
            self.__queueLock.acquire()
            self.__mailQueues.clear()
        finally:
            self.__queueLock.release()

    def __sendMail(self, mailData: _MailQueueData) -> tuple:
        '''
        '''
        if mailData.send2EmailList is None or len(mailData.send2EmailList) == 0:
            return (False, 'No sender found.')
        isSuccess = Mailer.sendHtmlMail(subject=mailData.subject, content=mailData.mailContent, sendFrom=self.__mailFrom, to=mailData.send2EmailList, cc=mailData.cc2EmailList)
        errorMessage = None
        if mailData.mailAddressErrorMessage:
            errorMessage = mailData.mailAddressErrorMessage
        if isSuccess:
            message = 'sent' if errorMessage == '' else 'sent with these errors: %s' % errorMessage
            logger.info(message)
            return (True, message)
        else:
            message = 'sent failed.' if errorMessage == '' else 'sent failed with these errors: %s' % errorMessage
            logger.error(message)
            return (False, message)

    def __sendMailFromPool(self) -> None:
        mailSendTimes = {}
        try:
            while True:
                if len(self.__mailQueues) == 0:
                    try:
                        time.sleep(3)
                    except Exception as e:
                        logger.error('Sleep faioed: %s' % str(e))
                        pass
                if len(self.__mailQueues) > 0:
                    try:
                        mailData = None
                        try:
                            self.__queueLock.acquire()
                            mailData = self.__mailQueues.pop()
                        finally:
                            self.__queueLock.release()
                        if mailData is not None:
                            try:
                                isSuccess, message = self.__sendMail(mailData)
                                if isSuccess:
                                    logger.debug('Send mail success. Message=%s' % message)
                                else:
                                    logger.error('Send mail failed. Message=%s' % message)
                            except Exception as e:
                                # add to last and try again later
                                self.__queueLock.acquire()
                                try:
                                    retryTimes = mailSendTimes.get(mailData, 0)
                                    retryTimes += 1
                                    mailSendTimes[mailData] = retryTimes
                                    if retryTimes >= __MailQueue.SEND_FAILED_RETRY_TIMES:
                                        logger.error('send mail [%s] to [%s] failed (tried %s of %s).' \
                                                     % (mailData.subject, mailData.send2EmailList, retryTimes, __MailQueue.SEND_FAILED_RETRY_TIMES))
                                        del mailSendTimes[mailData]
                                    else:
                                        logger.error('send mail [%s] to [%s] failed. Then add it to queue and try again later (tried %s of %s).' \
                                                     % (mailData.subject, mailData.send2EmailList, retryTimes, __MailQueue.SEND_FAILED_RETRY_TIMES))
                                        self.__mailQueues.append(mailData)  # TODO: if tried too many times, then ignore ?
                                finally:
                                    self.__queueLock.release()
                                pass
                    except Exception as e:
                        logger.error('Send mail failed: %s' % str(e))
                        logger.fatal(e, exc_info=True)
        except Exception as e:
            logger.fatal(e, exc_info=True)
        finally:
            mailSendTimes.clear()


# create one instance only
MailQueue = __MailQueue()
