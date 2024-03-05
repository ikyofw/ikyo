import React from "react"
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
}

const ImageButton: React.FC<IImageButton> = (props) => {
  const imgUrl = pyiGlobal.PUBLIC_URL + props.widgetParameter["icon"]
  return (
    <>
      {props.isField ? (
        <>
          <th className="property_key">{props.caption}</th>
          <td className="property_value tip_center">
            <a id={props.name}>
              <img
                src={imgUrl}
                alt=""
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
              alt=""
              onClick={props.editable ? props.clickEvent : null}
              style={props.editable ? { cursor: "pointer" } : { cursor: "not-allowed" }}
            />
          </a>
          &nbsp;{props.caption}
          {props.tooltip ? (
              <>
                <img
                  src={img_tip}
                  alt="tooltip img"
                  style={{ paddingLeft: "3px", paddingBottom: "2px" }}
                  data-tooltip-id={props.name}
                  data-tooltip-place="top"
                  data-tooltip-content={props.tooltip}
                ></img>
                <Tooltip id={props.name} />
              </>
            ) : null}
            &nbsp;&nbsp;&nbsp;&nbsp;
        </>
      )}
    </>
  )
}

export default ImageButton
