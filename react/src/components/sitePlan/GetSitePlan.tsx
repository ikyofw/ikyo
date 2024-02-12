import { useEffect, useState } from "react"
import { useHttp } from "../../utils/http"
import * as sysUtil from "../../utils/sysUtil"
import * as Loading from "../Loading"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

import { SitePlan } from "./SitePlan"
import cookie from "react-cookies"
import pyiLogger from "../../utils/log"

const pyiGlobal = pyiLocalStorage.globalParams

interface GetSitePlanProps {
  params: any
  refreshFlag: number
  screenID: string
}

const GetSitePlan: React.FC<GetSitePlanProps> = (props) => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const [scatterData, setScatterData] = useState(null)
  const [helpUrl, setHelpUrl] = useState()

  useEffect(() => {
    initPage()
  }, [props.refreshFlag])

  const initPage = async () => {
    Loading.show()
    try {
      pyiLogger.debug(props.screenID)
      await HttpGet("/api/" + props.screenID + "/getScreen")
        .then((response) => response.json())
        .then((result) => {
          sysUtil.showMessage(result.messages)
          if (Number(result.code) === 100001) {
            pyiLocalStorage.clearStore()
            window.location.href = "/login"
          } else if (result.code === 1) {
            if (result.data) {
              sysUtil.showScreenTitle(result.data.viewID + " - " + result.data.viewTitle)
            }
            setHelpUrl(result.data["helpUrl"])
          }
        })

      let GetHoleData: any
      let GetPierData: any
      let GetLayerNames: any
      await HttpGet("/api/" + props.screenID + "/getBoreholeData")
        .then((response) => response.json())
        .then((result) => {
          if (result.code !== 1) {
            if (result.messages && result.messages !== null) {
              sysUtil.showMessage(result.messages)
            } else {
              pyiLogger.error("unknown error. code=" + result.code, true)
            }
          } else {
            GetHoleData = result.data
          }
        })
      await HttpGet("/api/" + props.screenID + "/getPilecapData")
        .then((response) => response.json())
        .then((result) => {
          if (result.code !== 1) {
            if (result.messages && result.messages !== null) {
              sysUtil.showMessage(result.messages)
            } else {
              pyiLogger.error("unknown error. code=" + result.code, true)
            }
          } else {
            GetPierData = result.data
          }
        })
      await HttpGet("/api/" + props.screenID + "/getLayerNames")
        .then((response) => response.json())
        .then((result) => {
          if (result.code !== 1) {
            if (result.messages && result.messages !== null) {
              sysUtil.showMessage(result.messages)
            } else {
              pyiLogger.error("unknown error. code=" + result.code, true)
            }
          } else {
            GetLayerNames = result.data
          }
        })

      let minY = 0
      let maxY = 100
      let minX = 0
      let maxX = 100
      let squareSpace = 100
      let xlist = []
      let ylist = []
      for (let index = 0; index < GetHoleData.length; index++) {
        const data = GetHoleData[index]
        xlist.push(data.x)
        ylist.push(data.y)
      }

      for (let index = 0; index < GetPierData.length; index++) {
        const data = GetPierData[index]
        xlist.push(data.x)
        ylist.push(data.y)
      }

      xlist.sort()
      ylist.sort()
      minX = xlist[0] - (xlist[0] % squareSpace) - squareSpace
      minY = ylist[0] - (ylist[0] % squareSpace) - squareSpace
      let maxlengthY = ylist[ylist.length - 1] - minY
      let maxlengthX = xlist[xlist.length - 1] - minX
      let maxlength = maxlengthX > maxlengthY ? maxlengthX : maxlengthY
      maxlength = maxlength - (maxlength % squareSpace) + squareSpace * 2
      maxX = minX + maxlength
      maxY = minY + maxlength

      setScatterData({ GetHoleData, GetPierData, minX, minY, maxX, maxY, GetLayerNames })
    } catch (error) {
      pyiLogger.error("Load page error: " + error, true)
      sysUtil.showErrorMessage("Load data error: " + error)
    } finally {
      Loading.remove()
    }
  }

  if (scatterData) {
    const isSupportSession = cookie.load(pyiGlobal.COOKIE_SYS_SUPPORT_SESSION)
    const sysHelpHref = pyiGlobal.API_URL + helpUrl + (isSupportSession !== "true" ? "?token=" + pyiLocalStorage.getToken() : "")
    document.getElementById("sysHelp").setAttribute("href", sysHelpHref)
  }

  return (
    <>
      <div style={{ width: "100%", height: "80%" }}>{scatterData ? <SitePlan scatterData={scatterData} editable={props.params.editable} screenID={props.screenID} /> : null}</div>
    </>
  )
}
export default GetSitePlan
