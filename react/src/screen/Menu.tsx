import { useEffect, useState } from "react"
import cookie from "react-cookies"
import * as Loading from "../components/Loading"
import TableFg from "../components/TableFg"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { getScreenDfn, validateResponse } from "../utils/sysUtil"
import { getPluginParams } from "../components/Screen"

const pyiGlobal = pyiLocalStorage.globalParams
const img_goto = pyiGlobal.PUBLIC_URL + "images/goto_sbutton.gif"
const img_goto2 = pyiGlobal.PUBLIC_URL + "images/goto_sbutton2.gif"
const img_current = pyiGlobal.PUBLIC_URL + "images/current_sbutton.gif"

const Menu = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const fgNames = ["MenuFg_level_1", "MenuFg_level_2", "MenuFg_level_3"]

  const [rowStatus, setRowStatus] = useState([{}, {}, {}])

  const [menuPageJson_L1, setMenuPageJson_L1] = useState(Object)
  const [menuPageJson_L2, setMenuPageJson_L2] = useState(Object)
  const [menuPageJson_L3, setMenuPageJson_L3] = useState(Object) // save the fetched screen

  const [screenEditable, setScreenEditable] = useState(Boolean)

  const MENU_KEY = pyiGlobal.COOKIE_MENU_ID
  const lastSelectedMenuId = cookie.load(MENU_KEY)

  useEffect(() => {
    refreshMenu()
  }, [])

  const refreshMenu = async () => {
    try {
      await HttpGet("/api/menu/initScreen")
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          initPage()
        })
    } catch (error) {
      pyiLogger.error("Load screen failed: " + error, true)
    }
  }

  const initPage = async () => {
    Loading.show()
    // get table data
    try {
      await HttpGet("/api/menu/getScreen?last=" + (lastSelectedMenuId ? lastSelectedMenuId : ""))
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          let screenDfn = getScreenDfn(result)
          if (!screenDfn) {
            pyiLogger.error("get screenDfn error, please check.", true)
            return
          }
          setScreenEditable(screenDfn.editable)

          fgNames.forEach((fgName: string) => {
            const pluginParams = getPluginParams(screenDfn[fgName])
            screenDfn[fgName]["pluginParams"] = pluginParams
          })
          setMenuPageJson_L1(screenDfn.MenuFg_level_1)
          setMenuPageJson_L2(screenDfn.MenuFg_level_2)
          setMenuPageJson_L3(screenDfn.MenuFg_level_3)

          let rowStatus = [{}, {}, {}]
          fgNames.forEach((fgName: string, index: number) => {
            let data = {}
            if (screenDfn[fgName]["data"]) {
              screenDfn[fgName]["data"].forEach((row) => {
                const key = row.id
                data[key] = row.rowStatus
              })
            }
            rowStatus[index] = data
          })
          setRowStatus(rowStatus)
        })

      pyiLocalStorage.clearSysMsgs()
    } catch (error) {
      Loading.remove()
      console.log(error);
      
      pyiLogger.error("Load screen failed: " + error, true)
    } finally {
      Loading.remove()
    }
  }

  const gotoCallback_1 = async (id) => {
    let jumpFlag = false
    menuPageJson_L1 &&
      menuPageJson_L1.data.forEach((menu) => {
        if (String(menu.id) === String(id) && String(menu.rowStatus) === '0') {
          jumpFlag = true
          window.location.href = "http://" + window.location.host + "/" + menu.screen_nm
        }
      })
    if (jumpFlag) {
      return
    }

    const pluginPrams = menuPageJson_L1.pluginParams[0]
    try {
      await HttpPost(pluginPrams.eventHandler, JSON.stringify({ activeRow: id }))
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, false)) {
            initPage()
          }
        })
    } catch (error) {
      Loading.remove()
      pyiLogger.error(pluginPrams.eventHandler + " error: " + error, true)
    } finally {
      Loading.remove() // can't delete
    }
  }
  const gotoCallback_2 = async (id) => {
    let jumpFlag = false
    menuPageJson_L2 &&
      menuPageJson_L2.data.forEach((menu) => {
        if (String(menu.id) === String(id) && String(menu.rowStatus) === '0') {
          jumpFlag = true
          window.location.href = "http://" + window.location.host + "/" + menu.screen_nm
        }
      })
    if (jumpFlag) {
      return
    }

    const pluginPrams = menuPageJson_L2.pluginParams[0]
    try {
      await HttpPost(pluginPrams.eventHandler, JSON.stringify({ activeRow: id }))
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, false)) {
            initPage()
          }
        })
    } catch (error) {
      Loading.remove()
      pyiLogger.error(pluginPrams.eventHandler + " error: " + error, true)
    } finally {
      Loading.remove() // can't delete
    }
  }
  const gotoCallback_3 = (id) => {
    menuPageJson_L3 &&
      menuPageJson_L3.data.forEach((menu) => {
        if (String(menu.id) === String(id) && String(menu.rowStatus) === '0') {
          window.location.href = "http://" + window.location.host + "/" + menu.screen_nm
        }
      })
  }

  const gotoColumn_1 = createGotoColumn(gotoCallback_1, img_goto, img_goto2, img_current, rowStatus[0])
  const gotoColumn_2 = createGotoColumn(gotoCallback_2, img_goto, img_goto2, img_current, rowStatus[1])
  const gotoColumn_3 = createGotoColumn(gotoCallback_3, img_goto, img_goto2, img_current, rowStatus[2])

  return (
    <div className="level_0">
      <div className="level_1">
        {menuPageJson_L1 && String(menuPageJson_L1.type).trim().toLocaleLowerCase() === "table" ? (
          <TableFg tableParams={menuPageJson_L1} pluginList={[gotoColumn_1]} editable={screenEditable} />
        ) : null}
      </div>
      <div className="level_2">
        {menuPageJson_L2 && String(menuPageJson_L2.type).trim().toLocaleLowerCase() === "table" ? (
          <TableFg tableParams={menuPageJson_L2} pluginList={[gotoColumn_2]} editable={screenEditable} />
        ) : null}
      </div>
      <div className="level_3">
        {menuPageJson_L3 && String(menuPageJson_L3.type).trim().toLocaleLowerCase() === "table" ? (
          <TableFg tableParams={menuPageJson_L3} pluginList={[gotoColumn_3]} editable={screenEditable} />
        ) : null}
      </div>
    </div>
  )
}
export default Menu

function createGotoColumn(myCallback: any, icon0: any, icon1: any, icon2: any, rowStatus: {}, header?: string) {
  //create plugin
  if (!header) {
    header = " "
  }
  const IconHeader = () => <th className="Spreadsheet__header Spreadsheet__header__column">{header}</th>
  const IconCell = (props: any) => (
    <th className="Spreadsheet__header">
      {
        <img
        src={rowStatus[props.id] === 0 ? icon0 : (rowStatus[props.id] === 1 ? icon1 : icon2)}
          alt=""
          onClick={() => myCallback(props.id)}
          style={{ cursor: "pointer" }}
        />
      }
    </th>
  )
  return { IconHeader, IconCell }
}