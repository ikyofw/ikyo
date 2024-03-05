import transform, { StyleTuple } from "css-to-react-native"
import React, { ChangeEvent, Ref, forwardRef, useEffect, useState } from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"

interface IComboBox {
  ref: any
  comboBoxLabel: string
  // data?: any
  value?: any
  require: boolean
  name: string
  editable: boolean
  onChangeEvent?: any
  style?: any
  tip?: string
  widgetParameter?: any
}
const ComboBox: React.FC<IComboBox> = forwardRef((props, ref: Ref<any>) => {
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [selectValue, setSelectValue] = useState<string>("")
  const [valueAndDisplay, setValueAndDisplay] = useState([])
  const [tooltip, setTooltip] = React.useState(String)

  useEffect(() => {
    if (props.value || props.value === 0 || props.value === false) {
      setSelectValue(props.value)
    } else {
      setSelectValue("")
    }
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
  }, [props.value, props.tip])

  const data = props.widgetParameter.data
  const onChange = props.widgetParameter.onChange
  useEffect(() => {
    let values = props.widgetParameter.values
    const dataUrl = props.widgetParameter.dataUrl
    if (values) {
      values = values.replace(/'/g, '"')
      values = JSON.parse(values)
    } else {
      values = { value: "value", display: "display" }
    }

    let options = []
    if (data) {
      if (typeof data === "string") {
        options = JSON.parse(data)
      } else if (Array.isArray(data)) {
        if (typeof data[0] !== "object") {
          data.forEach((option) => {
            options.push({ value: String(option), display: String(option) })
          })
        } else {
          if ("value" in data[0] && "display" in data[0]) {
            options = data
          } else {
            data.forEach((option) => {
              options.push({ value: option[values.value], display: option[values.display] })
            })
          }
        }
      }
      setValueAndDisplay(options)
    } else if (dataUrl) {
      HttpPost(dataUrl, JSON.stringify({ useDataUrl: true }))
        .then((response) => response.json())
        .then((result) => {
          if (result.data) {
            result.data.forEach((option) => {
              options.push({ value: option[values.value], display: option[values.display] })
            })
            setValueAndDisplay(options)
          }
        })
    }
  }, [props.widgetParameter, data])

  const changeSelectedValue = (e: ChangeEvent<HTMLSelectElement>) => {
    setSelectValue(e.target.value)

    if (onChange && props.onChangeEvent) {
      let func, prams
      if (onChange.indexOf("(") !== -1) {
        func = onChange.slice(0, onChange.indexOf("("))
        prams = onChange.slice(onChange.indexOf("(") + 1, onChange.indexOf(")")).split(",")
        prams = prams.map((str) => str.trim())
      } else {
        func = onChange
        prams = []
      }
      props.onChangeEvent({ func: func, prams: prams })
    }
  }

  let cellStyle: StyleTuple[] = []
  if (props.style) {
    const properties = Object.keys(props.style)
    properties.forEach((property) => {
      cellStyle.push([property, props.style[property]])
    })
  }

  const comboBoxNode = React.useMemo(
    () => (
      <>
        <th className="property_key">{props.comboBoxLabel}</th>
        <td className="property_value tip_center">
          <select
            ref={ref}
            name={props.name}
            id={props.name}
            value={selectValue ? selectValue : ""}
            onChange={changeSelectedValue}
            disabled={!props.editable}
            style={cellStyle.length > 0 ? transform(cellStyle) : null}
          >
            {!props.require ? <option key="" value=""></option> : null}
            {valueAndDisplay &&
              valueAndDisplay.length > 0 &&
              valueAndDisplay.map((item: any, index) => (
                <option key={index} value={item["value"]} title={String(item["display"]).length < 50 ? null : item["display"]}>
                  {String(item["display"]).length < 50
                    ? String(item["display"]).replace(/\s/g, "\u00a0")
                    : String(item["display"]).slice(0, 50).replace(/\s/g, "\u00a0") + "..."}
                </option>
              ))}
          </select>
          {tooltip ? <span className="tip">{tooltip}</span> : null}
        </td>
      </>
    ),
    [props.comboBoxLabel, props.editable, props.name, props.require, ref, selectValue, cellStyle, valueAndDisplay, tooltip]
  )

  return <>{comboBoxNode}</>
})
export default ComboBox
