## Database Menu Table

[![Datebase menu
model.png](images/Datebase_menu_model.png)](images/Datebase_menu_model.png)

Whenever a new page is added, a new entry must be added to this table for the
new page.

menu_nm: Menu name

menu_caption: Menu caption

screen_nm: Screen name. In most cases, the actual value is the same as the
menu name. It's null when there is no actual corresponding page (e.g. parent
menu)

parent_menu_id: Parent menu id.

enable: If enable is false, this menu will be ignored.

order_no: Setting the display order of submenus under the same parent menu.

is_free_access: If is_free_access is true, this menu will be visible for
everyone.

sub_menu_lct: If sub_menu_lct is top, the secondary menu will be displayed on
the page.

ctg:Where the static files for this page are stored.

code:In most cases, the actual value is the same as the menu name.

