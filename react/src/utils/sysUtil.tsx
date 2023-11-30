import moment from "moment"
import React from "react"
import cookie from "react-cookies"
import ReactDOM from "react-dom"
import { Tooltip } from "react-tooltip"
import * as Loading from "../components/Loading"
import SysMsgBox from "../components/SysMsgBox"
import { useHttp } from "./http"
import pyiLogger from "./log"
import pyiLocalStorage from "./pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams
const MENU_ACTION = pyiGlobal.COOKIE_MENU_ACTION
const backImg = pyiGlobal.PUBLIC_URL + "images/back.png"

const INFO_MSG = "info"
const DEBUG_MSG = "debug"
const WARNING_MSG = "warning"
const ERROR_MSG = "error"
const EXCEPTION_MSG = "exception"

// date format option 1
const dateStringFormat = "YYYY-MM-DD"
// date format option 2
const dateTimeStringFormat = "YYYY-MM-DD HH:mm:ss"
// date format option 3
const timeStringFormat = "HH:mm:ss"
const defaultFormat = dateStringFormat

export function clearMessage() {
  if (document.getElementById("sysMsgTitle")) {
    ReactDOM.unmountComponentAtNode(document.getElementById("sysMsgTitle"))
  }
}

export function saveMessage(messages: Array<Object>) {
  if (messages && messages.length > 0) {
    messages.forEach((msg: any) => {
      pyiLocalStorage.setSysMsgs(msg)
    })
  }
}

export function showMessage(messages: Array<Object>) {
  clearMessage()

  let localSysMsgStr = pyiLocalStorage.getSysMsgs()
  let localSysMsgArr: any[]
  if (localSysMsgStr) {
    localSysMsgArr = JSON.parse(localSysMsgStr)
  }
  let messageArr = []
  if (localSysMsgArr) {
    localSysMsgArr.forEach((msg: JSON, index) => {
      let isExists = messageArr.findIndex((element) => element.type === msg["type"] && element.message === msg["message"])
      if (messageArr.indexOf(msg) <= 0 && isExists <= -1) {
        messageArr.push(msg)
      }
    })
  }

  if (messages && messages.length > 0) {
    // clearMessage()
    messages.forEach((msg: JSON, index) => {
      let isExists = messageArr.findIndex((element) => element.type === msg["type"] && element.message === msg["message"])
      if (messageArr.indexOf(msg) <= 0 && isExists <= -1) {
        messageArr.push(msg)
      }
    })
  }
  if (messageArr && messageArr.length > 0 && document.getElementById("sysMsgTitle")) {
    let msgComponent: any = (
      <div style={{ padding: "2px 20px 2px 20px " }}>
        {messageArr.map((msgObj, index) => {
          return msgObj["type"] && msgObj["message"] ? (
            <SysMsgBox
              key={index}
              ref={(input) => {
                if (input != null) {
                  input.focus({
                    cursor: "end",
                  })
                }
              }}
              label={msgObj["type"]}
              name={"msgBox"}
              editable={true}
              value={msgObj["message"]}
            />
          ) : null
        })}
      </div>
    )
    document.body.scrollTop = 0
    document.documentElement.scrollTop = 0
    ReactDOM.render(msgComponent, document.getElementById("sysMsgTitle"))
  }
}

export function showInfoMessage(msg: string) {
  showMessage([{ type: INFO_MSG, message: msg }])
}

export function showDebugMessage(msg: string) {
  showMessage([{ type: DEBUG_MSG, message: msg }])
}

export function showErrorMessage(msg: string) {
  showMessage([{ type: ERROR_MSG, message: msg }])
}

export function showWarningMessage(msg: string) {
  showMessage([{ type: WARNING_MSG, message: msg }])
}

export function showExceptionMessage(msg: string) {
  showMessage([{ type: EXCEPTION_MSG, message: msg }])
}

export function showScreenTitle(title: string) {
  const TooltipComponent = () => {
    const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
    const path = window.location.pathname

    const [backMenus, setBackMenus] = React.useState([])

    React.useEffect(() => {
      refreshMenu()
    }, [])

    const refreshMenu = async () => {
      try {
        await HttpGet("/api/menu/getBackMenus")
          .then((response) => {
            if (response.ok) return response.json()
            throw response
          })
          .then((result) => {
            if (validateResponse(result, true)) {
              setBackMenus(result.data)
            }
          })
      } catch (error) {
        pyiLogger.error("Load screen failed: " + error, true)
      }
    }

    const handleClick = () => {
      window.location.href = "http://" + window.location.host + "/menu"
    }

    return (
      <>
        {path && path.toLocaleLowerCase() !== "/menu" && path.toLocaleLowerCase() !== "/home" ? (
          <>
            <img
              src={backImg}
              alt="back"
              onClick={handleClick}
              style={{ paddingRight: "3px" }}
              data-tooltip-id={"back-tooltip"}
              data-tooltip-place="bottom"
            />
            <Tooltip id={"back-tooltip"} className="tooltip" clickable={true}>
              <a href={"/menu"} className="tooltip-action" style={{ color: "yellow", display: "block" }}>
                Back To Menu Page
              </a>
              {backMenus.map((backMenu: string, index: number) => {
                return (
                  <a href={"/" + backMenu["screen_nm"]} className="tooltip-action" style={{ color: "white", display: "block" }}>
                    {(index + 1).toString().padStart(2, "0") + ". " + backMenu["menu_caption"]}
                  </a>
                )
              })}
            </Tooltip>
          </>
        ) : null}
        {title}
      </>
    )
  }

  if (document.getElementById("sysScreenTitle")) {
    ReactDOM.unmountComponentAtNode(document.getElementById("sysScreenTitle"))
  }

  ReactDOM.render(<TooltipComponent />, document.getElementById("sysScreenTitle"))
}

export function getScreenDfn(responseJson: any, refreshPage: Boolean) {
  //  if refreshPage is true, clear previous messages and display all messages; else only save current message
  if (refreshPage || responseJson.code === 0) {
    showMessage(responseJson.messages)
  } else {
    saveMessage(responseJson.messages)
  }

  if (responseJson.logLevel) {
    localStorage.setItem("__LOG_LEVEL__", responseJson.logLevel)
  }
  if (responseJson.code === 1) {
    if (responseJson.data && (responseJson.data.viewID || responseJson.data.viewTitle)) {
      showScreenTitle(responseJson.data.viewID + (responseJson.data.viewID ? " - " : "") + responseJson.data.viewTitle)
    }
    return responseJson.data
  } else if (Number(responseJson.code) === 100001) {
    pyiLocalStorage.clearStore()
    updateCurrentMenu(window.location.pathname + window.location.search)
    window.location.href = "/login"
  }
  return responseJson.data
}

export function getResponseData(responseJson: any) {
  // every http request will call this, should have this if check.
  if (responseJson.messages) {
    saveMessage(responseJson.messages)
  }

  if (responseJson.code === 1) {
    if (responseJson.href) {
      window.location.href = responseJson.href.url
    }
    return responseJson.data
  } else if (Number(responseJson.code) === 100001) {
    pyiLocalStorage.clearStore()
    updateCurrentMenu(window.location.pathname + window.location.search)
    window.location.href = "/login"
  } else {
    showMessage(responseJson.messages)
  }
  return responseJson.data
}

export function validateResponse(responseJson: any, refreshPage: Boolean) {
  //  if refreshPage is true, clear previous messages and display message; else only save current message
  if (refreshPage && responseJson.messages && responseJson.messages.length > 0) {
    showMessage(responseJson.messages)
  } else {
    saveMessage(responseJson.messages)
  }

  if (responseJson.code === 1) {
    if (responseJson.href) {
      window.location.href = responseJson.href.url
    }
    return true
  } else if (Number(responseJson.code) === 100001) {
    pyiLocalStorage.clearStore()
    updateCurrentMenu(window.location.pathname + window.location.search)
    window.location.href = "/login"
  } else {
    showMessage(responseJson.messages)
    Loading.remove()
  }
  return false
}

export function updateCurrentMenu(screenNm) {
  const expireDate = new Date()
  expireDate.setDate(expireDate.getDate() + 7) // expires in 7 days
  cookie.save(MENU_ACTION, screenNm, { path: "/", expires: expireDate })
}

// YL, 2023-05-31 Date part - start
export function getDateFormatStr(format: number | string) {
  var formatStr
  if (typeof format == "number") {
    switch (format) {
      case 1:
        formatStr = dateStringFormat
        break
      case 2:
        formatStr = dateTimeStringFormat
        break
      case 3:
        formatStr = timeStringFormat
        break
      default:
        formatStr = defaultFormat
    }
  } else if (typeof format == "string") {
    switch (format.trim().toLocaleUpperCase()) {
      case dateStringFormat.trim().toLocaleUpperCase():
        formatStr = dateStringFormat
        break
      case dateTimeStringFormat.trim().toLocaleUpperCase():
        formatStr = dateTimeStringFormat
        break
      case timeStringFormat.trim().toLocaleUpperCase():
        formatStr = timeStringFormat
        break
      default:
        formatStr = defaultFormat
    }
  }
  return formatStr
}

export function formatDate(dateStr: string, format: string) {
  if (format === timeStringFormat) {
    return verifyIsTime(dateStr) ? dateStr : ""
  } else {
    return verifyIsDate(dateStr) ? moment(dateStr).format(format) : ""
  }
}

export function verifyIsDate(dateStr: string) {
  var newDate = new Date(dateStr)
  return Object.prototype.toString.call(newDate) === "[object Date]" && !isNaN(newDate.getTime())
}

export function verifyIsTime(timeStr: string) {
  // 24-hour format
  var regex = /^([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$/
  return regex.test(timeStr)
}

// YL, 2023-05-31 - end
