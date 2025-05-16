import React, { forwardRef, Ref } from "react"
import transform from "css-to-react-native"
import classnames from "classnames"
import * as simpleFg from "./SimpleFg"

interface IFileUpload {
  ref: any
  fileBoxLabel: string
  name: string
  editable: boolean
  widgetParameter: any
  style?: any
  tip?: string
}
const FileUpload: React.FC<IFileUpload> = forwardRef((props, ref: Ref<any>) => {
  const [tooltip, setTooltip] = React.useState(String)
  const [fileKey, setFileKey] = React.useState<number>(0)
  const multiple = props.widgetParameter.multiple

  React.useEffect(() => {
    setFileKey((prevKey) => prevKey + 1)

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

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style)

  return (
    <>
      <th className="property_key">{props.fileBoxLabel}</th>
      <td className={classnames(cellClass, "property_value", "tip_center")}>
        <input
          key={fileKey}
          multiple={multiple && String(multiple) === "true" ? true : false}
          ref={ref}
          type="file"
          style={cellStyle.length > 0 ? transform(cellStyle) : null}
          name={props.name}
          id={props.name}
          disabled={!props.editable}
        />
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})
export default FileUpload
