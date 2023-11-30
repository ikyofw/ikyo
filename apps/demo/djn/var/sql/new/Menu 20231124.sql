--- Demo Menus
INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc)
VALUES (0, 'DevDemo', 'DevDemo', null, null, true, 10, null, null, null);

INSERT INTO ik_menu (version_no, menu_nm, menu_caption, screen_nm, parent_menu_id, enable, order_no, is_free_access, sub_menu_lct, dsc) VALUES 
(0, 'BeforeDisplayAdapterDemo', 'Before Display Adapter Demo', 'BeforeDisplayAdapterDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'ButtonBoxDemo', 'Button Box Demo', 'ButtonBoxDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'CheckBoxDemo', 'Check Box Demo', 'CheckBoxDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'ComboBoxDemo', 'Combo Box Demo', 'ComboBoxDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'DetailTableDemo', 'Detail Table Demo', 'DetailTableDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'DialogDemo', 'Dialog Demo', 'DialogDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'HtmlDemo', 'Html Demo', 'HtmlDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'IconAndTextDemo', 'Icon And Text Demo', 'IconAndTextDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'PageableDemo', 'Pageable Demo', 'PageableDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'PDFViewerDemo', 'PDF Viewer Demo', 'PDFViewerDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'SearchFgDemo', 'SearchFg Demo', 'SearchFgDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'SimpleFgDemo', 'SimpleFg Demo', 'SimpleFgDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'TableDemo', 'Table Demo', 'TableDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'TableHeaderFooterDemo', 'Table Header Footer Demo', 'TableHeaderFooterDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'TableStyleDemo', 'Table Style Demo', 'TableStyleDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'TextareaDemo', 'Textarea Demo', 'TextareaDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null),
(0, 'UploadAndDownloadDemo', 'Upload And Download Demo', 'UploadAndDownloadDemo', (SELECT id FROM ik_menu WHERE menu_nm = 'DevDemo'), true, 10, null, null, null);