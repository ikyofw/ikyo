import classnames from "classnames"
import transform from "css-to-react-native"
import React, { forwardRef, Ref, useState } from "react"
import * as simpleFg from "./SimpleFg"

interface IPasswordBox {
  ref: any
  label: string
  value: string
  name: string
  editable: boolean
  style?: any
  tip?: string
  widgetParameter?: any
}
const PasswordBox: React.FC<IPasswordBox> = forwardRef((props, ref: Ref<any>) => {
  const [tooltip, setTooltip] = useState(String)

  React.useEffect(() => {
    const inputElement: HTMLInputElement | null = document.getElementById(props.name + "_psw") as HTMLInputElement
    if (inputElement) {
      inputElement.value = props.value ?? ""
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
      setTooltip("")
    }
  }, [props.value, props.tip, props.name])

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style)

  return (
    <>
      <th className="property_key">{props.label}</th>
      <td className={classnames(cellClass, "property_value", "tip_center")}>
        <input
          ref={ref}
          type="password"
          name={props.name}
          id={props.name + "_psw"}
          disabled={!props.editable}
          style={cellStyle.length > 0 ? transform(cellStyle) : null}
          autoComplete="new-password"
        />
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default PasswordBox
