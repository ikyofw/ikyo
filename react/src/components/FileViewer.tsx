import React from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { validateResponse } from "../utils/sysUtil"
import ThreeDViewer from "./3d/ThreeDViewer"
import ImgViewer from "./viewer/ImgViewer"
import PDFViewer from "./viewer/PDFViewer"

interface IFileViewer {
  params: any
  fixed?: boolean // decide whether to display the page overlay and close button of viewer
  isOperate?: boolean // download & print & copy...
  screenID?: string
}

function isImgFile(pathImg: string) {
  if (pathImg.startsWith("data:image")) {
    return true
  } else if (/\.(jpg|jpeg|png|GIF|JPG|PNG)$/.test(pathImg)) {
    return true
  } else {
    return false
  }
}

function isPdfFile(pathPdf: string) {
  if (pathPdf.startsWith("data:application/pdf")) {
    return true
  } else if (/\.(pdf|PDF)$/.test(pathPdf)) {
    return true
  } else {
    return false
  }
}

function is3DFile(path3D: string) {
  if (path3D.indexOf("pd001q") > -1) {
    return true
  } else {
    return false
  }
}

const FileViewer: React.FC<IFileViewer> = (props) => {
  const HttpDownload = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD)

  const name = props.params.name
  const caption = props.params.caption
  const dataUrl = props.params.dataUrl
  const disWidth = props.params.disWidth
  const disHeight = props.params.disHeight
  const isFixed = props.fixed ?? false

  const [fileUrl, setFileUrl] = React.useState(dataUrl)
  const [showFlag, setShowFlag] = React.useState(false)
  const [isOperate, setIsOperate] = React.useState(props.isOperate ?? false)
  const [visible, setVisible] = React.useState(true)

  React.useEffect(() => {
    if (fileUrl && is3DFile(fileUrl)) {
      setShowFlag(false)
      setTimeout(() => {
        setShowFlag(true)
      }, 1)
    }
  }, [fileUrl, props.params]) // page refresh

  // Hide scrollbars when display Viewer - Valid
  // document.body.style.overflow = "hidden"
  // React.useEffect(() => {
  //   if (visible && (isPdfFile(fileUrl) || isImgFile(fileUrl))) {
  //     document.body.style.overflow = "hidden"
  //   } else {
  //     document.body.style.overflow = "auto"
  //   }
  //   return () => {
  //     document.body.style.overflow = "auto"
  //   }
  // }, [visible, fileUrl])

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ESC alway valid
      if (e.key === "Escape" && !isFixed) {
        setVisible(false)
        return
      }

      const isViewable = fileUrl && (isPdfFile(fileUrl) || isImgFile(fileUrl))
      if (!visible || !isViewable || isOperate) return

      if (e.ctrlKey && ["p", "s", "c", "x", "v", "a"].includes(e.key.toLowerCase())) {
        e.preventDefault()
      }

      if (e.key === "F12" || (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "i")) {
        e.preventDefault()
      }
    }

    const handleContextMenu = (e: MouseEvent) => {
      const isViewable = fileUrl && (isPdfFile(fileUrl) || isImgFile(fileUrl))
      if (!visible || !isViewable || isOperate) return
      e.preventDefault()
    }

    document.addEventListener("keydown", handleKeyDown)
    document.addEventListener("contextmenu", handleContextMenu)
    return () => {
      document.removeEventListener("keydown", handleKeyDown)
      document.removeEventListener("contextmenu", handleContextMenu)
    }
  }, [fileUrl, visible, isOperate])

  React.useEffect(() => {
    if (dataUrl && !isPdfFile(dataUrl) && !isImgFile(dataUrl) && !is3DFile(dataUrl)) {
      HttpDownload(dataUrl).then((response) => {
        let respType = response.headers?.["content-type"]
        let respParam = response.headers?.["custom-param"]
        var reader = new FileReader()
        if (respType.trim().toLocaleLowerCase() === "application/json") {
          reader.onload = (e) => {
            let data = JSON.parse(e.target.result as string)
            validateResponse(data, true)
          }
          reader.readAsText(response.data)
        } else {
          const blob = new Blob([response.data])
          reader.readAsDataURL(blob)
          reader.onload = (e) => {
            let base64: string = e.target.result.toString() // data:application/octet-stream;base64, XXX
            base64 = base64.split(",")[1]
            let fileType = respType.split("/")[1]
            let newPdfBlob = "data:" + (fileType === "pdf" ? "application" : "image") + "/" + fileType + ";base64," + base64
            setFileUrl(newPdfBlob)
            if (respParam && respParam !== "null") {
              setIsOperate(JSON.parse(respParam).isOperate)
            }
          }
        }
      })
    }
  }, [dataUrl])

  if (fileUrl && visible) {
    const isPdf = isPdfFile(fileUrl)
    const isImg = isImgFile(fileUrl)

    if (isPdf || isImg) {
      window.scrollTo({ top: 0, behavior: "auto" }) // Automatically scroll to the top
      return (
        <>
          {/* Page overlay layer */}
          {!isFixed ? (
            <div
              style={{
                position: "fixed",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                backgroundColor: "rgba(0,0,0,0.3)",
              }}
            />
          ) : null}
          {/* viewer */}
          {isPdf ? (
            <PDFViewer
              fileUrl={fileUrl}
              isOperate={isOperate}
              disWidth={disWidth}
              disHeight={disHeight}
              onClose={isFixed ? null : () => setVisible(false)}
            />
          ) : (
            <ImgViewer fileUrl={fileUrl} disWidth={disWidth} disHeight={disHeight} onClose={isFixed ? null : () => setVisible(false)} />
          )}
        </>
      )
    } else if (is3DFile(fileUrl)) {
      return (
        <form className="div_a" id={name} name={name}>
          <label className="fieldgroup_caption">{caption}</label>
          <div style={{ border: "1px solid black", width: "800px", height: "800px" }}>
            {showFlag ? <ThreeDViewer modelUrl={fileUrl} /> : null}
          </div>
        </form>
      )
    }
  }
  return null
}

export default FileViewer
