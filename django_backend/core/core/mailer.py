import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from core.core.exception import IkException
from core.sys.systemSetting import SystemSetting
from core.utils import strUtils
from django.template import loader
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


# YL.ikyo, 2023-03-09 - start
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


# YL.ikyo, 2023-03-09 - end


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
    # YL.ikyo, 2023-04-06 - start
    if not isinstance(emailAddress, EmailAddress):
        emailAddress = convert2EmailAddress(emailAddress)
    return str(emailAddress)
    # YL.ikyo, 2023-04-06 - end


class Mailer():

    def __init__(self) -> None:
        self.smtpHost = getSetting(name='SMTP Host', default=IkConfig.get("Email", "mail.smtp"))
        self.smtpPort = int(getSetting(name='SMTP Port', default=IkConfig.get("Email", "mail.smtp.port")))
        self.smtpWithSSL = getSetting(name='SMTP With SSL', default=IkConfig.get("Email", "mail.smtp.ssl")).lower() == 'yes'
        self.smtpAccount = getSetting(name='SMTP Account', default=IkConfig.get("Email", "mail.username"))
        self.smtpPassword = getSetting(name='SMTP Password', default=IkConfig.get("Email", "mail.password"))
        self.senderAddress = getSetting(name='SMTP Sender Address', default=IkConfig.get("Email", "mail.from"))
        self.senderName = getSetting(name='SMTP Sender Name', default=IkConfig.get("Email", "mail.from,name"))
        if self.senderName is None or self.senderName.strip() == '' and self.senderAddress is not None:
            self.senderName = getEmailAddressName(self.senderAddress)
        self.sender = formataddr(pair=(self.senderName, self.senderAddress))

    # YL.ikyo, 2023-03-16
    # get default email sender
    def getDefaultMailSender(self) -> EmailAddress:
        mailFrom = SystemSetting().get("mail.from")
        mailFromName = SystemSetting().get("mail.from.name")
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
        # YL.ikyo, 2023-03-16 UPDATE, add EmailAddress check - start
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
        # YL.ikyo, 2023-03-16 - end

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
        msg['From'] = standardEmailAddress(
            sendFrom) if sendFrom is not None else self.sender if self.sender is not None else self.getDefaultMailSender()
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

if __name__ == '__main__':
    pass
