--- User
insert into ik_usr(version_no, usr_nm, surname, other_nm, psw, email, enable, rmk)
values(0, 'admin', null, null, 'c4ca4238a0b923820dcc509a6f75849b', null, 'Y', null);


--- Menu
INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc)
VALUES 
(0, 'Menu', 'Menu', 'Menu', null, true, -1, true, null, null),
(0, 'Home', 'Home', 'Home', null, true, 0, true, null, null);


--- Group Management Menus
INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc)
VALUES (0, 'system', 'System', null, null, true, 20, null, null, null);

INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc) VALUES 
(0, 'UsrMnt', 'User Management', 'UsrMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 10, null, null, null),
(0, 'UsrGrpMnt', 'User Group Management', 'UsrGrpMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 20, null, null, null);

INSERT INTO ik_grp(version_no, grp_nm, rmk) VALUES(0, 'Administrator', null);
INSERT INTO ik_usr_grp(version_no, grp_id, usr_id) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_usr WHERE usr_nm='admin'));

INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='UsrMnt'), 'W');
INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='UsrGrpMnt'), 'W');


--- Screen Definition
INSERT INTO ik_screen_fg_type (version_no, type_nm, rmk) VALUES
(0, 'table', 'A controlable table.'),
(0, 'fields', 'A set for widgets.'),
(0, 'iconBar', 'Icon bars'),
(0, 'resultTable', 'A read only table.'),
(0, 'search', 'A set of widgets for search data from server side.'),
(0, 'html', 'A html field.'),
(0, 'iframe', 'A html field but only IT use.'),
(0, 'viewer', 'Used for Pile Design.'),
(0, 'PD001N', 'Used for Pile Design.'),
(0, 'PD001NCounter', 'Used for Pile Design.');

INSERT INTO ik_screen_field_widget (version_no, widget_nm, rmk) VALUES
(0, 'Label', 'If this field is empty, admin will use Label instead.'),
(0, 'TextBox', 'Text box'),
(0, 'TextArea', 'Line feedable text box'),
(0, 'DateBox', 'Date box'),
(0, 'ComboBox', 'Multiple choice one'),
(0, 'ListBox', 'Multiple choice multiple'),
(0, 'CheckBox', 'Choose one of two or three, Available options: True, False, (None)'),
(0, 'Button', 'Button'),
(0, 'IconAndText', 'The icons in toolbar.'),
(0, 'File', 'Download file.'),
(0, 'Plugin', 'Currently only used for the last column of the table, open the details table'),
(0, 'Html', 'HTML'),
(0, 'viewer', 'Used for Pile Design.'),
(0, 'AdvancedComboBox', 'Combobox that allow filtering and multi-selection.'),
(0, 'Password', 'Entry password text box.'),
(0, 'AdvancedSelection', 'Select the content displayed in the Label in the dialog after clicking the button.');
