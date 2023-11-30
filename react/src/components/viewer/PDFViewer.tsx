import { Viewer, Worker } from "@react-pdf-viewer/core"
import { defaultLayoutPlugin } from "@react-pdf-viewer/default-layout"
import type { ToolbarProps, ToolbarSlot, TransformToolbarSlot } from "@react-pdf-viewer/toolbar"
import { toolbarPlugin } from "@react-pdf-viewer/toolbar"
import * as React from "react"

import "@react-pdf-viewer/core/lib/styles/index.css"
import "@react-pdf-viewer/default-layout/lib/styles/index.css"

interface SwitchScrollModeInFullScreenModeExampleProps {
  fileUrl: string
  isOperate?: boolean // download & print
  //px
  disWidth?: Number
  disHeight?: Number
}

const SwitchScrollModeInFullScreenModeExample: React.FC<SwitchScrollModeInFullScreenModeExampleProps> = ({
  fileUrl,
  isOperate,
  disWidth,
  disHeight,
}) => {
  const toolbarPluginInstance = toolbarPlugin()
  const transform: TransformToolbarSlot = (slot: ToolbarSlot) => ({
    ...slot,
    Download: () => (isOperate ? <slot.Download></slot.Download> : <></>),
    Print: () => (isOperate ? <slot.Print></slot.Print> : <></>),
  })

  const renderToolbar = (Toolbar: (props: ToolbarProps) => React.ReactElement) => <Toolbar>{renderDefaultToolbar(transform)}</Toolbar>
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    renderToolbar,
  })
  const { renderDefaultToolbar } = defaultLayoutPluginInstance.toolbarPluginInstance

  // const defaultLayoutPluginInstance = defaultLayoutPlugin({
  //   toolbarPlugin: {
  //     fullScreenPlugin: {
  //       onEnterFullScreen: (zoom) => {
  //         zoom(SpecialZoomLevel.PageFit)
  //         defaultLayoutPluginInstance.toolbarPluginInstance.scrollModePluginInstance.switchScrollMode(ScrollMode.Wrapped)
  //       },
  //       onExitFullScreen: (zoom) => {
  //         zoom(SpecialZoomLevel.PageWidth)
  //         defaultLayoutPluginInstance.toolbarPluginInstance.scrollModePluginInstance.switchScrollMode(ScrollMode.Vertical)
  //       },
  //     },
  //   },
  // })

  let divWidth = disWidth
  let divHeight = disHeight
  return (
    <div
      style={{
        border: "1px solid rgba(0, 0, 0, 0.3)",
        display: "flex",
        flexDirection: "column",
        // height: '100%',
        height: divHeight ? String(divHeight).concat("px") : "90vh",
        // width:'100%',
        width: divWidth ? String(divWidth).concat("px") : "100%",
      }}
    >
      <Worker workerUrl="/static/js/pdf.worker.min.js">
        <Viewer fileUrl={fileUrl} plugins={[defaultLayoutPluginInstance]} />
      </Worker>
    </div>
  )
}

export default SwitchScrollModeInFullScreenModeExample
