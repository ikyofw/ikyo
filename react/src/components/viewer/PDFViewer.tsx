import { Viewer, Worker } from "@react-pdf-viewer/core"
import { defaultLayoutPlugin } from "@react-pdf-viewer/default-layout"
import type { ToolbarProps, ToolbarSlot, TransformToolbarSlot } from "@react-pdf-viewer/toolbar"
import { toolbarPlugin } from "@react-pdf-viewer/toolbar"
import * as React from "react"

import "@react-pdf-viewer/core/lib/styles/index.css"
import "@react-pdf-viewer/default-layout/lib/styles/index.css"

interface SwitchScrollModeInFullScreenModeExampleProps {
  fileUrl: string
  isOperate: boolean // download & print
  //px
  disWidth?: Number
  disHeight?: Number
  onClose?: () => void
}

const SwitchScrollModeInFullScreenModeExample: React.FC<SwitchScrollModeInFullScreenModeExampleProps> = ({
  fileUrl,
  isOperate,
  disWidth,
  disHeight,
  onClose,
}) => {
  const toolbarPluginInstance = toolbarPlugin()
  const transformToolbar: TransformToolbarSlot = (slot: ToolbarSlot) => ({
    ...slot,
    Download: () => (isOperate ? <slot.Download></slot.Download> : <></>),
    Print: () => (isOperate ? <slot.Print></slot.Print> : <></>),
  })

  const renderToolbar = (Toolbar: (props: ToolbarProps) => React.ReactElement) => (
    <Toolbar>
      {(slots) => (
        <>
          {renderDefaultToolbar(transformToolbar)(slots)}
          {onClose && (
            <div style={{ marginLeft: "auto", paddingRight: "8px" }}>
              <button
                onClick={onClose}
                title="Close"
                style={{
                  backgroundColor: "transparent",
                  color: "#666",
                  border: "none",
                  fontSize: "18px",
                  cursor: "pointer",
                  padding: "1px 8px",
                }}
              >
                ✖
              </button>
            </div>
          )}
        </>
      )}
    </Toolbar>
  )
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    // sidebarTabs: (defaultTabs) => [], // hidden left toolbar
    renderToolbar,
  })
  const { renderDefaultToolbar } = defaultLayoutPluginInstance.toolbarPluginInstance

  let divWidth = disWidth
  let divHeight = disHeight

  const pdfContainerRef = React.useRef<HTMLDivElement | null>(null)

  return (
    <div
      // className="rpv-core__viewer rpv-core__viewer--dark" // black theme
      className="viewerWrapper"
      ref={pdfContainerRef}
      tabIndex={0} // Make the div focusable so as to capture keyboard events
      style={{
        border: "1px solid rgba(0, 0, 0, 0.3)",
        display: "flex",
        flexDirection: "column",
        height: divHeight ? `${divHeight}px` : "90vh",
        width: divWidth ? `${divWidth}px` : "100%",
      }}
    >
      <Worker workerUrl="/static/js/pdf.worker.min.js">
        <Viewer fileUrl={fileUrl} plugins={[defaultLayoutPluginInstance]} />
      </Worker>
    </div>
  )
}

export default SwitchScrollModeInFullScreenModeExample
