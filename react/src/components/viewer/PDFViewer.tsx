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

  let divWidth = disWidth
  let divHeight = disHeight

  const pdfContainerRef = React.useRef<HTMLDivElement | null>(null)

  // disable mouse right click.
  const handleContextMenu = (event: MouseEvent) => {
    event.preventDefault()
  }

  // disable system hot keys.
  const handleKeyDown = (event: KeyboardEvent) => {
    if (
      event.ctrlKey &&
      (event.key === "p" || event.key === "s" || event.key === "c" || event.key === "x" || event.key === "v" || event.key === "a")
    ) {
      event.preventDefault()
    }
    if (event.key === "F12" || (event.ctrlKey && event.shiftKey && event.key === "I")) {
      event.preventDefault()
    }
  }

  // Add event listeners only to the PDF container.
  React.useEffect(() => {
    if (pdfContainerRef.current && !isOperate) {
      const container = pdfContainerRef.current

      container.addEventListener("contextmenu", handleContextMenu)
      container.addEventListener("keydown", handleKeyDown)

      return () => {
        container.removeEventListener("contextmenu", handleContextMenu)
        container.removeEventListener("keydown", handleKeyDown)
      }
    }
  }, [isOperate])

  return (
    <div
      ref={pdfContainerRef}
      tabIndex={0} // 使 div 可聚焦，以便捕获键盘事件
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
