import React, { forwardRef, Ref } from "react"
import { formatData } from "./tableFg/reducer"
import * as simpleFg from "./SimpleFg"
import classnames from "classnames"

interface ILabel {
  ref: any
  labelLabel: string
  labelValue: any
  name: string
  style?: any
  tip?: string
  widgetParameter?: any
}
const Label: React.FC<ILabel> = forwardRef((props, ref: Ref<any>) => {
  const [tooltip, setTooltip] = React.useState(String)
  const [value, setValue] = React.useState(props.labelValue)
  const [display, setDisplay] = React.useState("")

  React.useEffect(() => {
    const data = props.widgetParameter.data
    if (data) {
      let values = props.widgetParameter.values
      if (values) {
        values = values.replace(/'/g, '"')
        values = JSON.parse(values)
      } else {
        values = { value: "value", display: "display" }
      }
      
      let options = []
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
      
      let changeFlag = false
      options.map((item) => {
        if (String(item['value']) === String(props.labelValue)) {
          changeFlag = true
          setValue(item['value'])
          if (props.widgetParameter["format"]) {
            setDisplay(formatData(item['display'], props.widgetParameter["format"]))
          } else {
            setDisplay(item['display'])
          }
        }
      })
      if (!changeFlag) {
        setValue('')
        setDisplay('')
      }
    } else {
      if (props.widgetParameter["format"]) {
        setValue(formatData(props.labelValue, props.widgetParameter["format"]))
      } else {
        setValue(props.labelValue)
      }
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
    } else {
      setTooltip('')
    }
  }, [props])

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style);

  return (
    <>
      <th className="property_key">{props.labelLabel}</th>
      <td className={classnames(cellClass, "property_value", "tip_center")}>
        <input ref={ref} type="hidden" name={props.name} id={props.name} value={value}></input>
        {display ? display : value}
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default Label
