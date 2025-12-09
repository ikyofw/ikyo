import React, { useRef, useState } from "react"
import { useLocation } from "react-router-dom"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { getResponseData } from "../utils/sysUtil"
import { suuidContext } from "./ConText"
import Screen from "./Screen"

const ScreenRender = (props) => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const screenRef = useRef<any>(null)
  const [fgNames, setFgNames] = useState([])
  const [SUUID, setSUUID] = useState("")

  const location = useLocation()
  React.useEffect(() => {
    unloadScreen()
  }, [location])

  React.useEffect(() => {
    refreshList()
  }, []) // page refresh

  const unloadScreen = async () => {
    try {
      // When opening a new page send a request to the backend with the path and SUUID information of the old page
      const oldPath = localStorage.getItem("__PYI_OLD_PATH__")
      const screenIDs = localStorage.getItem("__PYI_SCREEN_IDS__").split(",")
      const paths = localStorage.getItem("__PYI_PATHS__").split(",")
      if (oldPath) {
        localStorage.removeItem("__PYI_OLD_PATH__")
      }
      let oldScreenID, newScreenID
      paths.forEach((path1, index) => {
        // YL, 2023-03-21 bugfix - start
        if (oldPath) {
          if (path1.toLocaleLowerCase() === oldPath.slice(1).toLocaleLowerCase()) {
            oldScreenID = screenIDs[index]
          }
        }
        if (location.pathname) {
          if (path1.toLocaleLowerCase() === location.pathname.slice(1).toLocaleLowerCase()) {
            newScreenID = screenIDs[index]
          }
        }
        // YL, 2023-03-21 - end
      })
      var data = { oldScreenID: oldScreenID, newScreenID: newScreenID }
      const oldSUUID = sessionStorage.getItem("SUUID")

      if (oldScreenID) {
        HttpPost("/api/" + oldScreenID + "/UNLOADED_SCREEN" + (oldSUUID ? "?SUUID=" + oldSUUID : ""), JSON.stringify(data))
          .then((response) => response.json())
          .then((result) => {})
      }
    } catch (error) {
      pyiLogger.error("Unload screen failed: " + error, true)
    }
  }

  const refreshList = async () => {
    try {
      let params = location.search || ""
      const oldSUUID = sessionStorage.getItem("SUUID")
      if (oldSUUID) {
        if (params) {
          params += `&SUUID=${encodeURIComponent(oldSUUID)}`
        } else {
          params = `?SUUID=${encodeURIComponent(oldSUUID)}`
        }
      }

      await HttpGet("/api/" + props.screenID + "/initScreen" + params)
        .then((response) => response.json())
        .then((result) => {
          let screenDfn = getResponseData(result)
          if (!screenDfn) {
            pyiLogger.error("get initScreen error, please check.", true)
            return
          } else {
            setFgNames(screenDfn["fieldGroupNames"])
            sessionStorage.setItem("SUUID", screenDfn["SUUID"])
            setSUUID(screenDfn["SUUID"])
          }
        })
    } catch (error) {
      pyiLogger.error("Load screen failed: " + error, true)
    }
  }

  if (fgNames.length !== 0 && SUUID !== "") {
    return (
      <suuidContext.Provider value={{ SUUID }}>
        <Screen ref={screenRef} fgNames={fgNames} screenID={props.screenID} />
      </suuidContext.Provider>
    )
  } else {
    return null
  }
}

export default ScreenRender
