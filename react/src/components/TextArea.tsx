import transform, { StyleTuple } from "css-to-react-native"
import React, { ChangeEvent, Ref, forwardRef, useEffect, useState } from "react"
import { formatDate, getDateFormatStr } from "../utils/sysUtil"

interface ITextArea {
  ref: any
  textAreaLabel: string
  textAreaValue: string
  name: string
  editable: boolean
  style?: any
  tip?: string
  widgetParameter?: any
}
const TextArea: React.FC<ITextArea> = forwardRef((props, ref: Ref<any>) => {
  const [value, setValue] = useState<string>("")
  const [tooltip, setTooltip] = React.useState(String)

  useEffect(() => {
    if (props.textAreaValue) {
      if (props.widgetParameter["format"]) {
        let format = getDateFormatStr(props.widgetParameter["format"])
        setValue(formatDate(props.textAreaValue, format))
      } else {
        setValue(props.textAreaValue)
      }
    } else {
      setValue("")
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

  const changeTextareaValue = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
  }

  let cellStyle: StyleTuple[] = [
    ["overflow", "auto"],
    ["resize", "vertical"],
  ]
  if (props.style) {
    const properties = Object.keys(props.style)
    properties.forEach((property) => {
      cellStyle.push([property, props.style[property]])
    })
  }

  return (
    <>
      <th className="property_key">{props.textAreaLabel}</th>
      <td className="property_value tip_center">
        <textarea
          rows={5}
          cols={40}
          style={transform(cellStyle)}
          ref={ref}
          name={props.name}
          defaultValue={props.textAreaValue}
          value={value}
          onChange={changeTextareaValue}
          disabled={!props.editable}
        />
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default TextArea
