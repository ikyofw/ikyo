import React, { useEffect, useCallback } from "react"
import { useHttp } from "../../utils/http"
import { validateResponse } from "../../utils/sysUtil"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

interface StaticHtml {
  params: any
}

const Iframe: React.FC<StaticHtml> = (props) => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const caption = props.params.caption
  const data = props.params.data
  const dataUrl = props.params.dataUrl
  const name = props.params.name

  const [htmlData, setHtmlData] = React.useState("")

  React.useEffect(() => {
    if (data) {
      setHtmlData(data)
    } else if (dataUrl) {
      HttpGet(dataUrl)
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, true)) {
            setHtmlData(result.data)
          }
        })
    }
  }, [data, dataUrl])

  const handleWindowResize = useCallback(() => {
    const ifm = document.getElementById(name) as any
    if (ifm) {
      const height = ifm.contentWindow.document.body.scrollHeight + 16
      ifm.style.height = height + "px"
      ifm.scrolling = "no"
    }
  }, [])

  useEffect(() => {
    handleWindowResize()
    window.addEventListener("resize", handleWindowResize)
    return () => {
      window.removeEventListener("resize", handleWindowResize)
    }
  }, [handleWindowResize])

  return (
    <>
      <iframe
        id={name}
        onLoad={handleWindowResize}
        style={{ width: "100%", border: "none", overflow: "auto" }}
        title={caption}
        srcDoc={htmlData}
      ></iframe>
    </>
  )
}

export default Iframe
