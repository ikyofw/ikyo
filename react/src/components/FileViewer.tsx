import React from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { validateResponse } from "../utils/sysUtil"
import ThreeDViewer from "./3d/ThreeDViewer"
import ImgViewer from "./viewer/ImgViewer"
import PDFViewer from "./viewer/PDFViewer"

interface IFileViewer {
  params: any
  isOperate?: boolean
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

  const [fileUrl, setFileUrl] = React.useState(dataUrl)
  const [showFlag, setShowFlag] = React.useState(false)
  const [isOperate, setIsOperate] = React.useState(props.isOperate)

  React.useEffect(() => {
    if (fileUrl && is3DFile(fileUrl)) {
      setShowFlag(false)
      setTimeout(() => {
        setShowFlag(true)
      }, 1)
    }
  }, [fileUrl, props.params]) // page refresh

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
            if (respParam) {
              setIsOperate(JSON.parse(respParam).isOperate)
            }
          }
        }
      })
    }
  }, [dataUrl])

  if (fileUrl) {
    if (isPdfFile(fileUrl)) {
      return <PDFViewer fileUrl={fileUrl} isOperate={isOperate} disWidth={disWidth ? disWidth : null} disHeight={disHeight ? disHeight : null} />
    } else if (isImgFile(fileUrl)) {
      return <ImgViewer fileUrl={fileUrl} disWidth={disWidth ? disWidth : null} disHeight={disHeight ? disHeight : null} />
    } else if (is3DFile(fileUrl)) {
      return (
        <form className="div_a" id={name} name={name}>
          <label className="fieldgroup_caption">{caption}</label>
          <div style={{ border: "1px solid black", width: "800px", height: "800px" }}>
            {showFlag ? (
              <ThreeDViewer
                modelUrl={fileUrl + "?token=" + pyiLocalStorage.getToken()}
                scale={{ x: 0.5, y: 0.5, z: 0.5 }}
                disWidth="800"
                disHeight="800"
              />
            ) : null}
          </div>
        </form>
      )
    }
  }
  return null
}

export default FileViewer
