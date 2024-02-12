from django.db import models
from core.db.model import IDModel


class Menu(IDModel):
    menu_nm = models.CharField(unique=True, max_length=100, verbose_name='Menu Name')
    menu_caption = models.CharField(max_length=100, verbose_name='Menu Caption')
    screen_nm = models.CharField(max_length=200, null=True, blank=True, verbose_name='Screen Name')
    parent_menu_id = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='Parent Menu ID')
    enable = models.BooleanField(null=True, blank=True, verbose_name="Menu Enable")
    order_no = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='Order No')
    is_free_access = models.BooleanField(null=True, blank=True, verbose_name='Is Free Access')
    sub_menu_lct = models.CharField(max_length=255, null=True, blank=True, verbose_name='Sub Menu Location')
    dsc = models.TextField(null=True, blank=True, verbose_name='Description')

    class Meta:
        managed = True
        db_table = 'ik_menu'
        verbose_name = 'Menu'


class User(IDModel):
    usr_nm = models.CharField(max_length=50, verbose_name='User Name')
    surname = models.CharField(max_length=50, blank=True, null=True, verbose_name="User Surname")
    other_nm = models.CharField(max_length=50, blank=True, null=True, verbose_name='User Other Name')
    psw = models.CharField(max_length=255, verbose_name='User Password')
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name='User Email')
    enable = models.CharField(max_length=1, verbose_name='User Enable')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='User Remark')

    class Meta:
        managed = True
        db_table = 'ik_usr'
        verbose_name = 'User'

    def __str__(self):
        return str(self.id) + '=' + self.usr_nm


class Group(IDModel):
    grp_nm = models.CharField(max_length=50, unique=True, verbose_name='Group Name')
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        db_table = 'ik_grp'
        verbose_name = 'Group'


class UserGroup(IDModel):
    usr = models.ForeignKey(User, models.CASCADE, verbose_name="User")
    grp = models.ForeignKey(Group, models.CASCADE, verbose_name="Group")
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        db_table = 'ik_usr_grp'
        unique_together = (('usr', 'grp'), )
        verbose_name = 'User Group'


class GroupMenu(IDModel):
    grp = models.ForeignKey(Group, models.CASCADE, verbose_name='Group')
    menu = models.ForeignKey(Menu, models.CASCADE, verbose_name='Menu')
    acl = models.CharField(max_length=1, default='D', verbose_name='Access Rights')

    class Meta:
        db_table = 'ik_grp_menu'
        unique_together = (('grp', 'menu'), )
        verbose_name = 'Group Menu'


class UsrToken(IDModel):
    usr = models.ForeignKey(User, models.CASCADE, verbose_name='Iky User')
    token = models.CharField(unique=True, max_length=32, verbose_name='Token Str')

    class Meta:
        managed = True
        db_table = 'ik_usr_token'
        verbose_name = 'User Token Information'


class UsrSessionPrm(IDModel):
    token = models.ForeignKey(UsrToken, models.CASCADE, verbose_name='Iky User Token')
    key = models.CharField(max_length=255, verbose_name='Key')
    value = models.TextField(blank=True, null=True, verbose_name='Value')

    class Meta:
        managed = True
        db_table = 'ik_usr_session_prm'
        unique_together = (('token_id', 'key'), )
        verbose_name = 'User Session Information'


class AccessLog(IDModel):
    session_id = models.CharField(max_length=38, blank=True, null=True, verbose_name='Session ID')
    request_url = models.TextField(blank=True, null=True, verbose_name='Request URL')
    ip = models.CharField(max_length=40, blank=True, null=True, verbose_name='IP')
    usr_id = models.BigIntegerField(blank=True, null=True, verbose_name='User ID')
    menu_id = models.BigIntegerField(blank=True, null=True, verbose_name='Menu ID')
    page_nm = models.CharField(max_length=100, blank=True, null=True, verbose_name='Page')
    action_nm = models.CharField(max_length=100, blank=True, null=True, verbose_name='Action')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remarks')

    class Meta:
        managed = True
        db_table = 'ik_access_log'
        verbose_name = 'System Access Log'


class Setting(IDModel):
    cd = models.CharField(max_length=100, verbose_name='Code')
    key = models.CharField(max_length=100, verbose_name='Key')
    value = models.CharField(max_length=200, blank=True, null=True, verbose_name='Value')
    rmk = models.TextField(blank=True, null=True, verbose_name='Remarks')

    class Meta:
        managed = True
        db_table = 'ik_setting'
        unique_together = (('cd', 'key'), )
        verbose_name = 'System Setting'


class ScreenFgType(IDModel):
    type_nm = models.CharField(max_length=50, unique=True, verbose_name='Type Name')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_fg_type'
        verbose_name = 'Field Group Type'


class ScreenFieldWidget(IDModel):
    widget_nm = models.CharField(max_length=50, unique=True, verbose_name='Widget Name')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_field_widget'
        verbose_name = 'Field Widget'


class Screen(IDModel):
    screen_sn = models.CharField(max_length=50, verbose_name='Screen Serial Number')
    screen_title = models.CharField(max_length=255, verbose_name='Screen Title')
    screen_dsc = models.TextField(verbose_name='Screen Description')
    layout_type = models.SmallIntegerField(choices=[(1, 'grid')], default=1, verbose_name='Layout Type')
    layout_params = models.CharField(max_length=255, blank=True, null=True, verbose_name='Layout Parameters')
    class_nm = models.CharField(max_length=255, verbose_name='Class Name')
    api_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='API URL')
    editable = models.BooleanField(default=True, verbose_name='Editable')
    auto_refresh_interval = models.IntegerField(blank=True, null=True, verbose_name='Auto Refresh Interval')
    auto_refresh_action = models.CharField(max_length=255, blank=True, null=True, verbose_name='Auto Refresh Action')
    api_version = models.SmallIntegerField(default=0, verbose_name='Api Version')
    rev = models.IntegerField(default=0, verbose_name='Revision')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen'
        unique_together = (('screen_sn', 'rev'), )
        verbose_name = 'Page Screen'


class ScreenRecordset(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    recordset_nm = models.CharField(max_length=50, verbose_name='Recordset Name')
    sql_fields = models.CharField(blank=True, null=True, max_length=255, verbose_name='Recordset SQL - Select Fields')
    sql_models = models.CharField(max_length=255, verbose_name='Recordset SQL - From Model')
    sql_where = models.CharField(max_length=255, blank=True, null=True, verbose_name='Recordset SQL - Where')
    sql_order = models.CharField(max_length=255, blank=True, null=True, verbose_name='Recordset SQL - Order By')
    sql_limit = models.CharField(max_length=255, blank=True, null=True, verbose_name='Recordset SQL - Limit')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_recordset'
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
    selection_mode = models.CharField(max_length=50, choices=[('single', 'Single'),
                                      ('multiple', 'Multiple')], blank=True, null=True, verbose_name='Selection Mode')
    cols = models.IntegerField(blank=True, null=True, verbose_name='Columns')
    # sort_new_rows = models.BooleanField(blank=True, null=True, verbose_name='Whether to Sort New Rows')
    data_page_type = models.CharField(max_length=50, choices=[('client', 'Client'),
                                      ('server', 'Server')], blank=True, null=True, verbose_name='Data Page Type')
    data_page_size = models.IntegerField(blank=True, null=True, verbose_name='Data Page Size')
    outer_layout_params = models.TextField(blank=True, null=True, verbose_name="Outer Layout Parameters")
    inner_layout_type = models.TextField(blank=True, null=True, verbose_name="Inner Layout Type")
    inner_layout_params = models.TextField(blank=True, null=True, verbose_name="Inner Layout Parameters")
    html = models.TextField(blank=True, null=True, verbose_name='Html')
    additional_props = models.TextField(blank=True, null=True, verbose_name='Additional Properties')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_field_group'
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
    widget = models.ForeignKey(ScreenFieldWidget, models.CASCADE, blank=True, null=True, verbose_name='Widget')
    widget_parameters = models.TextField(blank=True, null=True, verbose_name='Widget Parameters')
    db_field = models.CharField(max_length=50, blank=True, null=True, verbose_name='Database Field')
    md_format = models.CharField(max_length=255, blank=True, null=True, verbose_name='Format')
    md_validation = models.TextField(blank=True, null=True, verbose_name='Validation')
    event_handler = models.CharField(max_length=255, blank=True, null=True, verbose_name='Event Handler')
    styles = models.CharField(max_length=255, blank=True, null=True, verbose_name='Styles')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_field'
        unique_together = (('screen', 'field_group', 'field_nm'), )
        verbose_name = 'Screen Field Groups Fields'


class ScreenFgLink(IDModel):
    screen = models.ForeignKey(Screen, models.CASCADE, verbose_name="Screen")
    field_group = models.ForeignKey(ScreenFieldGroup, models.CASCADE, blank=True, null=True,
                                    verbose_name='Field Group', related_name='field_group')
    local_key = models.CharField(max_length=50, blank=True, null=True, verbose_name='Local Key')
    parent_field_group = models.ForeignKey(ScreenFieldGroup, models.CASCADE, blank=True, null=True,
                                           verbose_name='Parent Field Group', related_name='parent_field_group')
    parent_key = models.CharField(max_length=50, blank=True, null=True, verbose_name='Parent Key')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_fg_link'
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
        managed = True
        db_table = 'ik_screen_fg_header_footer'
        unique_together = (('screen', 'field_group', 'field'), )
        verbose_name = 'Screen Table Header and Footer'


class ScreenFile(IDModel):
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, verbose_name="Screen")
    file_nm = models.CharField(max_length=255, verbose_name='File Name')
    file_size = models.IntegerField(verbose_name='File Size')
    file_path = models.CharField(max_length=255, verbose_name='File Path')
    file_dt = models.DateTimeField(verbose_name='File Last Modify Date')
    file_md5 = models.CharField(default='', max_length=255, verbose_name='File MD5 String')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Remark')

    class Meta:
        managed = True
        db_table = 'ik_screen_file'
        verbose_name = 'Screen File'


class ScreenDfn(IDModel):
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, verbose_name="Screen")
    sub_screen_nm = models.CharField(max_length=50, verbose_name="Sub Screen Name")
    field_group_nms = models.TextField(blank=True, null=True, verbose_name="Field Groups Name")
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name="Remark")

    class Meta:
        managed = True
        db_table = 'ik_screen_dfn'
        unique_together = (('screen', 'sub_screen_nm'), )
        verbose_name = "Screen Definition"
