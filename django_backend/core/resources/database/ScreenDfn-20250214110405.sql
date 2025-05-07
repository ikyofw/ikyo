UPDATE ik_screen
SET app_nm = split_part(class_nm, '.', 1);