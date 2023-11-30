import * as React from "react"
import ReactDOM from "react-dom"
import pyiLocalStorage from "../../utils/pyiLocalStorage"
import * as Loading from "../Loading"
import * as Actions from "./actions"
import * as Matrix from "./matrix"
import * as Point from "./point"
import * as Types from "./types"
import useDispatch from "./use-dispatch"
import useSelector from "./use-selector"

import { useHttp } from "../../utils/http"
import pyiLogger from "../../utils/log"
import { showErrorMessage, validateResponse, showInfoMessage } from "../../utils/sysUtil"
import { useContext } from "react"
import { DialogContext } from "../ConText"
import FileViewer from "../FileViewer"
import { getDialogEventHandler } from "../Dialog"
import { getFormData } from "../Screen"

const pyiGlobal = pyiLocalStorage.globalParams

interface IButton {
  value: any
  dialogPrams: any
  buttonBoxPrams: any
  bttIndex: number
  dialogIndex: number
  active: Point.Point
  initialData: any[]
}

const Button: React.FC<IButton> = (props) => {
  const { screenID, closeDialog, openDialog, createEventData } = useContext(DialogContext)

  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)
  const HttpDownload = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD)
  const HttpPostNoHeader = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST_NO_HEADER)

  const value = props.value
  const bttIndex = props.bttIndex
  const dialogIndex = props.dialogIndex
  const btnIcon = props.buttonBoxPrams.btnIcon[bttIndex]

  let iconUrl = ""
  if (btnIcon && btnIcon.length > 0) {
    if (btnIcon[0] === "{") {
      iconUrl = pyiGlobal.PUBLIC_URL + JSON.parse(btnIcon)[value]
    } else if (btnIcon[0] === "_") {
      if (value.length > 0) {
        iconUrl = pyiGlobal.PUBLIC_URL + btnIcon.slice(1)
      }
    } else {
      iconUrl = pyiGlobal.PUBLIC_URL + btnIcon
    }
  }

  const tableData = useSelector((state) => state.data)

  const dispatch = useDispatch()
  const setCellData = React.useCallback(
    (active: Point.Point, data: Types.CellBase, initialData?: any[], isMultiSelectBox?: boolean) =>
      dispatch(Actions.setCellData(active, data, initialData, isMultiSelectBox)),
    [dispatch]
  )
  const refreshTable = React.useCallback((refreshFlag: boolean) => dispatch(Actions.refreshTable(refreshFlag)), [dispatch])

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
      showInfoMessage("download success.")
    } else {
      pyiLogger.warn("Download - " + eventHandler + " no filename, please ask administrator to check.")
    }
  }

  const buttonClick = async () => {
    let removeLoadingDiv = true
    Loading.show()
    const btnType = props.buttonBoxPrams.type[dialogIndex]
    const dialog = props.dialogPrams.dialog[dialogIndex]

    const eventHandler = props.dialogPrams.eventHandler[dialogIndex].url
    const fieldGroups = props.dialogPrams.eventHandler[dialogIndex].fieldGroups
    const fields = props.dialogPrams.eventHandler[dialogIndex].fields
    try {
      const buttonData = {
        id: Matrix.get({ row: props.active.row, column: 0 }, tableData)?.value,
        row: handleData(tableData[props.active.row], fields),
        ...createEventData(fieldGroups),
      }

      if (dialog) {
        const beforeDisplayData = {
          id: Matrix.get({ row: props.active.row, column: 0 }, tableData)["value"],
          row: handleData(tableData[props.active.row], fields),
        }
        dialog.dialogGroups.forEach((dialog) => {
          const value = Matrix.get({ row: props.active.row, column: dialog[1] }, tableData)["value"]
          beforeDisplayData[dialog[0]] = value
        })
        // If there is a dialog, show the dialog first.
        showDialog(dialog, beforeDisplayData, btnType, eventHandler, buttonData)
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

  const showDialog = async (dialog, beforeDisplayData, btnType, eventHandler, buttonData) => {
    try {
      const dialogName = dialog.dialogName
      const title = dialog.title
      const message = dialog.message
      const eventName = dialog.eventName
      const continueNm = dialog.continueNm
      const cancelNm = dialog.cancelNm
      const dialogWidth = dialog.dialogWidth
      const dialogHeight = dialog.dialogHeight

      if (eventName) {
        const dialogEventHandler = getDialogEventHandler(eventName, screenID)
        await HttpPost(dialogEventHandler, JSON.stringify(beforeDisplayData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              sessionStorage.setItem(pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME, JSON.stringify(result.data))
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              const dialogTitle = result.data && result.data["title"] ? result.data["title"] : ""
              const dialogMessage = result.data && result.data["dialogMessage"] ? result.data["dialogMessage"] : ""
              const params = {
                dialogTitle: dialogTitle,
                dialogMessage: dialogMessage,
                dialogType: btnType,
                screenID: screenID,
                dialogName: dialogName,
                onCancel: () => closeDialog(),
                onContinue: (dialogData) => {
                  if (btnType === pyiGlobal.UPLOAD_BTN_TYPE) {
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
          screenID: screenID,
          dialogName: dialogName,
          onCancel: () => closeDialog(),
          onContinue: (dialogData) => {
            if (btnType === pyiGlobal.UPLOAD_BTN_TYPE) {
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
      pyiLogger.error(error) // YL, 2023-02-09 bugfix
      Loading.remove()
    } finally {
      Loading.remove()
    }
  }

  const onClickEvent = async (btnType, eventHandler, buttonData) => {
    let removeLoadingDiv = true
    Loading.show()
    console.log(btnType)

    try {
      if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_NORMAL_BTN_TYPE) {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              sessionStorage.setItem(pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME, JSON.stringify(result.data))
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              refreshTable(true)
            }
          })
      } else if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_SWITCH_BTN_TYPE) {
        if (String(value)?.trim().toLocaleLowerCase() === "true") {
          setCellData(props.active, { value: "false" }, props.initialData)
        } else if (String(value)?.trim().toLocaleLowerCase() === "false") {
          setCellData(props.active, { value: "true" }, props.initialData)
        }
      } else if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_PDF_BTN_TYPE) {
        HttpDownload(eventHandler, JSON.stringify(buttonData)).then((response) => {
          let respType = response.headers?.["content-type"]
          var reader = new FileReader()
          if (respType.trim().toLocaleLowerCase() === "application/json") {
            reader.onload = (e) => {
              let data = JSON.parse(e.target.result as string)
              validateResponse(data, false)
            }
            reader.readAsText(response.data)
          } else {
            const blob = new Blob([response.data])
            reader.readAsDataURL(blob)
            reader.onload = (e) => {
              let base64: string = e.target.result.toString() // data:application/octet-stream;base64, XXX
              base64 = base64.split(",")[1]
              let fileType = respType.split("/")[1]
              let newPdfBlob = "data:" + (fileType === "pdf" ? "application" : "image") + "/" + fileType + ";base64," + base64

              ReactDOM.render(
                <React.StrictMode>
                  <FileViewer params={{ dataUrl: newPdfBlob }} />
                </React.StrictMode>,
                document.getElementById("pdfContainer")
              )
            }
          }
        })
      } else if (btnType && btnType === pyiGlobal.TABLE_UPLOAD_BTN_TYPE) {
        // upload button event
        await HttpPostNoHeader(eventHandler, buttonData).then((response) => {
          response.blob().then((blob) => {
            try {
              if (blob.type.trim().toLocaleLowerCase() === "application/json") {
                var reader = new FileReader()
                reader.onload = (e) => {
                  let data = JSON.parse(e.target.result as string)
                  if (validateResponse(data, false)) {
                    refreshTable(true)
                  }
                }
                reader.readAsText(blob)
              } else {
                let fileName = response.headers.get("Content-Disposition")?.split("filename=")[1]
                domDownload(fileName, blob, eventHandler)
                refreshTable(true)
              }
            } finally {
              Loading.remove()
            }
          })
        })
        removeLoadingDiv = false
      } else if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_DOWNLOAD_BTN_TYPE) {
        HttpDownload(eventHandler, JSON.stringify(buttonData)).then((response) => {
          let respType = response.headers?.["content-type"]
          if (respType.trim().toLocaleLowerCase() === "application/json") {
            var reader = new FileReader()
            reader.onload = (e) => {
              let data = JSON.parse(e.target.result as string)
              if (validateResponse(data, false)) {
                refreshTable(true)
              }
            }
            reader.readAsText(response.data)
          } else {
            const blob = new Blob([response.data])
            let fileName = response?.headers?.["content-disposition"]?.split("filename=")[1]
            domDownload(fileName, blob, eventHandler)
          }
        })
      } else {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              sessionStorage.setItem(pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME, JSON.stringify(result.data))
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              refreshTable(true)
            }
          })
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

  if (iconUrl) {
    return <img alt="" onClick={buttonClick} src={iconUrl} className="Spreadsheet__data-viewer" />
  } else {
    return null
  }
}

export default Button

export const handleData = (rowData: Types.CellBase<any>[], fields: string[]): any => {
  let data = {}
  fields &&
    fields.map((field: string, index: number) => {
      if (field === "__KEY_") {
        data["id"] = rowData[index]["value"]
      } else {
        data[field] = rowData[index]["value"]
      }
    })
  return data
}
