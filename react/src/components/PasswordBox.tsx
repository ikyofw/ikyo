/*
 * @Description:
 * @version:
 * @Author: XH
 * @Date: 2023-09-15 16:07:12
 */

import React, { forwardRef, Ref, useState } from "react"
import transform, { StyleTuple } from "css-to-react-native"

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
    const inputElement: HTMLInputElement | null = document.getElementById(props.name + "_psw") as HTMLInputElement;
    if (props.value && inputElement) {
      inputElement.value = props.value
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
  }, [props.value, props.tip, props.name])

  let cellStyle: StyleTuple[] = []
  if (props.style) {
    const properties = Object.keys(props.style)
    properties.forEach((property) => {
      cellStyle.push([property, props.style[property]])
    })
  }

  return (
    <>
      <th className="property_key">{props.label}</th>
      <td className="property_value tip_center">
        <input
          ref={ref}
          type="password"
          name={props.name}
          id={props.name + "_psw"}
          disabled={!props.editable}
          style={cellStyle.length > 0 ? transform(cellStyle) : null}
        />
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default PasswordBox
