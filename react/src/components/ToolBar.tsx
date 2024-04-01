/*
 * @Description: ToolBar
 * @version:
 * @Author: YL
 * @Date: 2022-03-17 15:43:05
 */
import React from "react"
import ImageButton from "./ImageButton"

interface IToolBar {
  params: any
  clickEvent: any
  editable: boolean
}

const ToolBar: React.FC<IToolBar> = (props) => {
  const name = props.params.name
  const btnArr = props.params.icons
  const editable = props.editable && props.params.editable

  return (
    <div id={name} className="bar_layout">
      {btnArr
        ? btnArr.map((imgBtn: any, index: number) => (
            <ImageButton
              key={index}
              caption={imgBtn.caption}
              tooltip={imgBtn.tooltip}
              name={imgBtn.name}
              widgetParameter={imgBtn.widgetParameter}
              clickEvent={() => props.clickEvent([imgBtn.eventHandler, imgBtn.eventHandlerParameter, imgBtn.widgetParameter])}
              editable={editable && imgBtn.enable}
            />
          ))
        : null}
    </div>
  )
}
export default React.memo(ToolBar)
