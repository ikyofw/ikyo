/*
 * @Description:
 * @version:
 * @Author: XH
 * @Date: 2023-10-23 10:46:14
 */
import React, { forwardRef, Ref } from "react"
import * as Loading from "./Loading"
import ImageButton from "./ImageButton"
import { useContext } from "react"
import { DialogContext } from "./ConText"

import { useHttp } from "../utils/http"
import { validateResponse } from "../utils/sysUtil"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import pyiLogger from "../utils/log"

import { getDialogEvent, getDialogEventParamArr, getDialogEventHandler, getDialogParams } from "./Dialog"

const pyiGlobal = pyiLocalStorage.globalParams

interface IAdvancedSelection {
  ref: any
  labelLabel: string
  labelValue: any
  name: string
  editable: boolean
  clickPrams: any
  tip?: string
  widgetParameter?: any
}
const AdvancedSelection: React.FC<IAdvancedSelection> = forwardRef((props, ref: Ref<any>) => {
  const { screenID, closeDialog, openDialog, createEventData } = useContext(DialogContext)

  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [selectValue, setSelectValue] = React.useState<string>("")
  const [valueAndDisplay, setValueAndDisplay] = React.useState([])
  const [tooltip, setTooltip] = React.useState(String)

  React.useEffect(() => {
    setSelectValue(props.labelValue)
    // set tooltip
    if (props.tip) {
      if (props.tip.includes("\\r\\n")) {
        setTooltip(props.tip.replace(/\\r\\n/g, "\r\n"))
      } else if (props.tip.includes("\\n")) {
        setTooltip(props.tip.replace(/\\n/g, "\r\n"))
      } else if (props.tip.includes("\\r")) {
        setTooltip(props.tip.replace(/\\r/g, "\r\n"))
      } else {
        setTooltip(props.tip)
      }
    }
  }, [props, props.labelValue, props.tip])

  React.useEffect(() => {
    const data = props.widgetParameter.data
    let values = props.widgetParameter.values
    const dataUrl = props.widgetParameter.dataUrl
    if (values) {
      values = values.replace(/'/g, '"')
      values = JSON.parse(values)
    } else {
      values = { value: "value", display: "display" }
    }
    if (data) {
      if (typeof data === "string") {
        setValueAndDisplay(JSON.parse(data))
      } else if (Array.isArray(data)) {
        if (typeof data[0] !== "object") {
          let options = []
          data.forEach((option) => {
            options.push({ value: String(option), display: String(option) })
          })
          setValueAndDisplay(options)
        } else {
          if ("value" in data[0] && "display" in data[0]) {
            setValueAndDisplay(data)
          } else {
            let options = []
            data.forEach((option) => {
              options.push({ value: option[values.value], display: option[values.display] })
            })
            setValueAndDisplay(options)
          }
        }
      }
    } else if (dataUrl) {
      HttpPost(dataUrl, JSON.stringify({ useDataUrl: true }))
        .then((response) => response.json())
        .then((result) => {
          if (result.data) {
            let options = []
            result.data.forEach((option) => {
              options.push({ value: option[values.value], display: option[values.display] })
            })
            setValueAndDisplay(options)
          }
        })
    }
  }, [props.widgetParameter])

  const buttonClick = async () => {
    Loading.show()
    try {
      const btnType = "normal"
      const dialogParams = getDialogParams(props.widgetParameter.dialog)
      const dialogName = dialogParams["dialogName"]
      const title = dialogParams["dialogTitle"]
      const message = dialogParams["dialogMessage"]
      const eventWithParams = dialogParams["dialogBeforeDisplayEvent"]
      const continueNm = dialogParams["continueNm"] ? dialogParams["continueNm"] : "OK"
      const cancelNm = dialogParams["cancelNm"] ? dialogParams["cancelNm"] : "Cancel"
      const dialogWidth = dialogParams["width"]
      const dialogHeight = dialogParams["height"]

      let eventName
      let eventParams
      let beforeDisplayData = {}
      if (eventWithParams) {
        eventName = getDialogEvent(eventWithParams)
        eventParams = getDialogEventParamArr(eventWithParams)
        beforeDisplayData = createEventData(eventParams)
      }
      let buttonData = createEventData(props.clickPrams[1].fieldGroups)

      if (eventName) {
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
                onContinue: (dialogData) => onClickEvent(btnType, {...buttonData, ...dialogData}),
                continueNm: continueNm,
                cancelNm: cancelNm,
                dialogWidth: dialogWidth,
                dialogHeight: dialogHeight
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
          onContinue: (dialogData) => onClickEvent(btnType, {...buttonData, ...dialogData}),
          continueNm: continueNm,
          cancelNm: cancelNm,
          dialogWidth: dialogWidth,
          dialogHeight: dialogHeight
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

  const onClickEvent = async (btnType, buttonData) => {
    let removeLoadingDiv = true
    Loading.show()
    try {
      const eventHandler = props.clickPrams[0]
      if (btnType && btnType.toLocaleLowerCase() === pyiGlobal.TABLE_NORMAL_BTN_TYPE) {
        await HttpPost(eventHandler, JSON.stringify(buttonData))
          .then((response) => response.json())
          .then((result) => {
            if (validateResponse(result, false)) {
              const newValue = result.data["value"]
              setSelectValue(newValue)
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
    <>
      <th className="property_key">{props.labelLabel}</th>
      <td className="property_value tip_center">
        <input ref={ref} type="hidden" name={props.name} id={props.name} value={selectValue}></input>
        {valueAndDisplay &&
          valueAndDisplay.length > 0 &&
          valueAndDisplay.map((item: any) => (item["value"] === selectValue ? item["display"] : null))}
        {tooltip ? <span className="tip">{tooltip}</span> : null}
        &nbsp;&nbsp;
        <ImageButton
          key={1}
          caption={""}
          name={props.name}
          widgetParameter={props.widgetParameter}
          clickEvent={() => buttonClick()}
          editable={props.editable}
        />
      </td>
    </>
  )
})

export default AdvancedSelection
