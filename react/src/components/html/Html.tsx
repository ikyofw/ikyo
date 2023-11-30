/* eslint-disable react-hooks/exhaustive-deps */
import React from "react"
import { addStaticResource } from "../Screen"
import { useHttp } from "../../utils/http"
import { validateResponse } from "../../utils/sysUtil"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

interface HtmlPrams {
  resources: any
  params: any
}

const Html: React.FC<HtmlPrams> = (props) => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const data = props.params.data
  const dataUrl = props.params.dataUrl

  const [htmlPrams, setHtmlPrams] = React.useState("")

  React.useEffect(() => {
    getHtml()
  }, [props.params])

  const getHtml = async () => {
    if (data) {
      setHtmlPrams(data)
    } else if (dataUrl) {
      await HttpGet(dataUrl)
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, true)) {
            setHtmlPrams(result.data)
          }
        })
    }
  }

  React.useEffect(() => {
    const cont = document.getElementById(props.params.name)
    cont.innerHTML = htmlPrams
    const oldScripts = cont.getElementsByTagName("script")
    const scriptLen = oldScripts.length
    let jsFilesNum = 0
    let content
    for (var i = 0; i < scriptLen; i++) {
      let oldScript = oldScripts[0]
      let newScript = document.createElement("script")

      // if the oldScript is existent
      if (oldScript) {
        // remove the old script tag from the container
        cont.removeChild(oldScript)
        newScript.type = "text/javascript"

        // if the old script tag has a src attribute, set the src of the new script tag
        if (oldScript.src) {
          newScript.src = oldScript.src

          // add onload and onratechange event handlers to the new script tag
          // eslint-disable-next-line no-loop-func
          newScript.onload = newScript.onratechange = function () {
            // increment the jsFilesNum when a js file is loaded
            jsFilesNum += 1

            // if all the js files are loaded, create another script tag and append it to the container
            if (jsFilesNum > 0 && scriptLen - 1 === jsFilesNum) {
              let sc = document.createElement("script")
              sc.type = "text/javascript"
              sc.innerHTML = content
              const cont = document.getElementById(props.params.name)
              cont.appendChild(sc)
            }
          }
          cont.appendChild(newScript)
        } else if (oldScript.innerHTML) {
          // if the old script tag doesn't have a src attribute but has innerHTML
          newScript.type = "text/javascript"
          newScript.innerHTML = oldScript.innerHTML
          content = oldScript.innerHTML

          // if there's only one script tag that contains only script content
          if (scriptLen === 1) {
            cont.appendChild(newScript)
          }
        }
      }
    }

    // if props.resources is not empty, add each resource in props.resources
    if (Object.keys(props.resources).length > 0) {
      props.resources.forEach((resource) => {
        addStaticResource(resource)
      })
    }
  }, [htmlPrams, props.resources])

  return <div id={props.params.name} style={{paddingLeft: '5px'}}></div> // YL, 2022-12-06 bugfix if htmlParams is null
}

export default Html
