import { FocusEventHandler, forwardRef, Ref } from "react"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams
const debugIcon = pyiGlobal.PUBLIC_URL + "images/debug_icon.png"
const infoIcon = pyiGlobal.PUBLIC_URL + "images/info_icon.gif"
const warningIcon = pyiGlobal.PUBLIC_URL + "images/warning_icon.gif"
const errorIcon = pyiGlobal.PUBLIC_URL + "images/error_icon.gif"
const fatalIcon = pyiGlobal.PUBLIC_URL + "images/fatal_icon.png"
const exceptionIcon = pyiGlobal.PUBLIC_URL + "images/exception_icon.gif"

interface ISysMsgBox {
  ref: any
  label: string
  value: string
  name: string
  editable: boolean
  onBlur?: FocusEventHandler<HTMLInputElement>
}
const SysMsgBox: React.FC<ISysMsgBox> = forwardRef((props, ref: Ref<any>) => {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
      {props.label.toLowerCase() === "debug" ? (
        <img src={debugIcon} alt="debug icon" title="Debug" />
      ) : props.label.toLowerCase() === "info"  ? (
        <img src={infoIcon} alt="info icon" title="Information" />
      ) : props.label.toLowerCase() === "warning" ? (
        <img src={warningIcon} alt="warning icon" title="Warning" />
      ) : props.label.toLowerCase() === "error" ? (
        <img src={errorIcon} alt="error icon" title="Error" />
      ) : props.label.toLowerCase() === "fatal" ? (
        <img src={fatalIcon} alt="fatal icon" title="Fatal" />
      ) : props.label.toLowerCase() === "exception" ? (
        <img src={exceptionIcon} alt="exception icon" title="Exception" />
      ) : (
        <img src={infoIcon} alt="info icon" title="Information" />
      )}

      <div
        style={{
          backgroundColor: "transparent",
          border: "hidden",
          paddingLeft: "10px",
          paddingRight: "50px",
          width: "97%",
          float: "right",
          fontSize: "2em",
          whiteSpace: "pre-line",
        }}
        ref={ref}
        id={props.name}
        contentEditable={!props.editable}
        onBlur={props.onBlur}
      >
        {props.value}
      </div>
    </div>
  )
})
export default SysMsgBox
