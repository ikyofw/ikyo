/*
 * @Description:
 * @version:
 * @Author: XH
 * @Date: 2023-10-23 10:46:14
 */
import transform, { StyleTuple } from "css-to-react-native"
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
  style?: any
  tip?: string
  widgetParameter?: any
}
const AdvancedSelection: React.FC<IAdvancedSelection> = forwardRef((props, ref: Ref<any>) => {
  const { screenID, closeDialog, openDialog, createEventData } = useContext(DialogContext)

  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [selectValue, setSelectValue] = React.useState<string>("")
  const [tooltip, setTooltip] = React.useState(String)

  React.useEffect(() => {
    setSelectValue(props.labelValue ? props.labelValue : "")
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
        beforeDisplayData[props.name] = selectValue
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

  let cellStyle: StyleTuple[] = []
  if (props.style) {
    const properties = Object.keys(props.style)
    properties.forEach((property) => {
      cellStyle.push([property, props.style[property]])
    })
  }

  return (
    <>
      <th className="property_key">{props.labelLabel}</th>
      <td className="property_value tip_center">
        <input ref={ref} type="hidden" name={props.name} id={props.name} value={selectValue}></input>
        <textarea
          rows={5}
          cols={40}
          style={transform(cellStyle)}
          ref={ref}
          name={props.name}
          defaultValue={selectValue}
          value={selectValue}
          disabled={true}
        />
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
