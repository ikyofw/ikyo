-- menus
insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES', 'Expense System', null, null, true, null, NULL);

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ESSetting', 'Settings', null, (select id from ik_menu where menu_nm='ES'), true, 100, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001A', 'ES001A - Payment Method', 'ES001A', (select id from ik_menu where menu_nm='ESSetting'), true, 110, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001B', 'ES001B - Payee', 'ES001B', (select id from ik_menu where menu_nm='ESSetting'), true, 120, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001C', 'ES001C - Finance', 'ES001C', (select id from ik_menu where menu_nm='ESSetting'), true, 130, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001D', 'ES001D - Approver', 'ES001D', (select id from ik_menu where menu_nm='ESSetting'), true, 140, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001E', 'ES001E - Petty Expense', 'ES001E', (select id from ik_menu where menu_nm='ESSetting'), true, 150, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001F', 'ES001F - User Roles', 'ES001F', (select id from ik_menu where menu_nm='ESSetting'), true, 160, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES001G', 'ES001G - Settings', 'ES001G', (select id from ik_menu where menu_nm='ESSetting'), true, 170, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES002', 'Select Office', 'ES002', (select id from ik_menu where menu_nm='ES'), true, 200, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES003', 'ES003 - Expense Category', 'ES003', (select id from ik_menu where menu_nm='ES'), true, 300, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES004', 'ES004 - New Expense', 'ES004', (select id from ik_menu where menu_nm='ES'), true, 400, 'top');
 
insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES005', 'ES005 - Expense Enquiry', 'ES005', (select id from ik_menu where menu_nm='ES'), true, 500, 'top');

insert into ik_menu(version_no ,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES006', 'ES006 - Cash Advancement', 'ES006', (select id from ik_menu where menu_nm='ES'), true, 600, 'top');
	
insert into ik_menu(version_no,menu_nm,menu_caption,screen_nm,parent_menu_id,"enable",order_no,sub_menu_lct)
	values(0, 'ES101', 'ES101 - Expense Report', 'ES101', (select id from ik_menu where menu_nm='ES'), true, 700, 'top');

-- ES001A - Payment Method
INSERT INTO es_paymentmethod(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,tp,dsc) VALUES
    (1, now(), 1, now(), 0, 'bank transfer', NULL), 
	(1, now(), 1, now(),  0, 'e-cheque', NULL), 
	(1, now(), 1, now(),  0, 'petty cash', NULL), 
	(1, now(), 1, now(),  0, 'prior balance', NULL);


-- catregory
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'advertising',null);
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'bank charges',null);
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'book','newspaper, books and magazines');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'BR','business registration');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'certification','certification and declaration (e.g. ISO)');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'cleaning','office cleaning');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'courier','including postage');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'deposit','various deposit');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'director','director emoluments');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'electricity',null);
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'entertainment','client entertainment - restaurant');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'equipment','non computer equipment, electric appliance');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'fine','fine and penalty');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'furniture',null);
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'hardware','computer hardware excluding hardware maintenance');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'hotel','any local accomodation for visitors');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'insurance','medical insurance, office insurance etc.');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'internet','boardband, hosting, domain name');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'maintenance','repair, renovation, reinstatement, hw and sw maintenance, other annual maintenance etc.');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'material','project expenses - hydraulic oil, C beam, bolts and nuts, tools etc.');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'medical',null);
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'mgt fees','management fees');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'mpf',null);
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'phone','all telecommunication - mobile phone, land line, zoom etc.');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'printing','paper, toner, ink, printer rental etc.');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'professional','professional fees excluding those in services - consultancy');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'rate','government rent and rate');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'refund','money refund to the company, entered as positive value to balance out petty cash');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'rent','office rent');
INSERT INTO es_expensecategory(cre_usr_id,cre_dt,mod_usr_id,mod_dt,version_no,cat,dsc) values(1,now(),1,now(),0,'salary',null);

-- system settings
INSERT INTO ik_setting(version_no,cd,key,value,rmk)
    VALUES(0,'ES',
	'Allow accounting to reject expenses and cash advances',
	'true', 'Options: true, false. Default is true.');

INSERT INTO ik_setting(version_no,cd,key,value,rmk)
    VALUES(0,'ES',
	'Enable IKYO2 inbox notification',
	'true', 'Options: true, false. Default is true.');
	
-- VIEWS
-- create view es_v_user_expense
CREATE OR REPLACE VIEW es_v_user_expense AS
 SELECT DISTINCT * FROM (
	-- 1. Claimer can access their own expense (admin)
	SELECT
	    e.claimer_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	
	-- 2. Accounting permission (admin)
	UNION
	SELECT
	    a.usr_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_accounting a ON a.office_id = e.office_id
	
	-- 3. Petty cash admin access (admin) for petty expenses
	UNION
	SELECT
	    p.admin_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_pettycashexpenseadmin p ON e.office_id = p.office_id
	WHERE e.is_petty_expense IS true AND p.enable = true
	
	UNION
	
	-- 4. Approver / Assistant / Approver2 roles (admin)
	-- 4.1 Approver
	SELECT
	    a.approver_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	WHERE a.approver_id IS NOT NULL
	
	-- 4.2 Approver Group
	UNION
	SELECT
	    ug.usr_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	JOIN ik_usr_grp ug ON ug.grp_id = a.approver_grp_id
	WHERE a.approver_grp_id IS NOT NULL
	
	UNION
	
	-- 4.3 Approver Assistant
	SELECT
	    a.approver_assistant_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	WHERE a.approver_assistant_id IS NOT NULL
	
	UNION 
	-- 4.4 Approver Assistant Group
	SELECT
	    ug.usr_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	JOIN ik_usr_grp ug ON ug.grp_id = a.approver_assistant_grp_id
	WHERE a.approver_assistant_grp_id IS NOT NULL
	
	-- 4.5 Approver2
	UNION
	SELECT
	    a.approver2_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	WHERE a.approver2_id IS NOT NULL AND e.claim_amt >= a.approver2_min_amount
	
	-- 4.6 Approver2 Group
	UNION
	SELECT
	    ug.usr_id AS usr_id,
	    e.id AS expense_id,
	    'admin' AS acl
	FROM es_expense e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	JOIN ik_usr_grp ug ON ug.grp_id = a.approver2_grp_id
	WHERE a.approver2_grp_id IS NOT NULL AND e.claim_amt >= a.approver2_min_amount
	
	-- 5. UserRole with acl
	UNION
    SELECT ur.usr_id,
        e.id AS expense_id,
        ur.role AS acl
    FROM es_expense e
    JOIN es_userrole ur ON ur.enable IS TRUE
    WHERE (ur.office_id IS NULL OR ur.office_id = e.office_id) 
      AND (ur.target_usr_id IS NULL OR ur.target_usr_id = e.claimer_id) 
	  AND (ur.target_usr_grp_id IS NULL OR (EXISTS (SELECT ug.id FROM ik_usr_grp ug WHERE ug.grp_id = ur.target_usr_grp_id AND e.claimer_id = ug.usr_id))) 
	  AND (ur.prj_nm IS NULL 
	       OR TRIM(BOTH FROM ur.prj_nm) = '' 
		   OR ur.prj_nm IS NOT NULL AND (EXISTS (SELECT ed.id FROM es_expensedetail ed WHERE ed.hdr_id = e.id AND ed.prj_nm IS NOT NULL AND ed.prj_nm ~~ replace(replace(ur.prj_nm, '*', '%'), '?', '_')))
		  )
	) a
;
COMMENT ON VIEW es_v_user_expense IS 'Query the expenses that user can accessable';

-- create view es_v_user_cash_advancement
CREATE OR REPLACE VIEW es_v_user_cash_advancement AS
 SELECT DISTINCT * FROM (
	-- 1. Claimer can access their own expense (admin)
	SELECT
	    e.claimer_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	
	-- 2. Accounting permission (admin)
	UNION
	SELECT
	    a.usr_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_accounting a ON a.office_id = e.office_id
	
	-- 3. Approver / Assistant / Approver2 roles (admin)
	-- 3.1 Approver
	UNION
	SELECT
	    a.approver_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	WHERE a.approver_id IS NOT NULL
	
	-- 3.2 Approver Group
	UNION
	SELECT
	    ug.usr_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	JOIN ik_usr_grp ug ON ug.grp_id = a.approver_grp_id
	WHERE a.approver_grp_id IS NOT NULL
	
	-- 3.3 Approver Assistant
	UNION
	SELECT
	    a.approver_assistant_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	WHERE a.approver_assistant_id IS NOT NULL
	 
	-- 3.4 Approver Assistant Group
	UNION
	SELECT
	    ug.usr_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	JOIN ik_usr_grp ug ON ug.grp_id = a.approver_assistant_grp_id
	WHERE a.approver_assistant_grp_id IS NOT NULL
	
	-- 3.5 Approver2
	UNION
	SELECT
	    a.approver2_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	WHERE a.approver2_id IS NOT NULL AND e.claim_amt >= a.approver2_min_amount
	
	UNION
	
	-- 3.6 Approver2 Group
	SELECT
	    ug.usr_id AS usr_id,
	    e.id AS ca_id,
	    'admin' AS acl
	FROM es_cashadvancement e
	JOIN es_approver a ON a.enable IS true AND a.office_id = e.office_id
	JOIN ik_usr_grp ug ON ug.grp_id = a.approver2_grp_id
	WHERE a.approver2_grp_id IS NOT NULL AND e.claim_amt >= a.approver2_min_amount
	
	-- 4. UserRole with acl
	UNION
    SELECT ur.usr_id,
        e.id AS ca_id,
        ur.role AS acl
    FROM es_cashadvancement e
    JOIN es_userrole ur ON ur.enable IS TRUE
    WHERE (ur.office_id IS NULL OR ur.office_id = e.office_id) 
      AND (ur.target_usr_id IS NULL OR ur.target_usr_id = e.claimer_id) 
	  AND (ur.target_usr_grp_id IS NULL OR (EXISTS (SELECT ug.id FROM ik_usr_grp ug WHERE ug.grp_id = ur.target_usr_grp_id AND e.claimer_id = ug.usr_id)))
	) a
;
COMMENT ON VIEW es_v_user_cash_advancement IS 'Query the cash advancement that user can accessable';
