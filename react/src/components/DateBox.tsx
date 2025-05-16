import React, { forwardRef, Ref } from "react"
import DatePicker from "./calendar/DatePicker"

interface IDateBox {
  ref: any
  widgetParameter: any
  inputLabel: string
  inputValue?: string
  editable: boolean
  style?: any
  tip?: string
}

const DateBox: React.FC<IDateBox> = forwardRef((props, ref: Ref<any>) => {
  const propsParameter = props.widgetParameter["format"]
  const [tooltip, setTooltip] = React.useState(String)

  React.useEffect(() => {
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
  }, [props.tip])

  const dtFormatFlag = propsParameter
    ? propsParameter.trim().toLocaleLowerCase() === "yyyy-mm-dd"
      ? 1
      : propsParameter.trim().toLocaleLowerCase() === "yyyy-mm-dd hh:mm:ss"
      ? 2
      : 3
    : 1
  return (
    <>
      <th className="property_key">{props.inputLabel}</th>
      <td className="property_value tip_center">
        <DatePicker
          ref={ref}
          calType="input"
          textStr={props.inputValue}
          format={dtFormatFlag}
          editable={props.editable}
          style={props.style}
        ></DatePicker>
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default DateBox
