--- User
INSERT INTO ik_usr(version_no, usr_nm, surname, other_nm, psw, email, active, rmk)
VALUES(0, 'admin', null, null, 'pbkdf2_sha256$320000$iah5WdU2QY4ZYeDCd8SkQk$DT+7gFkr+Cg7uORzT/myUr4JSRgpDoSd4d/a6Q/Xkhw=', null, true, null);


--- Menu
INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc)
VALUES 
(0, 'Menu', 'Menu', 'Menu', null, true, -1, true, null, null),
(0, 'Home', 'Home', 'Home', null, true, 0, true, null, null);

INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, sub_menu_lct, dsc)
VALUES (0, 'system', 'System', null, null, true, 20, null, null);

INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc) VALUES 
(0, 'UsrMnt', 'User Management', 'UsrMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 10, null, null, null),
(0, 'UsrGrpMnt', 'User Group Management', 'UsrGrpMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 20, null, null, null),
(0, 'MenuMnt', 'Menu Management', 'MenuMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 30, null, null, null),
(0, 'AppMnt', 'App Management', 'AppMnt', (select id from ik_menu where menu_nm = 'system'), true, 40, null, null, null),
(0, 'TypeWidgetMnt', 'Field Group Type and Field Widget Management', 'TypeWidgetMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 50, null, null, null),
(0, 'ScreenDfn', 'Screen Definition', 'ScreenDfn', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 60, null, null, null),
(0, 'Office', 'Office', 'Office', (select id from ik_menu where menu_nm = 'system'), true, 70, null, null, null),
(0, 'Currency', 'Currency', 'Currency', (select id from ik_menu where menu_nm = 'system'), true, 80, null, null, null),
(0, 'Inbox', 'Inbox', 'Inbox', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 90, true, null, null),
(0, 'Mail001', 'Email Queue Management', 'Mail001', (select id from ik_menu where menu_nm = 'system'), true, 100, null, null, null),
(0, 'Mail002', 'Compose Email', 'Mail002', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 110, null, null, null),
(0, 'PermissionControl', 'Permission Control', 'PermissionControl', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 120, null, null, null);


--- Group Management Menus
INSERT INTO ik_grp(version_no, grp_nm, rmk) VALUES(0, 'Administrator', null);
INSERT INTO ik_usr_grp(version_no, grp_id, usr_id) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_usr WHERE usr_nm='admin'));

INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='UsrMnt'), 'W');
INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='UsrGrpMnt'), 'W');
INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='ScreenDfn'), 'W');


--- Screen Definition
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUES(0, 'tree', 'A tree field.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUES(0, 'table', 'A controlable table.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'fields', 'A set for widgets.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'iconBar', 'Icon bars');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'resultTable', 'A read only table.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'search', 'A set of widgets for search data from server side.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'html', 'A html field.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'iframe', 'A html field but only IT use.');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUEs(0, 'viewer', 'Display image or PDF');
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUES(0, 'sitePlan', 'Display Site Plan And Soil Chart.');

INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'Label', 'If this field is empty, admin will use Label instead.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'TextBox', 'Text box');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'TextArea', 'Line feedable text box');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'DateBox', 'Date box');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'ComboBox', 'Multiple choice one');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'ListBox', 'Multiple choice multiple');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'CheckBox', 'Choose one of two or three, Available options: True, False, (None)');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'Button', 'Button');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'IconAndText', 'The icons in toolbar.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'File', 'Download file.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'Plugin', 'Currently only used for the last column of the table, open the details table');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'Html', 'HTML');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'AdvancedComboBox', 'Combobox that allow filtering and multi-selection.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'Password', 'Entry password text box.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'AdvancedSelection', 'Select the content displayed in the Label in the dialog after clicking the button.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'InlineRadioGroup', 'Radio group that supports multi-selection and displays all options inline.');
INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES(0, 'Link', 'Display a link. Click to navigate to a specific page.');

--- Ik Setting
INSERT INTO ik_setting(version_no, cd, key, value, rmk) VALUES(0, 'WCI2', 'EMAIL_ATTACH_TOTAL_SIZE_LIMIT', 5, 'MB');