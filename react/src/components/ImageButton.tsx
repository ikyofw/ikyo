import React from "react"
import pyiLocalStorage from "../utils/pyiLocalStorage"

interface IImageButton {
  isField?: boolean
  caption?: string
  name: string
  widgetParameter: any
  clickEvent: any
  editable: boolean
}

const ImageButton: React.FC<IImageButton> = (props) => {
  const imgUrl = pyiLocalStorage.globalParams.PUBLIC_URL + props.widgetParameter["icon"]
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
          &nbsp;{props.caption}&nbsp;&nbsp;
        </>
      )}
    </>
  )
}

export default ImageButton
