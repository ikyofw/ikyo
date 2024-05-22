import transform, { StyleTuple } from "css-to-react-native"
import React, { ChangeEvent, Ref, forwardRef, useEffect, useState } from "react"
import classnames from "classnames"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"

interface IListBox {
  ref: any
  listBoxLabel: string
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
const ListBox: React.FC<IListBox> = forwardRef((props, ref: Ref<any>) => {
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [selectValues, setSelectValues] = useState([])
  const [valueAndDisplay, setValueAndDisplay] = useState([])
  const [tooltip, setTooltip] = React.useState(String)

  useEffect(() => {
    if (props.value) {
      setSelectValues(props.value.split(","))
    } else {
      setSelectValues([])
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
  }, [props.widgetParameter, data])

  const changeSelectedValue = (e: ChangeEvent<HTMLSelectElement>) => {
    const selected = Array.from(e.target.options)
      .filter((option) => option.selected)
      .map((option) => option.value)
    setSelectValues(selected)

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
  let cellClass = []
  if (props.style) {
    const properties = Object.keys(props.style)
    properties.forEach((property) => {
      if (property.toLocaleLowerCase() === "class") {
        cellClass = props.style[property].split(",").map((str) => str.trim())
      } else {
        cellStyle.push([property, props.style[property]])
      }
    })
  }
  
  const IListBoxNode = React.useMemo(
    () => (
      <>
        <th className="property_key">{props.listBoxLabel}</th>
        <td className={classnames(cellClass, "property_value")}>
          <select
            multiple
            size={4}
            ref={ref}
            name={props.name}
            id={props.name}
            disabled={!props.editable}
            value={selectValues}
            onChange={changeSelectedValue}
            style={cellStyle.length > 0 ? transform(cellStyle) : null}
            className="select"
          >
            {!props.require ? <option key="" value=""></option> : null}
            {valueAndDisplay &&
              valueAndDisplay.length > 0 &&
              valueAndDisplay.map((item: any, index) => (
                <option key={index} value={String(item["value"])} title={String(item["display"]).length < 50 ? null : item["display"]}>
                  {String(item["display"]).length < 50 ? item["display"] : String(item["display"]).slice(0, 50) + "..."}
                </option>
              ))}
          </select>
          {tooltip ? <span className="tip">{tooltip}</span> : null}
        </td>
      </>
    ),
    [props.listBoxLabel, props.editable, props.name, props.require, ref, selectValues, cellStyle, valueAndDisplay, tooltip]
  )

  return <>{IListBoxNode}</>
})
export default ListBox
