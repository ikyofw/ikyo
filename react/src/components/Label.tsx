import React, { forwardRef, Ref } from "react"
import { formatDate, getDateFormatStr } from "../utils/sysUtil"

interface ILabel {
  ref: any
  labelLabel: string
  labelValue: any
  name: string
  tip?: string
  widgetParameter?: any
}
const Label: React.FC<ILabel> = forwardRef((props, ref: Ref<any>) => {
  const [tooltip, setTooltip] = React.useState(String)
  const [value, setValue] = React.useState(props.labelValue)

  React.useEffect(() => {
    if (props.labelValue || props.labelValue === 0 || props.labelValue === false) {
      if (props.widgetParameter["format"]) {
        let format = getDateFormatStr(props.widgetParameter["format"])
        setValue(formatDate(props.labelValue, format))
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
    }
  }, [props])

  return (
    <>
      <th className="property_key">{props.labelLabel}</th>
      <td className="property_value tip_center">
        <input ref={ref} type="hidden" name={props.name} id={props.name} value={value}></input>
        {value}
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default Label
