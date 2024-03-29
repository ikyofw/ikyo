import transform from "css-to-react-native"
import React, { Ref, forwardRef, useImperativeHandle, useState } from "react"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { getScreenDfn, saveMessage, showErrorMessage, showInfoMessage, validateResponse } from "../utils/sysUtil"
import { DialogContext } from "./ConText"
import CustomDialog, { getDialogEvent, getDialogEventHandler, getDialogEventParamArr, getDialogParams } from "./Dialog"
import FileViewer from "./FileViewer"
import * as Loading from "./Loading"
import SearchFg from "./SearchFg"
import SimpleFg from "./SimpleFg"
import TableFg, { createIconColumn } from "./TableFg"
import ToolBar from "./ToolBar"
import Html from "./html/Html"
import IFrame from "./html/IFrame"
import GetSitePlan from "./sitePlan/GetSitePlan"

const pyiGlobal = pyiLocalStorage.globalParams

interface IScreenBox {
  ref: any
  fgNames: String[]
  screenID: any
  subScreenNm?: string
}

const Screen: React.FC<IScreenBox> = forwardRef((props, ref: Ref<any>) => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)
  const HttpPostNoHeader = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST_NO_HEADER)
  const HttpDownload = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD)

  useImperativeHandle(ref, () => {
    // send data to parent component
    return {
      refs,
      getData: (dialogType) => {
        let data = {}
        if (dialogType === pyiGlobal.DIALOG_TYPE_UPLOAD) {
          props.fgNames.forEach((fgName: string) => {
            data = refs[fgName].current.formData()
          })
        } else {
          data = createEventData(props.fgNames)
        }
        return data
      },
    }
  })

  const [refs, setRefs] = useState<Record<string, React.MutableRefObject<any>>>(() => {
    const initialRefs = {}
    props.fgNames.forEach((fgName: string) => {
      initialRefs[fgName] = React.createRef()
    })
    return initialRefs
  })

  const [screenJson, setScreenJson] = useState(Object)
  const [screenLayoutParams, setScreenLayoutParams] = useState(Object)
  const [screenPlugin, setScreenPlugin] = useState(Object)
  const [screenPluginLists, setScreenPluginLists] = useState(Object)
  const [autoRefresh, setAutoRefresh] = useState(Object)
  const [resources, setResources] = useState(Object)

  const [screenEditable, setScreenEditable] = useState(Boolean)

  const [helpUrl, setHelpUrl] = useState(String)
  const [helpDocTp, setHelpDocTp] = useState(String)

  const [pageRefreshFlag, setPageRefreshFlag] = useState(() => {
    const initialFlags = {}
    props.fgNames.forEach((fgName: string) => {
      initialFlags[fgName] = 1
    })
    return initialFlags
  })
  const [sitePlanRefreshFlag, setSitePlanRefreshFlag] = useState(1)

  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [dialogPrams, setDialogPrams] = React.useState({ onCancel: () => closeDialog() })

  React.useEffect(() => {
    const newRefs = { ...refs }
    props.fgNames.forEach((fgName: string) => {
      if (!newRefs[fgName]) {
        newRefs[fgName] = React.createRef()
      }
    })
    setRefs(newRefs)
  }, [props.fgNames])

  const createEventData = (eventHandlerParameter: any) => {
    let eventData = {}
    if (!eventHandlerParameter || eventHandlerParameter.length <= 0) {
      eventData = {}
    } else if (eventHandlerParameter[0] === "*") {
      props.fgNames.forEach((fgName: string) => {
        eventData[fgName] = createDataByFgName(fgName)
      })
    } else {
      eventHandlerParameter.forEach((fgName: string) => {
        eventData[fgName] = createDataByFgName(fgName)
      })
    }
    return eventData
  }
  const createDataByFgName = (fgName: string) => {
    let data
    if (screenJson[fgName] && refs[fgName].current) {
      if (screenJson[fgName].type === pyiGlobal.TABLE_TYPE) {
        data = refs[fgName].current.data
      } else if (screenJson[fgName].type === pyiGlobal.TABLE_TYPE_RESULT) {
        data = refs[fgName].current.data
      } else if (screenJson[fgName].type === pyiGlobal.SIMPLE_TYPE || screenJson[fgName].type === pyiGlobal.SEARCH_TYPE) {
        data = refs[fgName].current.formDataToJson()
      }
    }
    return data
  }

  const closeDialog = () => {
    setDialogOpen(false)
  }
  const openDialog = (params) => {
    setDialogPrams(params)
    setDialogOpen(true)
  }

  React.useEffect(() => {
    refreshList()
  }, []) // page refresh

  // set page data
  const refreshList = async () => {
    setSitePlanRefreshFlag(sitePlanRefreshFlag + 1)
    Loading.show()
    // get table data
    try {
      let params = ""
      if (props.subScreenNm) {
        params = "?" + pyiGlobal.SUB_SCREEN_KEY_NAME + "=" + props.subScreenNm
      }
      await HttpGet("/api/" + props.screenID + "/getScreen" + params)
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          // YL, 2022-12-27 load static files.
          let screenDfn_0 = getScreenDfn(result, true)
          if (!screenDfn_0) {
            pyiLogger.error("get screenDfn error, please check.", true)
            return
          }
          setScreenEditable(screenDfn_0.editable)
          let screenDfnDic = {}
          let screenPlugin = {}
          let refreshPrams = {}
          let htmlFlag = false
          props.fgNames.forEach((fgName: string) => {
            if (
              screenDfn_0[fgName] &&
              (screenDfn_0[fgName].type === pyiGlobal.TABLE_TYPE || screenDfn_0[fgName].type === pyiGlobal.TABLE_TYPE_RESULT)
            ) {
              const pluginParams = getPluginParams(screenDfn_0[fgName])
              screenPlugin[fgName] = pluginParams
              screenDfn_0[fgName]["pluginParams"] = pluginParams
            }
            screenDfnDic[fgName] = screenDfn_0[fgName]
            if (screenDfn_0[fgName] && screenDfn_0[fgName].type === pyiGlobal.HTML) {
              htmlFlag = true
            }
          })
          if (result.resources && result.resources.length > 0) {
            if (htmlFlag) {
              // If need to add static resources and there is an html component on the page,
              // save the static resources and pass them to the html component, then add static resources to the html component.
              setResources(result.resources)
            } else {
              // No html components, add static resources directly
              result.resources.forEach((resource) => {
                addStaticResource(resource)
              })
            }
          }

          if (autoRefresh && Object.keys(autoRefresh).length === 0) {
            refreshPrams["autoRefreshInterval"] = screenDfn_0["autoRefreshInterval"]
            refreshPrams["autoRefreshAction"] = screenDfn_0["autoRefreshAction"]
            setAutoRefresh(refreshPrams)
          }

          setScreenLayoutParams(parseLayoutParams(screenDfn_0["layoutParams"]))
          setScreenJson(screenDfnDic)
          setScreenPlugin(screenPlugin)

          // get help url & params
          var hUrl = screenDfn_0["helpUrl"]
          if (hUrl.indexOf("?") > 0) {
            setHelpUrl(hUrl.substring(0, hUrl.indexOf("?")))
            if (hUrl.indexOf("&") > 0) {
              setHelpDocTp(hUrl.substring(hUrl.indexOf("docType=") + 8, hUrl.indexOf("&")))
            } else {
              setHelpDocTp(hUrl.substring(hUrl.indexOf("docType") + 8))
            }
          } else {
            setHelpUrl(hUrl)
          }
        })

      var data = {}
      await HttpPost("/api/" + props.screenID + "/LOAD_SCREEN_DONE" + params, JSON.stringify(data))
        .then((response) => response.json())
        .then((result) => {
          Loading.remove()
        })

      pyiLocalStorage.clearSysMsgs()
    } catch (error) {
      console.log(error)
      Loading.remove()
      pyiLogger.error("Load screen failed: " + error, true)
    }
  }

  // help icon event
  document.getElementById("sysHelp").onclick = async function () {
    // const helpPage = window.open("_black")
    // helpPage.location.href = window.location.origin + helpUrl + (helpDocTp ? "&docType=" + helpDocTp : "")
    var urlSuffix = helpUrl.split("help/")[1].replace("/", "=")
    window.open("/help?" + urlSuffix)
  }

  React.useEffect(() => {
    if (autoRefresh["autoRefreshInterval"] || String(autoRefresh["autoRefreshInterval"]) === "0") {
      const autoRefreshInterval = Number(autoRefresh["autoRefreshInterval"])
      const second = autoRefreshInterval === 0 ? 1 : autoRefreshInterval * 1000

      Loading.show()
      if (!autoRefresh["autoRefreshAction"]) {
        setInterval(function () {
          refreshList()
        }, second)
      }
    }
  }, [autoRefresh]) // page refresh

  const comboBoxOnChange = async (e: any) => {
    let removeLoadingDiv = true
    Loading.show()
    pyiLocalStorage.clearSysMsgs()
    const eventHandler = e.eventHandler.func
    if (!eventHandler) {
      Loading.remove()
      return
    }
    const fieldGroups = e.eventHandler.prams
    let data = {}
    data[e.fgName] = refs[e.fgName].current.formDataToJson()
    try {
      await HttpPost(eventHandler + "?COMBOX_CHANGE_EVENT=true", JSON.stringify(data))
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          if (fieldGroups.length === 0) {
            saveMessage(result.messages)
            refreshList()
            removeLoadingDiv = false
          } else if (validateResponse(result, false)) {
            const fgName = Object.keys(result.data)[0]
            const fgData = result.data[fgName][fgName]
            if (fieldGroups.indexOf(fgName) !== -1) {
              if (fgData) {
                screenJson[fgName].data = fgData
              }

              Object.keys(result.data[fgName]).forEach((key: string) => {
                if (key !== fgName) {
                  screenJson[fgName].fields.forEach((field, index) => {
                    if (field.name === key) {
                      pageRefreshFlag[fgName] += 1
                      screenJson[fgName].fields[index].widgetParameter.data = result.data[fgName][key]
                    }
                  })
                }
              })
              setPageRefreshFlag(JSON.parse(JSON.stringify(pageRefreshFlag)))
            }
          }
        })
    } catch (error) {
      Loading.remove()
      pyiLogger.error(eventHandler + " error: " + error, true)
    } finally {
      if (removeLoadingDiv) {
        Loading.remove()
      }
    }
  }

  const searchBarIconClick = async (e: any) => {
    let removeLoadingDiv = true
    Loading.show()
    pyiLocalStorage.clearSysMsgs()
    const eventHandler = e.eventHandler
    if (!eventHandler) {
      Loading.remove()
      return
    }
    const fieldGroups = e.eventHandlerParameter.fieldGroups
    let data = {}
    data[e.fgName] = refs[e.fgName].current.formDataToJson()

    // SessionStorage only needs to be saved when a search event refreshes the entire page, so that previous search criteria can be displayed in searchFg after the page is refreshed.
    if (fieldGroups.length === 0) {
      sessionStorage.setItem("SEARCH_DATA_" + e.fgName, refs[e.fgName].current.formDataToJson())
    }
    try {
      await HttpPost(eventHandler, JSON.stringify(data))
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          if (fieldGroups.length === 0) {
            saveMessage(result.messages)
            refreshList()
            removeLoadingDiv = false
          } else if (validateResponse(result, false)) {
            fieldGroups.map((fgName) => {
              const fgNames = Object.keys(result.data)
              if (fgNames.indexOf(fgName) !== -1) {
                const fgData = result.data[fgName][pyiGlobal.SCREEN_FIELD_GROUP_DATA]
                const fgDataStyle = result.data[fgName][pyiGlobal.SCREEN_FIELD_GROUP_DATA_STYLE]
                pageRefreshFlag[fgName] += 1
                screenJson[fgName].data = fgData // reset table data'
                screenJson[fgName].style = fgDataStyle // reset table style'
              }
            })
            // Turn the string and then back to the object to change the object to change his memory address, so that you can listen to the dynamic change of pageRefreshFlag
            setPageRefreshFlag(JSON.parse(JSON.stringify(pageRefreshFlag)))
          }
        })
    } catch (error) {
      Loading.remove()
      pyiLogger.error(eventHandler + " error: " + error, true)
    } finally {
      if (removeLoadingDiv) {
        Loading.remove()
      }
    }
  }

  const btnClick = async (e: any) => {
    let removeLoadingDiv = true
    Loading.show()
    pyiLocalStorage.clearSysMsgs()
    const eventHandler = e.eventHandler[0]
    const eventHandlerParameter = e.eventHandler[1].fieldGroups
    // YL, 2022-07-18 NEW encapsulates all pages - start
    const btnType = e.eventHandler[2]["type"] ? e.eventHandler[2]["type"] : "normal"

    try {
      let buttonData = {}
      if (btnType === pyiGlobal.BTN_TYPE_UPLOAD) {
        eventHandlerParameter.forEach((fgName: string) => {
          buttonData = refs[fgName].current.formData()
        })
      } else {
        buttonData = createEventData(eventHandlerParameter)
      }

      if (Object.keys(e.eventHandler[2]).toString().trim().toLowerCase().indexOf("dialog") > -1) {
        // If there is a dialog, show the dialog first.
        const dialogParams = getDialogParams(e.eventHandler[2]["dialog"])
        showDialog(dialogParams, btnType, eventHandler, buttonData)
        removeLoadingDiv = false
      } else {
        // If there is no dialog, the button click event is triggered directly.
        onClickEvent(btnType, eventHandler, buttonData)
        removeLoadingDiv = false
      }
      // YL, 2022-07-18 - end
    } catch (error) {
      showErrorMessage("System error, please ask administrator to check.")
      pyiLogger.error(eventHandler + " error: " + error)
      removeLoadingDiv = true
    } finally {
      if (removeLoadingDiv) {
        Loading.remove() // can't delete
      }
    }
  }

  const domDownload = (fileName, blob, eventHandler) => {
    if (fileName) {
      fileName = fileName.replaceAll("%20", " ")
      const linkNode = document.createElement("a")
      // Set the download attribute of the linkNode to the fileName. This will tell the browser to download the resource pointed to by the link instead of navigating to it.
      linkNode.download = fileName
      linkNode.style.display = "none"
      // Create a new Blob URL that represents the given blob object. Assign this URL to linkNode's href.
      linkNode.href = URL.createObjectURL(blob)
      document.body.appendChild(linkNode)
      // Trigger a click event on linkNode to start the download
      linkNode.click()

      // Revoke the Blob URL after triggering the download, freeing system resources as the blob URL is no longer needed
      URL.revokeObjectURL(linkNode.href)
      document.body.removeChild(linkNode)
    } else {
      pyiLogger.warn("Download - " + eventHandler + " no filename, please ask administrator to check.")
    }
  }

  const onClickEvent = async (btnType, eventHandler, data) => {
    let removeLoadingDiv = true
    Loading.show()
    try {
      if (btnType === pyiGlobal.BTN_TYPE_NORMAL) {
        await HttpPost(eventHandler, JSON.stringify(data)).then((response) => {
          response.blob().then((blob) => {
            try {
              if (blob.type.trim().toLocaleLowerCase() === "application/json") {
                var reader = new FileReader()
                reader.onload = (e) => {
                  let result = JSON.parse(e.target.result as string)
                  if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
                    window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
                  }
                  if (validateResponse(result, false)) {
                    refreshList()
                  }
                }
                reader.readAsText(blob)
              } else if (response.headers.get("Content-Disposition").startsWith("attachment;")) {
                let fileName = response.headers.get("Content-Disposition")?.split("filename=")[1]
                domDownload(fileName, blob, eventHandler)
                refreshList()
                saveMessage([{ type: "info", message: "download success." }])
              } else {
                showErrorMessage("System error, please ask administrator to check: unknown content-type: " + blob.type)
              }
            } finally {
              Loading.remove()
            }
          })
        })
        removeLoadingDiv = false
      } else if (btnType === pyiGlobal.BTN_TYPE_UPLOAD) {
        // upload button event
        await HttpPostNoHeader(eventHandler, data).then((response) => {
          response.blob().then((blob) => {
            try {
              if (blob.type.trim().toLocaleLowerCase() === "application/json") {
                var reader = new FileReader()
                reader.onload = (e) => {
                  let data = JSON.parse(e.target.result as string)
                  if (validateResponse(data, false)) {
                    refreshList()
                  }
                }
                reader.readAsText(blob)
              } else {
                let fileName = response.headers.get("Content-Disposition")?.split("filename=")[1]
                domDownload(fileName, blob, eventHandler)
                refreshList()
                saveMessage([{ type: "info", message: "download success." }])
              }
            } finally {
              Loading.remove()
            }
          })
        })
        removeLoadingDiv = false
      } else if (btnType === pyiGlobal.BTN_TYPE_DOWNLOAD) {
        // download button event
        await HttpDownload(eventHandler, data).then((response) => {
          try {
            let respType = response.headers?.["content-type"]
            if (respType.trim().toLocaleLowerCase() === "application/json") {
              var reader = new FileReader()
              reader.onload = (e) => {
                let resultData = JSON.parse(e.target.result as string)
                if (validateResponse(resultData, false) && data.constructor === Object && Object.keys(data).length > 0) {
                  refreshList()
                }
              }
              reader.readAsText(response.data)
            } else {
              const blob = new Blob([response.data])
              let fileName = response?.headers?.["content-disposition"]?.split("filename=")[1]
              domDownload(fileName, blob, eventHandler)
              if (data.constructor === Object && Object.keys(data).length > 0) {
                saveMessage([{ type: "info", message: "download success." }])
                refreshList()
              } else {
                showInfoMessage("download success.")
              }
            }
          } finally {
            Loading.remove()
          }
        })
        removeLoadingDiv = false
      }
    } catch (error) {
      pyiLogger.error(error)
      removeLoadingDiv = true
    } finally {
      if (removeLoadingDiv) {
        Loading.remove()
      }
    }
  }

  const showDialog = async (dialogParams, btnType, eventHandler, buttonData) => {
    Loading.show()
    try {
      const dialogName = dialogParams["dialogName"]
      const title = dialogParams["dialogTitle"]
      const message = dialogParams["dialogMessage"]
      const eventWithParams = dialogParams["dialogBeforeDisplayEvent"]
      const continueNm = dialogParams["continueNm"] ? dialogParams["continueNm"] : "OK"
      const cancelNm = dialogParams["cancelNm"] ? dialogParams["cancelNm"] : "Cancel"
      const dialogWidth = dialogParams["width"]
      const dialogHeight = dialogParams["height"]
      // YL, 2022-10-08 BUGFIX if no dialog will error - start
      let eventName
      let eventParams
      let beforeDisplayData = {}
      if (eventWithParams) {
        eventName = getDialogEvent(eventWithParams)
        eventParams = getDialogEventParamArr(eventWithParams)
        beforeDisplayData = createEventData(eventParams)
      }

      if (eventName) {
        const dialogEventHandler = getDialogEventHandler(eventName, props.screenID)
        await HttpPost(dialogEventHandler, JSON.stringify(beforeDisplayData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              const dialogTitle = result.data && result.data["title"] ? result.data["title"] : ""
              const dialogMessage = result.data && result.data["dialogMessage"] ? result.data["dialogMessage"] : ""
              const params = {
                dialogTitle: dialogTitle,
                dialogMessage: dialogMessage,
                dialogType: btnType,
                screenID: props.screenID,
                dialogName: dialogName,
                onCancel: () => closeDialog(),
                onContinue: (dialogData) => {
                  if (btnType === pyiGlobal.BTN_TYPE_UPLOAD) {
                    onClickEvent(btnType, eventHandler, getFormData(dialogData, buttonData))
                  } else {
                    onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData })
                  }
                },
                continueNm: continueNm,
                cancelNm: cancelNm,
                dialogWidth: dialogWidth,
                dialogHeight: dialogHeight,
              }
              openDialog(params)
            }
          })
      } else {
        const params = {
          dialogTitle: title,
          dialogMessage: message,
          dialogType: btnType,
          screenID: props.screenID,
          dialogName: dialogName,
          onCancel: () => closeDialog(),
          onContinue: (dialogData) => {
            if (btnType === pyiGlobal.BTN_TYPE_UPLOAD) {
              onClickEvent(btnType, eventHandler, getFormData(dialogData, buttonData))
            } else {
              onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData })
            }
          },
          continueNm: continueNm,
          cancelNm: cancelNm,
          dialogWidth: dialogWidth,
          dialogHeight: dialogHeight,
        }
        openDialog(params)
      }
    } catch (error) {
      pyiLogger.error(error)
      Loading.remove()
    } finally {
      Loading.remove()
    }
  }

  React.useEffect(() => {
    if (Object.keys(screenPlugin).length === 0) {
      return
    }
    pyiLocalStorage.clearSysMsgs()
    let screenPluginLists = {}
    props.fgNames.forEach((fgName: string) => {
      if (
        screenJson[fgName] &&
        (screenJson[fgName].type === pyiGlobal.TABLE_TYPE || screenJson[fgName].type === pyiGlobal.TABLE_TYPE_RESULT) &&
        screenPlugin[fgName] &&
        screenPlugin[fgName].length !== 0
      ) {
        let pluginCallBack = []
        let pluginLists = []
        screenPlugin[fgName].forEach((plugin: any, index: number) => {
          const currentIcon = pyiGlobal.PUBLIC_URL + "images/current_sbutton.gif"
          const expandIcon = pyiGlobal.PUBLIC_URL + "images/expand_sbutton.gif"
          pluginCallBack[index] = async (id: number) => {
            Loading.show()
            try {
              await HttpPost(plugin.eventHandler, JSON.stringify({ EditIndexField: id }))
                .then((response) => response.json())
                .then((result) => {
                  if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
                    window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
                  }
                  if (validateResponse(result, false)) {
                    refreshList()
                  }
                })
            } catch (error) {
              Loading.remove()
              pyiLogger.error(plugin.eventHandler + " error: " + error, true)
            } finally {
              Loading.remove() // can't delete
            }
          }
          const caption = Array.isArray(plugin.caption) ? plugin.caption[0].text : plugin.caption
          pluginLists[index] = createIconColumn(expandIcon, pluginCallBack[index], currentIcon, caption)
        })
        screenPluginLists[fgName] = pluginLists
      }
    })
    setScreenPluginLists(screenPluginLists)
  }, [screenPlugin])

  const mainScreenNode = React.useMemo(() => {
    return (
      <div style={screenLayoutParams.length > 0 ? transform(screenLayoutParams) : null}>
        <>
          {Object.keys(screenJson).length > 0 &&
            props.fgNames.map((fgName: any, index: number) =>
              screenJson[fgName] ? (
                <div style={screenJson[fgName].outerLayoutParams ? transform(parseLayoutParams(screenJson[fgName].outerLayoutParams)) : null}>
                  {pageRefreshFlag[fgName] && String(screenJson[fgName].type) === pyiGlobal.SEARCH_TYPE ? (
                    <SearchFg
                      key={index}
                      ref={refs[fgName]}
                      searchParams={screenJson[fgName]}
                      searchEvent={() =>
                        searchBarIconClick({
                          fgName: fgName,
                          eventHandler: screenJson[fgName].fields[0].eventHandler,
                          eventHandlerParameter: screenJson[fgName].fields[0].eventHandlerParameter,
                        })
                      }
                      onChangeEvent={(eventHandler) => comboBoxOnChange({ fgName, eventHandler })}
                      editable={screenEditable}
                    />
                  ) : null}

                  {pageRefreshFlag[fgName] && String(screenJson[fgName].type).trim() === pyiGlobal.SIMPLE_TYPE ? (
                    <DialogContext.Provider
                      value={{
                        screenID: props.screenID,
                        closeDialog: closeDialog,
                        openDialog: (params) => openDialog(params),
                        createEventData: (params) => createEventData(params),
                      }}
                    >
                      <SimpleFg
                        key={index}
                        ref={refs[fgName]}
                        simpleParams={screenJson[fgName]}
                        onChangeEvent={(eventHandler) => comboBoxOnChange({ fgName, eventHandler })}
                        btnClickEvent={(eventHandler) => btnClick({ fgName, eventHandler })}
                        editable={screenEditable}
                      />
                    </DialogContext.Provider>
                  ) : null}

                  {pageRefreshFlag[fgName] &&
                  (String(screenJson[fgName].type).trim() === pyiGlobal.TABLE_TYPE ||
                    String(screenJson[fgName].type).trim() === pyiGlobal.TABLE_TYPE_RESULT) ? (
                    <DialogContext.Provider
                      value={{
                        screenID: props.screenID,
                        closeDialog: closeDialog,
                        openDialog: (params) => openDialog(params),
                        createEventData: (params) => createEventData(params),
                      }}
                    >
                      <TableFg
                        key={index}
                        ref={refs[fgName]}
                        tableParams={screenJson[fgName]}
                        pluginList={screenPluginLists[fgName]}
                        editable={screenEditable}
                        refresh={() => refreshList()}
                      />
                    </DialogContext.Provider>
                  ) : null}

                  {String(screenJson[fgName].type) === pyiGlobal.ICON_BAR && screenJson[fgName].icons ? (
                    <ToolBar
                      key={index}
                      params={screenJson[fgName]}
                      clickEvent={(eventHandler) => btnClick({ fgName, eventHandler })}
                      editable={screenEditable}
                    />
                  ) : null}

                  {String(screenJson[fgName].type) === pyiGlobal.IFRAME ? <IFrame key={index} params={screenJson[fgName]} /> : null}

                  {String(screenJson[fgName].type) === pyiGlobal.HTML ? <Html key={index} resources={resources} params={screenJson[fgName]} /> : null}

                  {String(screenJson[fgName].type) === pyiGlobal.VIEWER ? (
                    <FileViewer key={index} params={screenJson[fgName]} screenID={props.screenID} />
                  ) : null}

                  {String(screenJson[fgName].type) === pyiGlobal.SITE_PLAN ? (
                    <GetSitePlan key={index} refreshFlag={sitePlanRefreshFlag} params={screenJson[fgName]} screenID={props.screenID} />
                  ) : null}
                </div>
              ) : null
            )}
        </>
      </div>
    )
  }, [
    props.fgNames,
    props.screenID,
    screenLayoutParams,
    screenJson,
    pageRefreshFlag,
    screenEditable,
    screenPluginLists,
    resources,
    sitePlanRefreshFlag,
  ])

  const subScreenNode = React.useMemo(() => {
    return <>{!props.subScreenNm ? <CustomDialog open={dialogOpen} dialogPrams={dialogPrams} /> : null}</>
  }, [dialogOpen, props.subScreenNm])

  return (
    <>
      {mainScreenNode}
      {subScreenNode}
    </>
  )
})

export default Screen

function getPluginParams(screenDfn: any) {
  const fields = screenDfn.fields
  let pluginParams = []
  for (let i = fields.length - 1; i >= 0; i--) {
    if (fields[i].widget.trim().toLowerCase() === "plugin") {
      const field = fields.pop()
      pluginParams.push(field)
    }
  }
  pluginParams.reverse()
  return pluginParams
}

export function addStaticResource(resourcePram: any) {
  const resource = resourcePram.resource
  const properties = resourcePram.properties
  const resourceType = resource.split(/\.|\?/).pop()
  if (resourceType === "js") {
    var js = document.createElement("script")
    js.type = "text/javascript"
    js.src = resource
    if (properties) {
      if (properties.id) {
        js.id = properties.id
      }
      if (properties.title) {
        js.title = properties.title
      }
    }
    document.body.appendChild(js)
  } else if (resourceType === "css") {
    var css = document.createElement("link")
    css.type = "text/css"
    css.rel = "stylesheet"
    css.href = resource
    document.head.appendChild(css)
  }
}

export function parseLayoutParams(layoutParams) {
  let newLayoutParams = []
  if (layoutParams) {
    if (layoutParams.indexOf("{") !== -1) {
      layoutParams = layoutParams.split("{")[1].split("}")[0].trim()
    }
    let params = {}
    layoutParams.split(/,|;/).forEach((param: string) => {
      if (param.indexOf(":") !== -1) {
        let paramName = param.split(":")[0].trim()
        if (paramName.startsWith("'") || paramName.startsWith('"')) {
          paramName = paramName.slice(1, -1)
        }
        let content = param.split(":")[1].trim()
        if (content.startsWith("'") || content.startsWith('"')) {
          content = content.slice(1, -1)
        }
        params[paramName] = content
      }
    })

    if (layoutParams) {
      const properties = Object.keys(params)
      properties.forEach((property) => {
        newLayoutParams.push([property, params[property]])
      })
    }
  }
  return newLayoutParams
}

export function getFormData(data1, data2) {
  const isFormData1 = data1 instanceof FormData
  const isFormData2 = data2 instanceof FormData

  if (isFormData1) {
    return data1
  } else if (isFormData2) {
    return data2
  }
  return null
}
