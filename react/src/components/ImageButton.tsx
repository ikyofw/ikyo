import React from "react"
import ReactDOM from "react-dom"
import classnames from "classnames"
import * as simpleFg from "./SimpleFg"
import { Tooltip } from "react-tooltip"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams
const img_tip = pyiGlobal.PUBLIC_URL + "images/tips_icon.gif"

interface IImageButton {
  isField?: boolean
  caption?: string
  tooltip?: string
  name: string
  widgetParameter: any
  clickEvent: any
  editable: boolean
  style?: any
}

const ImageButton: React.FC<IImageButton> = (props) => {
  const imgUrl = pyiGlobal.PUBLIC_URL + props.widgetParameter["icon"]

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style)
  return (
    <>
      {props.isField ? (
        <>
          <th className="property_key">{props.caption}</th>
          <td className={classnames(cellClass, 'property_value', 'tip_center')}>
            <a id={props.name}>
              <img
                src={imgUrl}
                alt={props.name}
                onClick={props.editable ? props.clickEvent : null}
                style={props.editable ? { cursor: "pointer" } : { cursor: "not-allowed" }}
              />
            </a>
          </td>
        </>
      ) : (
        <>
          <a id={props.name}>
            <img
              src={imgUrl}
              alt={props.name}
              onClick={props.editable ? props.clickEvent : null}
              style={props.editable ? { cursor: "pointer" } : { cursor: "not-allowed", filter: "grayscale(1)" }}
            />
          </a>
          &nbsp;{props.caption}
          {props.tooltip ? (
            <>
              <img
                src={img_tip}
                alt="tooltip img"
                style={{ paddingLeft: "3px", paddingBottom: "2px" }}
                data-tooltip-id={"btt-tooltip_" + props.name}
                data-tooltip-place="top"
                data-tooltip-content={props.tooltip}
              ></img>
              {ReactDOM.createPortal(<Tooltip id={"btt-tooltip_" + props.name} style={{ zIndex: 2000 }} />, document.getElementById("root"))} 
            </>
          ) : null}
          &nbsp;&nbsp;&nbsp;&nbsp;
        </>
      )}
    </>
  )
}

export default ImageButton
