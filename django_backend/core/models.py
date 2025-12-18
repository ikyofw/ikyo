from datetime import datetime
from django.utils import timezone

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.db.model import IDModel, addModelHistoryFilter

from .const import TABLE_NAME_PREFIX


class Menu(IDModel):
    menu_nm = models.CharField(unique=True, max_length=100, verbose_name='Menu Name')
    menu_caption = models.CharField(max_length=100, verbose_name='Menu Caption')
    screen_nm = models.CharField(max_length=200, null=True, blank=True, verbose_name='Screen Name')
    parent_menu_id = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='Parent Menu ID')
    enable = models.BooleanField(null=True, blank=True, verbose_name="Menu Enable")
    order_no = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='Order No')
    is_free_access = models.BooleanField(null=True, blank=True, verbose_name='Is Free Access')
    sub_menu_lct = models.CharField(max_length=255, null=True, blank=True, verbose_name='Sub Menu Location')
    ctg = models.CharField(max_length=255, null=True, blank=True, verbose_name='Category')
    code = models.CharField(max_length=255, null=True, blank=True, verbose_name='Code')
    dsc = models.TextField(null=True, blank=True, verbose_name='Description')

    class Meta:
        db_table = '%smenu' % TABLE_NAME_PREFIX
        verbose_name = 'Menu'


class User(IDModel):
    usr_nm = models.CharField(max_length=50, verbose_name='User Name')
    surname = models.CharField(max_length=50, blank=True, null=True, verbose_name="User Surname")
    other_nm = models.CharField(max_length=50, blank=True, null=True, verbose_name='User Other Name')
    psw = models.CharField(max_length=255, verbose_name='User Password')
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name='User Email')
    active = models.BooleanField(default=True, verbose_name='User Active')
    rmk = models.TextField(blank=True, null=True, verbose_name='User Remark')

    class Meta:
        db_table = '%susr' % TABLE_NAME_PREFIX
        verbose_name = 'User'

    def __str__(self):
        return str(self.id) + '=' + self.usr_nm

    @property
    def groups_list(self):
        """
            eg. ['group1', 'group2']
        """
        return [ug.grp.grp_nm for ug in self.usergroup_set.select_related('grp').all().order_by('id')]

    @property
    def groups_str(self):
        """
            eg. '1. group1\n2. group2'
        """
        return '\n'.join(f"{i+1}. {ug.grp.grp_nm}" for i, ug in enumerate(self.usergroup_set.select_related('grp').all().order_by('id')))


class TimestampMixin(models.Model):
    DB_COLUMN_CREATE_USER_ID = 'cre_usr_id'
    DB_COLUMN_CREATE_DATE = 'cre_dt'
    DB_COLUMN_MODIFY_USER_ID = 'mod_usr_id'
    DB_COLUMN_MODIFY_DATE = 'mod_dt'

    cre_usr = models.ForeignKey(User, models.DO_NOTHING, db_column=DB_COLUMN_CREATE_USER_ID, related_name='+', blank=True, null=True, verbose_name='Create user')
    cre_dt = models.DateTimeField(auto_now_add=True, db_column=DB_COLUMN_CREATE_DATE, blank=True, null=True, verbose_name='Create Date')
    mod_usr = models.ForeignKey(User, models.DO_NOTHING, db_column=DB_COLUMN_MODIFY_USER_ID, related_name='+', blank=True, null=True, verbose_name='Update user')
    mod_dt = models.DateTimeField(auto_now=True, db_column=DB_COLUMN_MODIFY_DATE, blank=True, null=True, verbose_name='Update Date')

    class Meta:
        abstract = True


@receiver(pre_save)
def updateModelTimestamps(sender, instance, **kwargs):
    if issubclass(sender, TimestampMixin):
        from core.core.request_middleware import getCurrentUser
        userRc = getCurrentUser()
        instance.mod_dt = timezone.now() if settings.USE_TZ else datetime.now()
        instance.mod_usr = userRc
        if instance._state.adding:
            instance.cre_dt = timezone.now() if settings.USE_TZ else datetime.now()
            instance.cre_usr = userRc


class IdDateModel(IDModel, TimestampMixin):
    class Meta:
        abstract = True


class Group(IDModel):
    grp_nm = models.CharField(max_length=50, unique=True, verbose_name='Group Name')
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        db_table = '%sgrp' % TABLE_NAME_PREFIX
        verbose_name = 'Group'


class UserGroup(IDModel):
    usr = models.ForeignKey(User, models.CASCADE, verbose_name="User")
    grp = models.ForeignKey(Group, models.CASCADE, verbose_name="Group")
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        db_table = '%susr_grp' % TABLE_NAME_PREFIX
        unique_together = (('usr', 'grp'), )
        verbose_name = 'User Group'


class GroupMenu(IDModel):
    grp = models.ForeignKey(Group, models.CASCADE, verbose_name='Group')
    menu = models.ForeignKey(Menu, models.CASCADE, verbose_name='Menu')
    acl = models.CharField(max_length=1, default='D', verbose_name='Access Rights')

    class Meta:
        db_table = '%sgrp_menu' % TABLE_NAME_PREFIX
        unique_together = (('grp', 'menu'), )
        verbose_name = 'Group Menu'


class UsrToken(IDModel):
    usr = models.ForeignKey(User, models.CASCADE, verbose_name='Iky User')
    token = models.CharField(unique=True, max_length=32, verbose_name='Token Str')

    class Meta:
        db_table = '%susr_token' % TABLE_NAME_PREFIX
        verbose_name = 'User Token Information'


class UsrSessionPrm(IDModel):
    token = models.ForeignKey(UsrToken, models.CASCADE, verbose_name='Iky User Token')
    key = models.CharField(max_length=255, verbose_name='Key')
    value = models.TextField(blank=True, null=True, verbose_name='Value')

    class Meta:
        db_table = '%susr_session_prm' % TABLE_NAME_PREFIX
        unique_together = (('token_id', 'key'), )
        verbose_name = 'User Session Information'


class AccessLog(IDModel):
    session_id = models.CharField(max_length=38, blank=True, null=True, verbose_name='Session ID')
    request_url = models.TextField(blank=True, null=True, verbose_name='Request URL')
    ip = models.CharField(max_length=40, blank=True, null=True, verbose_name='IP')
    usr_id = models.IntegerField(blank=True, null=True, verbose_name='User ID')
    menu_id = models.IntegerField(blank=True, null=True, verbose_name='Menu ID')
    page_nm = models.CharField(max_length=100, blank=True, null=True, verbose_name='Page')
    action_nm = models.CharField(max_length=100, blank=True, null=True, verbose_name='Action')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remarks')

    class Meta:
        db_table = '%saccess_log' % TABLE_NAME_PREFIX
        verbose_name = 'System Access Log'


class Setting(IDModel):
    cd = models.CharField(max_length=100, verbose_name='Code')
    key = models.CharField(max_length=100, verbose_name='Key')
    value = models.CharField(max_length=200, blank=True, null=True, verbose_name='Value')
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        db_table = '%ssetting' % TABLE_NAME_PREFIX
        unique_together = (('cd', 'key'), )
        verbose_name = 'System Setting'


class ScreenFgType(IDModel):
    type_nm = models.CharField(max_length=50, unique=True, verbose_name='Type Name')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_fg_type' % TABLE_NAME_PREFIX
        verbose_name = 'Field Group Type'


class ScreenFieldWidget(IDModel):
    widget_nm = models.CharField(max_length=50, unique=True, verbose_name='Widget Name')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_field_widget' % TABLE_NAME_PREFIX
        verbose_name = 'Field Widget'


class Screen(IDModel):
    screen_sn = models.CharField(max_length=50, verbose_name='Screen Serial Number')
    screen_title = models.CharField(max_length=255, verbose_name='Screen Title')
    screen_dsc = models.TextField(verbose_name='Screen Description')
    layout_type = models.SmallIntegerField(choices=[(1, 'grid')], default=1, verbose_name='Layout Type')
    layout_params = models.CharField(max_length=255, blank=True, null=True, verbose_name='Layout Parameters')
    app_nm = models.CharField(max_length=30, verbose_name='App Name')
    class_nm = models.CharField(max_length=255, blank=True, null=True, verbose_name='Class Name')
    api_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='API URL')
    editable = models.BooleanField(default=True, verbose_name='Editable')
    auto_refresh_interval = models.IntegerField(blank=True, null=True, verbose_name='Auto Refresh Interval')
    auto_refresh_action = models.CharField(max_length=255, blank=True, null=True, verbose_name='Auto Refresh Action')
    template_version = models.SmallIntegerField(default=0, verbose_name='Template File Version')
    rev = models.IntegerField(default=0, verbose_name='Revision')
    spreadsheet_rev = models.BigIntegerField(blank=True, null=True, verbose_name='Spreadsheet Revision')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen' % TABLE_NAME_PREFIX
        unique_together = (('screen_sn', 'rev'), )
        verbose_name = 'Page Screen'


class ScreenRecordset(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    recordset_nm = models.CharField(max_length=50, verbose_name='Recordset Name')
    seq = models.FloatField(blank=True, null=True, default=0, verbose_name='Sequence')
    sql_fields = models.CharField(blank=True, null=True, max_length=255, verbose_name='Recordset SQL - Select Fields')
    sql_models = models.CharField(max_length=255, verbose_name='Recordset SQL - From Model')
    sql_where = models.CharField(max_length=255, blank=True, null=True, verbose_name='Recordset SQL - Where')
    sql_order = models.CharField(max_length=255, blank=True, null=True, verbose_name='Recordset SQL - Order By')
    sql_limit = models.CharField(max_length=255, blank=True, null=True, verbose_name='Recordset SQL - Limit')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_recordset' % TABLE_NAME_PREFIX
        unique_together = (('screen_id', 'recordset_nm'), )
        verbose_name = 'Screen Recordset'


class ScreenFieldGroup(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    fg_nm = models.CharField(max_length=50, verbose_name='Field Group Name')
    fg_type = models.ForeignKey(ScreenFgType, models.CASCADE, verbose_name='Field Group Type')
    seq = models.FloatField(blank=True, null=True, verbose_name='Sequence')
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name='Caption')
    recordset = models.ForeignKey(ScreenRecordset, models.CASCADE, blank=True, null=True, verbose_name='Recordset')
    deletable = models.BooleanField(default=False, verbose_name='Deletable')
    editable = models.BooleanField(default=False, verbose_name='Editable')
    insertable = models.BooleanField(default=False, verbose_name='Insertable')
    highlight_row = models.BooleanField(default=False, verbose_name='Highlight Select Row')
    selection_mode = models.CharField(max_length=50, choices=[('single', 'Single'), ('multiple', 'Multiple')], blank=True, null=True, verbose_name='Selection Mode')
    cols = models.IntegerField(blank=True, null=True, verbose_name='Columns')
    # sort_new_rows = models.BooleanField(blank=True, null=True, verbose_name='Whether to Sort New Rows')
    data_page_type = models.CharField(max_length=50, choices=[('client', 'Client'), ('server', 'Server')], blank=True, null=True, verbose_name='Data Page Type')
    data_page_size = models.IntegerField(blank=True, null=True, verbose_name='Data Page Size')
    outer_layout_params = models.TextField(blank=True, null=True, verbose_name="Outer Layout Parameters")
    inner_layout_type = models.TextField(blank=True, null=True, verbose_name="Inner Layout Type")
    inner_layout_params = models.TextField(blank=True, null=True, verbose_name="Inner Layout Parameters")
    html = models.TextField(blank=True, null=True, verbose_name='Html')
    additional_props = models.TextField(blank=True, null=True, verbose_name='Additional Properties')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_field_group' % TABLE_NAME_PREFIX
        unique_together = (('screen', 'fg_nm'), )
        verbose_name = 'Screen Field Groups'


class ScreenField(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    field_group = models.ForeignKey(ScreenFieldGroup, models.CASCADE, blank=True, null=True, verbose_name='Field Group')
    field_nm = models.CharField(blank=True, null=True, max_length=50, verbose_name='Field Name')
    seq = models.FloatField(blank=True, null=True, verbose_name='Sequence')
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name='Caption')
    tooltip = models.TextField(blank=True, null=True, verbose_name='Tooltip')
    visible = models.BooleanField(default=True, verbose_name='Visible')
    editable = models.BooleanField(default=True, verbose_name='Editable')
    db_unique = models.BooleanField(default=None, blank=True, null=True, verbose_name='Unique')
    db_required = models.BooleanField(default=None, blank=True, null=True, verbose_name='Required')
    widget = models.ForeignKey(ScreenFieldWidget, models.CASCADE, blank=True, null=True, verbose_name='Widget')
    widget_parameters = models.TextField(blank=True, null=True, verbose_name='Widget Parameters')
    db_field = models.CharField(max_length=50, blank=True, null=True, verbose_name='Database Field')
    event_handler = models.CharField(max_length=255, blank=True, null=True, verbose_name='Event Handler')
    styles = models.CharField(max_length=255, blank=True, null=True, verbose_name='Styles')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_field' % TABLE_NAME_PREFIX
        verbose_name = 'Screen Field Groups Fields'


class ScreenFgLink(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    field_group = models.ForeignKey(ScreenFieldGroup, models.CASCADE, blank=True, null=True, verbose_name='Field Group', related_name='field_group')
    local_key = models.CharField(max_length=50, blank=True, null=True, verbose_name='Local Key')
    parent_field_group = models.ForeignKey(ScreenFieldGroup, models.CASCADE, blank=True, null=True, verbose_name='Parent Field Group', related_name='parent_field_group')
    parent_key = models.CharField(max_length=50, blank=True, null=True, verbose_name='Parent Key')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_fg_link' % TABLE_NAME_PREFIX
        unique_together = (('screen', 'field_group', 'parent_field_group'), )
        verbose_name = 'Screen Field Group Links'


class ScreenFgHeaderFooter(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    field_group = models.ForeignKey(ScreenFieldGroup, models.CASCADE, blank=True, null=True, verbose_name='Field Group')
    field = models.ForeignKey(ScreenField, models.CASCADE, blank=True, null=True, verbose_name='Field')
    header_level1 = models.CharField(max_length=255, blank=True, null=True, verbose_name='Header Level 1')
    header_level2 = models.CharField(max_length=255, blank=True, null=True, verbose_name='Header Level 2')
    header_level3 = models.CharField(max_length=255, blank=True, null=True, verbose_name='Header Level 3')
    footer = models.TextField(blank=True, null=True, verbose_name='Footer')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_fg_header_footer' % TABLE_NAME_PREFIX
        unique_together = (('screen', 'field_group', 'field'), )
        verbose_name = 'Screen Table Header and Footer'


class ScreenFile(IDModel):
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, verbose_name="Screen")
    file_nm = models.CharField(max_length=255, verbose_name='File Name')
    file_size = models.IntegerField(verbose_name='File Size')
    file_path = models.CharField(max_length=255, verbose_name='File Path')
    file_dt = models.DateTimeField(verbose_name='File Last Modify Date')
    file_md5 = models.CharField(default='', blank=True, null=True, max_length=255, verbose_name='File MD5 String')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        db_table = '%sscreen_file' % TABLE_NAME_PREFIX
        verbose_name = 'Screen File'


class ScreenDfn(IDModel):
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, verbose_name="Screen")
    sub_screen_nm = models.CharField(max_length=50, verbose_name="Sub Screen Name")
    field_group_nms = models.TextField(blank=True, null=True, verbose_name="Field Groups Name")
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name="Remark")

    class Meta:
        db_table = '%sscreen_dfn' % TABLE_NAME_PREFIX
        unique_together = (('screen', 'sub_screen_nm'), )
        verbose_name = "Screen Definition"


class IkInbox(IDModel):
    STATUS_NEW = 'new'
    STATUS_READ = 'read'
    STATUS_COMPLETED = 'completed'
    STATUS_DELETED = 'deleted'
    STATUS_CHOOSES = ((STATUS_NEW, STATUS_NEW), (STATUS_READ, STATUS_READ), (STATUS_COMPLETED, STATUS_COMPLETED), (STATUS_DELETED, STATUS_DELETED))

    owner = models.ForeignKey(User, models.CASCADE, related_name="owner_user", verbose_name='Owner ID')
    sender = models.ForeignKey(User, models.DO_NOTHING, related_name="sender_user", verbose_name='Sender ID')
    send_dt = models.DateTimeField(verbose_name='Send Time')
    module = models.CharField(max_length=255, verbose_name='Send From')
    sts = models.CharField(max_length=10, choices=STATUS_CHOOSES, default=STATUS_NEW, verbose_name='Status')
    summary = models.TextField(verbose_name='Summary')
    usr_rmk = models.TextField(blank=True, null=True, verbose_name='User Remark')

    class Meta:
        db_table = '%sinbox' % TABLE_NAME_PREFIX
        verbose_name = 'Inbox Table'


class IkInboxPrm(IDModel):
    inbox = models.ForeignKey(IkInbox, models.CASCADE, verbose_name='Inbox key')
    k = models.CharField(max_length=50, blank=True, null=True, verbose_name='Parameter Name')
    v = models.CharField(max_length=255, blank=True, null=True, verbose_name='Parameter Value')

    class Meta:
        db_table = '%sinbox_prm' % TABLE_NAME_PREFIX
        unique_together = (('inbox', 'k'), )
        verbose_name = 'Inbox Parameters'


class Currency(IDModel):
    seq = models.FloatField(verbose_name='Sequence')
    code = models.CharField(max_length=3, unique=True, verbose_name='Code')
    name = models.CharField(max_length=100, unique=True, verbose_name='Name')
    dsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Description')

    class Meta:
        db_table = '%scurrency' % TABLE_NAME_PREFIX


class Office(IDModel):
    name = models.CharField(max_length=100, unique=True, verbose_name='Office Name')
    code = models.CharField(max_length=3, unique=True, verbose_name='Office Code')
    addr = models.CharField(max_length=255, verbose_name='Address')
    city = models.CharField(max_length=100)
    st = models.CharField(max_length=100, blank=True, null=True, verbose_name='State')
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone_num = models.CharField(max_length=20, blank=True, null=True, verbose_name='Phone Number')
    email = models.EmailField(blank=True, null=True)
    ccy = models.ForeignKey(Currency, models.DO_NOTHING, verbose_name="Currency")
    dsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Description')

    class Meta:
        db_table = '%soffice' % TABLE_NAME_PREFIX

    def __str__(self):
        return self.code

    @property
    def fullname(self):
        return f"{self.code} - {self.name}"


class UserOffice(IDModel):
    usr = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    office = models.ForeignKey(Office, on_delete=models.CASCADE, verbose_name="Office")
    is_default = models.BooleanField(verbose_name="Default")
    seq = models.FloatField(verbose_name='Sequence')
    dsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Description')

    class Meta:
        db_table = '%susr_office' % TABLE_NAME_PREFIX
        unique_together = (('usr', 'office'), )


class Company(IdDateModel):
    sn = models.CharField(max_length=10, unique=True, verbose_name='SN')
    full_nm = models.CharField(max_length=255, unique=True, verbose_name='Company Full Name')
    short_nm = models.CharField(max_length=50, unique=True, verbose_name='Company Short Name')
    location = models.ForeignKey(Office, db_column='location', to_field='code', on_delete=models.DO_NOTHING, verbose_name='Location (Office)')
    dsc = models.TextField(null=True, blank=True, verbose_name='Description')
    ctg = models.CharField(max_length=20, verbose_name='Category')

    class Meta:
        db_table = '%scompany' % TABLE_NAME_PREFIX
        verbose_name = 'Company'


class Team(IdDateModel):
    nm = models.CharField(max_length=255, unique=True, verbose_name='Team Name')
    seq = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=4, verbose_name='Sequence')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, verbose_name='Company')
    enable = models.BooleanField(default=True, verbose_name='Enable')
    dsc = models.CharField(max_length=255, null=True, blank=True, verbose_name='Description')
    rmk = models.CharField(max_length=255, null=True, blank=True, verbose_name='Remarks')

    class Meta:
        db_table = '%steam' % TABLE_NAME_PREFIX
        verbose_name = 'Team'


class TeamMember(IdDateModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Team ID")
    usr = models.ForeignKey(User, models.CASCADE, verbose_name="User")
    seq = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Seq")
    role = models.SmallIntegerField(verbose_name="Role")
    is_default_team = models.BooleanField(default=False, verbose_name="Is Default Team")
    is_report_ts = models.BooleanField(default=True, verbose_name="Is Report Timesheet")
    rmk = models.CharField(max_length=255, null=True, blank=True, verbose_name="Remark")

    class Meta:
        db_table = '%steam_member' % TABLE_NAME_PREFIX
        unique_together = (('team', 'usr'),)
        verbose_name = 'Team Member'


class Mail(IDModel):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETE = 'complete'
    STATUS_ERROR = 'error'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOOSES = ((STATUS_PENDING, STATUS_PENDING), (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
                      (STATUS_COMPLETE, STATUS_COMPLETE), (STATUS_ERROR, STATUS_ERROR), (STATUS_CANCELLED, STATUS_CANCELLED))

    MAIL_TYPE_TEXT = 'text'
    MAIL_TYPE_HTML = 'html'
    MAIL_TYPE_CHOOSES = ((MAIL_TYPE_TEXT, MAIL_TYPE_TEXT), (MAIL_TYPE_HTML, MAIL_TYPE_HTML))

    sender = models.CharField(max_length=255, verbose_name='Mail Sender')
    request_ts = models.DateTimeField(auto_now_add=True, verbose_name='Request Date')
    subject = models.CharField(max_length=255, verbose_name='Mail Subject')
    content = models.TextField(verbose_name='Mail Content')
    type = models.CharField(max_length=4, choices=MAIL_TYPE_CHOOSES, default=MAIL_TYPE_TEXT, verbose_name='Mail Type')
    queue = models.BooleanField(default=True, verbose_name="Is queue mail")
    dsc = models.TextField(blank=True, null=True, verbose_name='Description')
    sts = models.CharField(max_length=20, choices=STATUS_CHOOSES, default=STATUS_PENDING, verbose_name='Status')
    send_ts = models.DateTimeField(blank=True, null=True, verbose_name='Send Date')
    duration = models.BigIntegerField(blank=True, null=True, verbose_name='Send Duration')
    error = models.TextField(blank=True, null=True, verbose_name='Error')

    class Meta:
        managed = True
        db_table = '%smail' % TABLE_NAME_PREFIX
        verbose_name = 'Mail'


class MailAddr(IDModel):
    TYPE_TO = 'to'
    TYPE_CC = 'cc'
    TYPE_BCC = 'bcc'
    TYPE_CHOOSES = ((TYPE_TO, TYPE_TO), (TYPE_CC, TYPE_CC), (TYPE_BCC, TYPE_BCC))

    mail = models.ForeignKey(Mail, on_delete=models.CASCADE, verbose_name="Mail")
    type = models.CharField(max_length=10, choices=TYPE_CHOOSES, verbose_name='Address Type')
    name = models.CharField(max_length=100, verbose_name='Receiver Name')
    address = models.CharField(max_length=100, verbose_name='Receiver Address')
    seq = models.IntegerField(blank=True, null=True, verbose_name='Sequency')

    class Meta:
        managed = True
        db_table = '%smail_addr' % TABLE_NAME_PREFIX
        unique_together = (('mail', 'type', 'name'), )
        verbose_name = 'Mail Address'


class MailAttch(IDModel):
    mail = models.ForeignKey(Mail, on_delete=models.CASCADE, verbose_name="Mail")
    file = models.TextField(verbose_name='File')
    size = models.IntegerField(verbose_name='File Size')
    seq = models.IntegerField(blank=True, null=True, verbose_name='Sequency')

    class Meta:
        managed = True
        db_table = '%smail_attch' % TABLE_NAME_PREFIX
        verbose_name = 'Mail Attachment'


class PermissionControl(IDModel):
    name = models.CharField(max_length=100, unique=True, verbose_name='Name')
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        managed = True
        db_table = '%spermission_control' % TABLE_NAME_PREFIX
        verbose_name = "Permission Control"

    def __str__(self):
        return self.name

    @property
    def user_list(self):
        # users
        direct_users = [pcu.user for pcu in self.permission_control_users.all() if pcu.user]
        # group users
        group_users = []
        for pcu in self.permission_control_users.all():
            if pcu.group:
                group_users.extend(
                    [ug.usr for ug in pcu.group.usergroup_set.select_related('usr').all()]
                )
        # distinct
        all_users = {user.id: user for user in (direct_users + group_users) if user}.values()
        return ", ".join([user.usr_nm for user in all_users])


class PermissionControlUser(IDModel):
    permission_control = models.ForeignKey(PermissionControl, on_delete=models.CASCADE, related_name='permission_control_users')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='user_permission_controls')
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE, related_name='group_permission_controls')

    class Meta:
        managed = True
        db_table = '%spermission_control_user' % TABLE_NAME_PREFIX
        verbose_name = "Permission Control User"
        constraints = [
            models.UniqueConstraint(
                fields=['permission_control', 'user'],
                name='unique_permission_control_user'
            ),
            models.UniqueConstraint(
                fields=['permission_control', 'group'],
                name='unique_permission_control_group'
            ),
            models.CheckConstraint(
                check=~(models.Q(user__isnull=True) & models.Q(group__isnull=True)),
                name='user_or_group_not_null'
            )
        ]


class CronJob(IdDateModel):
    second = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - second (0-59)')
    minute = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - minute (0-59)')
    hour = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - hour (0-23)')
    day = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - day of month (1-31)')
    week = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - ISO week (1-53)')
    day_of_week = models.CharField(max_length=255, blank=True, null=True,
                                   verbose_name='(int|str) - number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)')
    month = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - month (1-12)')
    year = models.CharField(max_length=255, blank=True, null=True, verbose_name='(int|str) - 4-digit year')
    start_date = models.CharField(max_length=255, blank=True, null=True,
                                  verbose_name='(datetime|str) - earliest possible date/time to trigger on (inclusive)')
    end_date = models.CharField(max_length=255, blank=True, null=True,
                                verbose_name='(datetime|str) - latest possible date/time to trigger on (inclusive)')
    jitter = models.IntegerField(blank=True, null=True, verbose_name='(int|None) - delay the job execution by jitter seconds at most')
    task = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tasks')
    args = models.TextField(blank=True, null=True, verbose_name='Arguments')
    enable = models.BooleanField(blank=True, null=True, verbose_name='Enable')
    dsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Description')

    class Meta:
        db_table = '%scron_job' % TABLE_NAME_PREFIX
        verbose_name = "Cron Job"


def coreHistoryFilter(sender, instance, **kwargs) -> bool:
    return not isinstance(instance, AccessLog) and not isinstance(instance, UsrToken)


addModelHistoryFilter(coreHistoryFilter)
