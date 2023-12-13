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
(0, 'UsrGrpMnt', 'User Group Management', 'UsrGrpMnt', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 20, null, null, null),
(0, 'ScreenDfn', 'Screen Definition', 'ScreenDfn', (SELECT id FROM ik_menu WHERE menu_nm = 'system'), true, 30, null, null, null);

INSERT INTO ik_grp(version_no, grp_nm, rmk) VALUES(0, 'Administrator', null);
INSERT INTO ik_usr_grp(version_no, grp_id, usr_id) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_usr WHERE usr_nm='admin'));

INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='UsrMnt'), 'W');
INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='UsrGrpMnt'), 'W');
INSERT INTO ik_grp_menu(version_no, grp_id, menu_id, acl) VALUES(0, (SELECT id FROM ik_grp WHERE grp_nm='Administrator'), (SELECT id FROM ik_menu WHERE menu_nm='ScreenDfn'), 'W');