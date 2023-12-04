import * as React from "react"
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
import { validateResponse } from "../../utils/sysUtil"
import { useContext } from "react"
import { DialogContext } from "../../components/ConText"
import { getDialogEventHandler } from "../../components/Dialog"

const pyiGlobal = pyiLocalStorage.globalParams

interface IAdvancedSelection {
  cell: any
  dialogPrams: any
  advancedSelectionBoxPrams: any
  selectIndex: number
  dialogIndex: number
  active: Point.Point
  initialData: any[]
}

const AdvancedSelection: React.FC<IAdvancedSelection> = (props) => {
  const { screenID, closeDialog, openDialog, createEventData } = useContext(DialogContext)

  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const value = props.cell ? props.cell.value : ""
  const display = props.cell ? props.cell.display : ""
  const selectIndex = props.selectIndex
  const dialogIndex = props.dialogIndex
  const btnIcon = props.advancedSelectionBoxPrams.btnIcon[selectIndex]

  let iconUrl = ""
  if (btnIcon && btnIcon.length > 0) {
    iconUrl = pyiGlobal.PUBLIC_URL + btnIcon
  }
  const tableData = useSelector((state) => state.data)
  const editable = useSelector((state) => state.editable)
  const [valueAndDisplay, setValueAndDisplay] = React.useState({ value: "", display: "" })

  React.useEffect(() => {
    let valueAndDisplay = { value: value, display: value }
    if (display) {
      valueAndDisplay = { value: value, display: display }
    } else {
      let comboData = props.advancedSelectionBoxPrams.comboData[selectIndex]
      if (comboData && comboData.length > 0) {
        let values = value.split(",").map((s) => s.trim())
        let matchingItems = comboData.filter((item) => values.includes(item["value"]))
        let displays = matchingItems.map((item) => item["display"]).join(", ")
        valueAndDisplay = { value: value, display: displays }
      }
    }
    setValueAndDisplay(valueAndDisplay)
  }, [value]) // just set the init value

  const dispatch = useDispatch()
  const setCellData = React.useCallback(
    (active: Point.Point, data: Types.CellBase, initialData?: any[], isMultiSelectBox?: boolean) =>
      dispatch(Actions.setCellData(active, data, initialData, isMultiSelectBox)),
    [dispatch]
  )
  const updateCellValue = (valueAndDisplay: any) => {
    setValueAndDisplay(valueAndDisplay)
    setCellData(props.active, valueAndDisplay, props.initialData, true)
  }

  const buttonClick = async () => {
    Loading.show()
    try {
      const dialog = props.dialogPrams.dialog[dialogIndex]
      const btnType = "normal"
      const dialogName = dialog.dialogName
      const title = dialog.title
      const message = dialog.message
      const eventName = dialog.eventName
      const continueNm = dialog.continueNm
      const cancelNm = dialog.cancelNm
      const dialogWidth = dialog.dialogWidth
      const dialogHeight = dialog.dialogHeight

      const eventHandler = props.dialogPrams.eventHandler[dialogIndex].url
      const fieldGroups = props.dialogPrams.eventHandler[dialogIndex].fieldGroups
      const fields = props.dialogPrams.eventHandler[dialogIndex].fields

      const buttonData = {
        id: Matrix.get({ row: props.active.row, column: 0 }, tableData)?.value,
        row: handleData(tableData[props.active.row], fields),
        ...createEventData(fieldGroups),
      }

      if (eventName) {
        const beforeDisplayData = {
          id: Matrix.get({ row: props.active.row, column: 0 }, tableData)["value"],
          row: handleData(tableData[props.active.row], fields),
        }
        dialog.dialogGroups.forEach((dialog) => {
          const value = Matrix.get({ row: props.active.row, column: dialog[1] }, tableData)["value"]
          beforeDisplayData[dialog[0]] = value
        })
        const dialogEventHandler = getDialogEventHandler(eventName, screenID)
        await HttpPost(dialogEventHandler, JSON.stringify(beforeDisplayData))
          .then((response) => response.json())
          .then((result) => {
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
                onContinue: (dialogData) => onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData }),
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
          onContinue: (dialogData) => onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData }),
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
      if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_NORMAL_BTN_TYPE) {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (validateResponse(result, false)) {
              const newValue = result.data["value"]
              let newDisplay = result.data["display"]
              if (newValue || newValue === '' || newValue === false) {
                if (!newDisplay && newValue !== '' && newValue !== false) {
                  newDisplay = newValue
                }
                updateCellValue({ value: newValue, display: newDisplay })
              }
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
    return (
      <span style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ flexGrow: 1 }}>{valueAndDisplay["display"]}</span>
        {editable ? <img alt="" onClick={buttonClick} src={iconUrl} className="Spreadsheet__data-viewer" /> : null}
      </span>
    )
  } else {
    return null
  }
}

export default AdvancedSelection

export const handleData = (rowData: Types.CellBase<any>[], fields: string[]): any => {
  let data = {}
  fields &&
    fields.map((field: string, index: number) => {
      if (field === "__KEY_") {
        data["id"] = rowData[index]?.value 
      } else {
        const value = rowData[index]?.comboKey !== undefined ? rowData[index]?.comboKey : rowData[index]?.value ? rowData[index]?.value : null
        data[field] = value
      }
    })
  return data
}
