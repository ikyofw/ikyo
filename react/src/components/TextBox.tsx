import transform, {StyleTuple} from "css-to-react-native"
import React, { forwardRef, Ref } from "react"

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
    }
  }, [props, props.textBoxValue])

  let cellStyle: StyleTuple[] = []
  if (props.style) {
    const properties = Object.keys(props.style)
    properties.forEach((property) => {
      cellStyle.push([property, props.style[property]])
    })
  }

  return (
    <>
      <th className="property_key">{props.textBoxLabel}</th>
      <td className="property_value tip_center">
        <input
          ref={ref}
          type="Textbox"
          name={props.name}
          id={props.name}
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
