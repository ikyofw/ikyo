import { createRoot } from "react-dom/client";
import * as React from "react"
import pyiLocalStorage from "../../utils/pyiLocalStorage"
import * as Loading from "../Loading"
import * as Actions from "./actions"
import * as Matrix from "./matrix"
import * as Point from "./point"
import * as Types from "./types"
import useDispatch from "./use-dispatch"
import useSelector from "./use-selector"

import { useContext } from "react"
import { useHttp } from "../../utils/http"
import pyiLogger from "../../utils/log"
import { showErrorMessage, showInfoMessage, validateResponse } from "../../utils/sysUtil"
import { DialogContext } from "../ConText"
import { getDialogEventHandler } from "../Dialog"
import FileViewer from "../FileViewer"
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
  const { screenID, closeDialog, openDialog, createEventData, setShowPdfViewer } = useContext(DialogContext)

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
      iconUrl = JSON.parse(btnIcon)[value] ? pyiGlobal.PUBLIC_URL + JSON.parse(btnIcon)[value] : null
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
  const refreshPrams = props.dialogPrams.eventHandler[dialogIndex].refreshPrams
  const refresh = () => (refreshPrams.includes("false") ? refreshTable(false) : refreshTable(true))

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
      showInfoMessage("Downloaded.")
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
      const dialogType = btnType === pyiGlobal.BTN_TYPE_UPLOAD_DIALOG ? pyiGlobal.DIALOG_TYPE_UPLOAD : pyiGlobal.DIALOG_TYPE_NORMAL

      const multiple = dialog.multiple
      const dialogName = dialog.dialogName
      const dialogTitle = dialog.dialogTitle
      const uploadTip = dialog.uploadTip
      const dialogContent = dialog.dialogContent
      const eventName = dialog.eventName
      const continueName = dialog.continueName
      const cancelName = dialog.cancelName
      const dialogWidth = dialog.dialogWidth
      const dialogHeight = dialog.dialogHeight

      if (eventName) {
        const dialogEventHandler = getDialogEventHandler(eventName, screenID)
        await HttpPost(dialogEventHandler, JSON.stringify(beforeDisplayData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              const dialogTitle = result.data && result.data["title"] ? result.data["title"] : dialog.dialogTitle
              const dialogContent = result.data && result.data["content"] ? result.data["content"] : dialog.dialogContent
              const params = {
                multiple: multiple,
                dialogName: dialogName,
                dialogTitle: dialogTitle,
                uploadTip: uploadTip,
                dialogContent: dialogContent,
                dialogType: dialogType,
                screenID: screenID,
                onCancel: () => closeDialog(),
                onContinue: (dialogData) => {
                  if (btnType === pyiGlobal.BTN_TYPE_UPLOAD_DIALOG || btnType === pyiGlobal.BTN_TYPE_UPLOAD_BUTTON) {
                    onClickEvent(btnType, eventHandler, getFormData(dialogData, buttonData))
                  } else {
                    onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData })
                  }
                },
                continueName: continueName,
                cancelName: cancelName,
                dialogWidth: dialogWidth,
                dialogHeight: dialogHeight,
              }
              openDialog(params)
            }
          })
      } else {
        const params = {
          multiple: multiple,
          dialogName: dialogName,
          dialogTitle: dialogTitle,
          uploadTip: uploadTip,
          dialogContent: dialogContent,
          dialogType: dialogType,
          screenID: screenID,
          onCancel: () => closeDialog(),
          onContinue: (dialogData) => {
            if (btnType === pyiGlobal.BTN_TYPE_UPLOAD_DIALOG || btnType === pyiGlobal.BTN_TYPE_UPLOAD_BUTTON) {
              onClickEvent(btnType, eventHandler, getFormData(dialogData, buttonData))
            } else {
              onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData })
            }
          },
          continueName: continueName,
          cancelName: cancelName,
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
    setShowPdfViewer(false)
    try {
      if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_BTN_TYPE_NORMAL) {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              refresh()
            }
          })
      } else if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_BTN_TYPE_SWITCH) {
        if (String(value)?.trim().toLocaleLowerCase() === "true") {
          setCellData(props.active, { value: "false" }, props.initialData)
        } else if (String(value)?.trim().toLocaleLowerCase() === "false") {
          setCellData(props.active, { value: "true" }, props.initialData)
        }
      } else if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_BTN_TYPE_PDF) {
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

              const root = createRoot(document.getElementById("pdfContainer"));

              root.render(<React.StrictMode>
                <FileViewer params={{ dataUrl: newPdfBlob }} />
              </React.StrictMode>);
            }
          }
        })
      } else if (btnType && btnType === pyiGlobal.TABLE_BTN_TYPE_UPLOAD) {
        // upload button event
        await HttpPostNoHeader(eventHandler, buttonData).then((response) => {
          response.blob().then((blob) => {
            try {
              if (blob.type.trim().toLocaleLowerCase() === "application/json") {
                var reader = new FileReader()
                reader.onload = (e) => {
                  let data = JSON.parse(e.target.result as string)
                  if (validateResponse(data, false)) {
                    refresh()
                  }
                }
                reader.readAsText(blob)
              } else {
                let fileName = response.headers.get("Content-Disposition")?.split("filename=")[1]
                domDownload(fileName, blob, eventHandler)
                refresh()
              }
            } finally {
              Loading.remove()
            }
          })
        })
        removeLoadingDiv = false
      } else if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_BTN_TYPE_DOWNLOAD) {
        HttpDownload(eventHandler, JSON.stringify(buttonData)).then((response) => {
          const blob = new Blob([response.data])
          let fileName = response?.headers?.["content-disposition"]?.split("filename=")[1]
          domDownload(fileName, blob, eventHandler)

          let respType = response.headers?.["content-type"]
          if (respType.trim().toLocaleLowerCase() === "application/json") {
            var reader = new FileReader()
            reader.onload = (e) => {
              let data = JSON.parse(e.target.result as string)
              if (validateResponse(data, false)) {
                refresh()
              }
            }
            reader.readAsText(response.data)
            setShowPdfViewer(true)
          } 
          // else {
          //   const blob = new Blob([response.data])
          //   let fileName = response?.headers?.["content-disposition"]?.split("filename=")[1]
          //   domDownload(fileName, blob, eventHandler)
          // }
        })
      } else {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
              window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
            }
            if (validateResponse(result, false)) {
              refresh()
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
