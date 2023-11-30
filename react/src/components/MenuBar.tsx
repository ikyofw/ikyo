/*
 * @Description:
 * @version:
 * @Author: Sunny
 * @Date: 2022-04-19 09:32:27
 */
import classnames from "classnames"
import { useEffect, useState } from "react"
import cookie from "react-cookies"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"

const pyiGlobal = pyiLocalStorage.globalParams

const MenuBar = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const MENU_KEY = pyiGlobal.COOKIE_MENU_ID
  const MENU_ACTION = pyiGlobal.COOKIE_MENU_ACTION
  const lastSelectedMenuId = cookie.load(MENU_KEY)
  // cookie.remove(KEY, { path: "/" })
  const path = window.location.pathname

  const [selectedL0MenuId, setSelectedL0MenuId] = useState(lastSelectedMenuId)
  const [selectedL1MenuId, setSelectedL1MenuId] = useState(lastSelectedMenuId)
  const [menu0Data, setMenu0Data] = useState([])
  const [menu1Data, setMenu1Data] = useState([])

  useEffect(() => {
    refreshMenu()
  }, [])

  const refreshMenu = async () => {
    try {
      await HttpGet("/api/menubar/getMenubar?currentPath=" + path)
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          if (sysUtil.validateResponse(result, true)) {
            let menu0s: any[] = []
            let menu1s: any[] = []
            if (result.data) {
              for (let menu of result.data) {
                menu0s.push(menu)
                if (menu.isCurrentMenu) {
                  setSelectedL0MenuId(menu.id)
                }
                if (menu.subMenus) {
                  for (let subMenu of menu.subMenus) {
                    menu1s.push(subMenu)
                    if (subMenu.isCurrentMenu) {
                      setSelectedL1MenuId(subMenu.id)
                    }
                  }
                }
              }
            }
            setMenu0Data(menu0s)
            setMenu1Data(menu1s)
          }
        })
    } catch (error) {
      pyiLogger.error("Load screen failed: " + error, true)
    }
  }

  function updateCurrentMenu(menu) {
    if (menu.action && menu.action.trim().toLocaleLowerCase() === "logout") {
      cookie.remove(MENU_KEY, { path: "/" })
      cookie.remove(MENU_ACTION, { path: "/" })
      // pyiLocalStorage.clearStore() // do not clear, for Logout menu
      return
    }
    if (menu.id) {
      // YL, 2023-04-17 set last menu selected expire after 7 days.
      const expireDate = new Date()
      expireDate.setDate(expireDate.getDate() + 7) // expires in 7 days
      cookie.save(MENU_KEY, menu.id, { path: "/", expires: expireDate })
      cookie.save(MENU_ACTION, menu.action, { path: "/", expires: expireDate })
    } else {
      cookie.remove(MENU_KEY, { path: "/" })
      cookie.remove(MENU_ACTION, { path: "/" })
    }
  }

  function SubMenuBar(props) {
    const level = props.level
    const menus = props.menus
    const selectedMenuId = props.selectedMenuId

    const menuItems = menus.map((menu) => (
      <li key={menu.id} className={selectedMenuId && String(selectedMenuId) === String(menu.id) ? "currentMenu" : level}>
        <a
          href={"/" + menu.action}
          onClick={(e) => {
            updateCurrentMenu(menu)
          }}
        >
          <span>{menu.title}</span>
        </a>
      </li>
    ))

    return (
      <div className={classnames("sys-top-menu-bar", `sys-top-menu-bar--${level}`)}>
        <ul>{menuItems}</ul>
      </div>
    )
  }
  return (
    <div className="sys-menu">
      <SubMenuBar level={"L0"} menus={menu0Data} selectedMenuId={selectedL0MenuId} />
      {menu1Data.length > 0 ? <SubMenuBar level={"L1"} menus={menu1Data} selectedMenuId={selectedL1MenuId} /> : null}
    </div>
  )
}

export default MenuBar
