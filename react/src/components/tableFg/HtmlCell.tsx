import * as React from "react"
import pyiLocalStorage from "../../utils/pyiLocalStorage"
import * as Loading from "../Loading"
import * as Actions from "./actions"
import * as Matrix from "./matrix"
import * as Point from "./point"
import * as Types from "./types"
import useDispatch from "./use-dispatch"
import useSelector from "./use-selector"

import parse from "html-react-parser"
import { useContext } from "react"
import { useHttp } from "../../utils/http"
import pyiLogger from "../../utils/log"
import { showErrorMessage, validateResponse } from "../../utils/sysUtil"
import { DialogContext } from "../ConText"
import { getDialogEventHandler } from "../Dialog"

const pyiGlobal = pyiLocalStorage.globalParams

interface IButton {
  value: any
  dialogPrams: any
  dialogIndex: number
  active: Point.Point
  initialData: any[]
}

const Button: React.FC<IButton> = (props) => {
  const { screenID, closeDialog, openDialog, createEventData } = useContext(DialogContext)

  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const value = props.value
  const dialogIndex = props.dialogIndex

  const tableData = useSelector((state) => state.data)

  const dispatch = useDispatch()
  const refreshTable = React.useCallback((refreshFlag: boolean) => dispatch(Actions.refreshTable(refreshFlag)), [dispatch])

  const buttonClick = async () => {
    let removeLoadingDiv = true
    Loading.show()
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
      const btnType = "normal"

      if (dialog) {
        // If there is a dialog, show the dialog first.
        const beforeDisplayData = {
          id: Matrix.get({ row: props.active.row, column: 0 }, tableData)["value"],
          row: handleData(tableData[props.active.row], fields),
        }
        dialog.dialogGroups.forEach((dialog) => {
          const value = Matrix.get({ row: props.active.row, column: dialog[1] }, tableData)["value"]
          beforeDisplayData[dialog[0]] = value
        })
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
                  if (btnType === pyiGlobal.BTN_TYPE_UPLOAD) {
                    onClickEvent(btnType, eventHandler, dialogData)
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
            if (btnType === pyiGlobal.BTN_TYPE_UPLOAD) {
              onClickEvent(btnType, eventHandler, dialogData)
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
    try {
      if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_BTN_TYPE_NORMAL && eventHandler) {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
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

  return (
    <span className="Spreadsheet__data-viewer" onClick={buttonClick}>
      {typeof value == "string" ? parse(value) : value}
    </span>
  )
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
