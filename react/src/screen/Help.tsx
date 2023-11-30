import { useEffect, useState } from "react"
import FileViewer from "../components/FileViewer"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { validateResponse } from "../utils/sysUtil"
import useWindowSize from "../utils/useWindowSize"

const Help = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const HttpDownload = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD)

  const { width, height } = useWindowSize()
  const [htmlData, setHtmlData] = useState(null)
  const [fileData, setFileData] = useState(null)

  var helpUrl
  var helpDocType
  useEffect(() => {
    var urlSuffix = window.location.search
    if (urlSuffix.indexOf("&")) {
      helpUrl = urlSuffix.substring(urlSuffix.indexOf("url=") + 4, urlSuffix.indexOf("&"))
      helpDocType = urlSuffix.substring(urlSuffix.indexOf("docType=") + 8)
    } else {
      helpUrl = urlSuffix.substring(urlSuffix.indexOf("url=") + 4)
    }
    getData()
  }, [])

  const getData = async () => {
    if (helpUrl) {
      if (helpDocType.trim().toLocaleLowerCase() === "html") {
        await HttpGet(helpUrl)
          .then((response) => response.text())
          .then((result) => {
            setHtmlData(result)
          })
      } else if (helpDocType.trim().toLocaleLowerCase() === "pdf") {
        await HttpDownload(helpUrl).then((response) => {
          let respType = response.headers?.["content-type"]
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
              let newpdfblob = "data:" + (fileType == "pdf" ? "application" : "image") + "/" + fileType + ";base64," + base64
              setFileData(newpdfblob)
            }
          }
        })
      }
    }
  }
  return htmlData ? <>{htmlData}</> : fileData ? <FileViewer params={{ dataUrl: fileData, disHeight: height, disWidth: width }} /> : null
}
export default Help
