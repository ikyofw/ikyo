import React, { Ref, forwardRef, useState } from "react"
import transform, { StyleTuple } from "css-to-react-native"
import "../../public/static/css/CheckBox.css"
import classnames from "classnames"
import * as simpleFg from "./SimpleFg"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams
const iconFalse = pyiGlobal.PUBLIC_URL + "images/checkbox_false.gif"
const iconTrue = pyiGlobal.PUBLIC_URL + "images/checkbox_true.gif"
const iconNull = pyiGlobal.PUBLIC_URL + "images/checkbox_null.gif"

const CHECKBOX_STATES = {
  True: "true",
  False: "false",
  Null: "null",
}

interface ICheckBox {
  ref: any
  checkBoxLabel?: string
  value?: string | boolean
  name?: string
  editable?: boolean
  style?: any
  tip?: string
  widgetParameter?: any
}

const CheckBox: React.FC<ICheckBox> = forwardRef((props, ref: Ref<any>) => {
  const { checkBoxLabel, value, name, editable, tip, widgetParameter } = props
  const mRef = ref as React.MutableRefObject<any>

  const [checkBoxValue, setCheckBoxValue] = useState<string>("false")
  const [checked, setChecked] = useState(false)
  const [tooltip, setTooltip] = React.useState(String)

  React.useEffect(() => {
    if (String(value).toLocaleLowerCase() === "false") {
      setChecked(false)
      setCheckBoxValue("false")
    } else if (String(value).toLocaleLowerCase() === "n") {
      setChecked(false)
      setCheckBoxValue("N")
    } else if (String(value).toLocaleLowerCase() === "true") {
      setChecked(true)
      setCheckBoxValue("true")
    } else if (String(value).toLocaleLowerCase() === "y") {
      setChecked(true)
      setCheckBoxValue("Y")
    } else {
      setChecked(false)
      setCheckBoxValue("false")
      if (widgetParameter.stateNumber === "3") {
        setCheckBoxValue("null")
        let checkbox = document.getElementById(name) as any
        checkbox.indeterminate = true
      }
    }

    // set tooltip
    if (tip) {
      if (tip.includes("\\r\\n")) {
        setTooltip(tip.replace(/\\r\\n/g, "\r\n"))
      } else if (tip.includes("\\n")) {
        setTooltip(tip.replace(/\\n/g, "\r\n"))
      } else if (tip.includes("\\r")) {
        setTooltip(tip.replace(/\\r/g, "\r\n"))
      } else {
        setTooltip(tip)
      }
    }
  }, [props, value])

  React.useEffect(() => {
    mRef.current.src = getIcon(checkBoxValue)
    mRef.current.focus()
  }, [checkBoxValue])

  const changeValue = () => {
    setCheckBoxValue(getNextState(checkBoxValue.toLocaleLowerCase()))
    setChecked(checked === true ? false : true)
  }

  let { cellStyle, cellClass } = simpleFg.formatCss(props.style)
  const additionalStyles: StyleTuple[] = [
    ["width", "auto"],
    ["height", "auto"],
  ]
  cellStyle = [...additionalStyles, ...cellStyle]

  return (
    <>
      {checkBoxValue ? (
        <>
          {widgetParameter.captionPosition !== "right" ? <th className="property_key">{checkBoxLabel ?? null}</th> : null}
          <td className={classnames(cellClass, "property_value", "tip_center")}>
            <input
              ref={ref}
              id={name}
              type="checkbox"
              value={checkBoxValue}
              disabled={!editable}
              checked={checked}
              onChange={changeValue}
              style={cellStyle.length > 0 ? transform(cellStyle) : null}
            />
            {widgetParameter.captionPosition === "right" ? <th className="property_key_right">{checkBoxLabel ?? null}</th> : null}
            {tooltip ? <span className="tip">{tooltip}</span> : null}
          </td>
        </>
      ) : null}
    </>
  )
})
export default CheckBox

export function getIcon(state: string) {
  if (state === CHECKBOX_STATES.True) {
    return iconTrue
  } else if (state === CHECKBOX_STATES.False) {
    return iconFalse
  } else {
    return iconNull
  }
}

export function getNextState(currentState: string) {
  var nextState
  if (currentState === "true") {
    nextState = "false"
  } else if (currentState === "false") {
    nextState = "true"
  } else if (currentState === "y") {
    nextState = "N"
  } else if (currentState === "n") {
    nextState = "Y"
  } else {
    nextState = "true"
  }
  return nextState
}
