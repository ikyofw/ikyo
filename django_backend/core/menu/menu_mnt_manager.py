'''
Description: Menu Management
version:
Author: YL
Date: 2024-06-21 14:55:50
'''
import logging

import core.models as ikModels
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.menu.menuManager import MenuManager
from core.utils.langUtils import isNotNullBlank, isNullBlank

logger = logging.getLogger('ikyo')


def get_parent_menu() -> list:
    qs = ikModels.Menu.objects.all().order_by('parent_menu_id', 'order_no', "menu_nm")
    data = []
    for i in qs:
        parent_menu_caption = i.menu_caption
        parent_menu_id = i.parent_menu_id
        parent_order_no = i.order_no
        menu_level_index = 0
        # Get parent menu caption and parent order_no, eg: Top Menu >> Level 1 Menu >> Level 2 Menu
        while isNotNullBlank(parent_menu_id) and menu_level_index < 2:
            parent_menu = ikModels.Menu.objects.filter(id=parent_menu_id).first()
            if parent_menu:
                parent_menu_caption = parent_menu.menu_caption + " -> " + parent_menu_caption
                parent_order_no = parent_menu.order_no
                parent_menu_id = parent_menu.parent_menu_id
                menu_level_index += 1
            else:
                break

        if menu_level_index <= 2 and isNullBlank(parent_menu_id):  # It's Top Menu if parent_menu_id is null
            data.append({
                'parent_menu_id': i.id,
                'parent_menu': parent_menu_caption,
                'parent_order_no': parent_order_no if isNotNullBlank(parent_order_no) else 0
            })

    # Sort data by parent_order_no first, then by parent_menu
    data.sort(key=lambda x: (x['parent_order_no'], x['parent_menu']))
    data.insert(0, {'parent_menu_id': 0, 'parent_menu': '--Top Menu--'})
    return data


def get_menu_tree() -> list:
    qs = ikModels.Menu.objects.all().order_by("parent_menu_id", "order_no", "menu_nm")
    data = []
    # build a dictionary to store the mapping relationship between menu_id and menu_caption
    menu_caption_map = {menu.id: menu.menu_caption for menu in qs}

    # build menu tree
    menu_tree = {}
    for menu in qs:
        parent_id = menu.parent_menu_id if menu.parent_menu_id is not None else 0
        if parent_id not in menu_tree:
            menu_tree[parent_id] = []
        menu_tree[parent_id].append(menu)

        # iterator
        def add_to_data(menu_list, parent_caption=''):
            for menu in menu_list:
                if menu.id in menu_tree:
                    current_caption = f"{parent_caption} >> {menu_caption_map[menu.id]}" if parent_caption else menu_caption_map[menu.id]
                    data.append({
                        'id': menu.id,
                        'parent_menu_id': menu.parent_menu_id if isNotNullBlank(menu.parent_menu_id) else 0,
                        'parent_menu': parent_caption,
                        'menu_nm': menu.menu_nm,
                        'menu_caption': menu.menu_caption,
                        'screen_nm': menu.screen_nm,
                        'order_no': menu.order_no,
                        'sub_menu_lct': menu.sub_menu_lct,
                        'dsc': menu.dsc
                    })
                    add_to_data(menu_tree[menu.id], current_caption)
                else:
                    data.append({
                        'id': menu.id,
                        'parent_menu_id': menu.parent_menu_id if isNotNullBlank(menu.parent_menu_id) else 0,
                        'parent_menu': parent_caption,
                        'menu_nm': menu.menu_nm,
                        'menu_caption': menu.menu_caption,
                        'screen_nm': menu.screen_nm,
                        'order_no': menu.order_no,
                        'sub_menu_lct': menu.sub_menu_lct,
                        'dsc': menu.dsc
                    })

    # top menu start
    top_level_menus = menu_tree.get(0, [])
    add_to_data(top_level_menus)
    return data


def save_menus(user_id: int, menu_fg: list[ikModels.Menu]) -> Boolean2:
    data = []
    for i in menu_fg:
        if i.ik_is_status_retrieve():
            continue
        else:
            if i.ik_is_status_delete():  # delete
                data.append(i)
                # check sub menus, if delete set sub menu's parent_id = null
                sub_menu_rcs = ikModels.Menu.objects.filter(parent_menu_id=i.id)
                for sub_menu in sub_menu_rcs:
                    sub_menu.parent_menu_id = None
                    sub_menu.ik_set_status_modified()
                    data.append(sub_menu)
            else:
                if i.ik_is_status_new():  # new
                    if ikModels.Menu.objects.filter(menu_nm=i.menu_nm).count() > 0:
                        return Boolean2(False, "The menu name: [%s] already exists, please change it." % i.menu_nm)
                    if i.parent_menu_id == 0:
                        i.parent_menu_id = None
                else:  # update
                    if i in data:  # menu is update status & parent menu is delete status
                        data.remove(i)
                        i.parent_menu_id = None
                    sub_menu_level = MenuManager.isSubMenus(i.parent_menu_id, i.id)
                    if sub_menu_level > 0:
                        message = "Parent menu [%s] error: " % MenuManager.getMenuName(i.parent_menu_id)
                        if sub_menu_level == 1:
                            message += "The intended parent menu cannot be itself."
                        else:
                            message += "The intended parent menu is in the subtree of the current menu."
                        return Boolean2(False, message)
                    if ikModels.Menu.objects.filter(menu_nm=i.menu_nm).count() > 1:
                        return Boolean2(False, "The menu name: [%s] already exists, please change it." % i.menu_nm)
                    if i.parent_menu_id == 0:
                        i.parent_menu_id = None
                data.append(i)  # new, update

    ptrn = IkTransaction(userID=user_id)
    ptrn.add(data)
    b = ptrn.save()
    if not b.value:
        return b
    return Boolean2(True, "Saved")
