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
  const [textData, setTextData] = useState(null)
  const [htmlData, setHtmlData] = useState(null)
  const [fileData, setFileData] = useState(null)

  var helpUrl
  var helpDocType = "pdf"
  useEffect(() => {
    var urlSuffix = window.location.search.substring(1)
    document.title = "WCI 2 - " + urlSuffix.split("=")[urlSuffix.split("=").length - 1] + " Help"
    urlSuffix = urlSuffix.replace("=", "/")
    if (urlSuffix.indexOf("&") > -1) {
      helpUrl = urlSuffix.substring(0, urlSuffix.indexOf("&"))
      helpDocType = urlSuffix.substring(urlSuffix.indexOf("docType=") + 8)
    } else {
      helpUrl = urlSuffix
    }
    getData()
  }, [])

  const getData = async () => {
    if (helpUrl) {
      helpUrl = "/api/help/" + helpUrl
      if (helpDocType.trim().toLocaleLowerCase() === "html") {
        await HttpGet(helpUrl)
          .then((response) => response.text())
          .then((result) => {
            setTextData(result)
          })
      } else if (helpDocType.trim().toLocaleLowerCase() === "pdf") {
        await HttpDownload(helpUrl).then((response) => {
          let respType = response.headers?.["content-type"]
          var reader = new FileReader()
          if (respType.trim().toLocaleLowerCase() === "application/pdf") {
            const blob = new Blob([response.data])
            reader.readAsDataURL(blob)
            reader.onload = (e) => {
              let base64: string = e.target.result.toString() // data:application/octet-stream;base64, XXX
              base64 = base64.split(",")[1]
              let fileType = respType.split("/")[1]
              let newpdfblob = "data:" + (fileType == "pdf" ? "application" : "image") + "/" + fileType + ";base64," + base64
              setFileData(newpdfblob)
            }
          } else if (respType.trim().toLocaleLowerCase() === "application/json") {
            reader.onload = (e) => {
              let data = JSON.parse(e.target.result as string)
              validateResponse(data, true)
            }
            reader.readAsText(response.data)
          } else if (respType.trim().toLocaleLowerCase() === "application/html") {
            reader.onload = (e) => {
              try {
                let content: string = e.target.result as string // 显式类型转换为 string
                setHtmlData(content)
                const cont = document.getElementById("htmlContainer")
                if (cont) {
                  cont.innerHTML = content
                } else {
                  console.error('Element with ID "htmlContainer" not found.')
                }
              } catch (error) {
                console.error("Error processing HTML:", error)
                setTextData("Error processing HTML: " + error)
              }
            }
            reader.readAsText(response.data)
          } else {
            reader.onload = (e) => {
              setTextData(e.target.result)
            }
            reader.readAsText(response.data)
          }
        })
      }
    }
  }
  return (
    <>
      {textData ? (
        <div style={{ fontSize: "12pt" }}>{textData}</div>
      ) : htmlData ? (
        <div id="htmlContainer"></div>
      ) : fileData ? (
        <FileViewer params={{ dataUrl: fileData, disHeight: height, disWidth: width }} isOperate={false} />
      ) : null}
    </>
  )
}
export default Help
