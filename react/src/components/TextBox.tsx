import transform, { StyleTuple } from "css-to-react-native"
import React, { forwardRef, Ref } from "react"
import * as simpleFg from "./SimpleFg"
import classnames from "classnames"

interface ITextbox {
  ref: any
  textBoxLabel: string
  textBoxValue?: any
  name: string
  editable: boolean
  style?: any
  tip?: string
  widgetParameter?: any
}
const TextBox: React.FC<ITextbox> = forwardRef((props, ref: Ref<any>) => {
  const [value, setValue] = React.useState("")
  const [tooltip, setTooltip] = React.useState(String)

  React.useEffect(() => {
    if (props.textBoxValue || props.textBoxValue === 0 || props.textBoxValue === false) {
      setValue(String(props.textBoxValue))
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
    } else {
      setTooltip('')
    }
  }, [props, props.textBoxValue])

  let { cellStyle, cellClass } = simpleFg.formatCss(props.style)
  const additionalStyles: StyleTuple[] = [
    ["overflow", "auto"],
    ["resize", "vertical"],
  ]
  cellStyle = [...additionalStyles, ...cellStyle]

  const placeholder = props.widgetParameter.placeholder

  return (
    <>
      <th className="property_key">{props.textBoxLabel}</th>
      <td className={classnames(cellClass, "property_value", "tip_center")}>
        <input
          ref={ref}
          type="Textbox"
          name={props.name}
          id={props.name}
          placeholder={placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={!props.editable}
          style={cellStyle.length > 0 ? transform(cellStyle) : null}
        />
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default TextBox
