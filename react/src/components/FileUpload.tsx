import { forwardRef, Ref } from "react"
interface IFileUpload {
  ref: any
  fileBoxLabel: string
  name: string
  editable: boolean
  widgetParameter: any
}
const FileUpload: React.FC<IFileUpload> = forwardRef((props, ref: Ref<any>) => {
  const multiple = props.widgetParameter.multiple
  return (
    <>
      <th className="property_key">{props.fileBoxLabel}</th>
      <td className="property_value">
        <input
          multiple={multiple && multiple === "yes" ? true : false}
          ref={ref}
          type="file"
          name={props.name}
          id={props.name}
          disabled={!props.editable}
        />
      </td>
    </>
  )
})
export default FileUpload
