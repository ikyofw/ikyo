import { useEffect, useState } from "react"
import { useHttp } from "../../utils/http"
import * as sysUtil from "../../utils/sysUtil"
import * as Loading from "../Loading"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

import { SitePlan } from "./SitePlan"
import cookie from "react-cookies"
import pyiLogger from "../../utils/log"

const pyiGlobal = pyiLocalStorage.globalParams
const DEFAULT_LAYER_COLOR = "#FFFFFF"

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
      // await HttpGet("/api/" + props.screenID + "/getScreen")
      //   .then((response) => response.json())
      //   .then((result) => {
      //     sysUtil.showMessage(result.messages)
      //     if (Number(result.code) === 100001) {
      //       pyiLocalStorage.clearStore()
      //       window.location.href = "/login"
      //     } else if (result.code === 1) {
      //       if (result.data) {
      //         sysUtil.showScreenTitle(result.data.viewID + " - " + result.data.viewTitle)
      //       }
      //       setHelpUrl(result.data["helpUrl"])
      //     }
      //   })

      let GetHoleData: any
      let GetPierData: any
      let GetLayerNames: string[] = []
      let GetLayerColorSets: any[] = []
      let httpGetFlag = true
      await HttpGet("/api/" + props.screenID + "/getBoreholeData")
        .then((response) => response.json())
        .then((result) => {
          if (sysUtil.validateResponse(result, true)) {
            GetHoleData = result.data
          } else {
            httpGetFlag = false
          }
        })
      await HttpGet("/api/" + props.screenID + "/getPilecapData")
        .then((response) => response.json())
        .then((result) => {
          if (sysUtil.validateResponse(result, true)) {
            GetPierData = result.data
          } else {
            httpGetFlag = false
          }
        })
      await HttpGet("/api/" + props.screenID + "/getLayerNames")
        .then((response) => response.json())
        .then((result) => {
          if (sysUtil.validateResponse(result, true)) {
            result.data.map((item) => {
              if (Array.isArray(item)) {
                GetLayerNames.push(item[0])
                if (item.length === 2) {
                  let ls = { nm: item[0], color: item[1] }
                  GetLayerColorSets.push(ls)
                } else {
                  let ls = { nm: item, color: DEFAULT_LAYER_COLOR }
                  GetLayerColorSets.push(ls)
                }
              } else {
                GetLayerNames.push(item)
                let ls = { nm: item, color: DEFAULT_LAYER_COLOR }
                GetLayerColorSets.push(ls)
              }
            })
          } else {
            httpGetFlag = false
          }
        })

      if (httpGetFlag) {
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

        setScatterData({ GetHoleData, GetPierData, minX, minY, maxX, maxY, GetLayerNames, GetLayerColorSets })
      }
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
      <div style={{ width: "100%", height: "80%" }}>
        {scatterData ? <SitePlan scatterData={scatterData} editable={props.params.editable} screenID={props.screenID} /> : null}
      </div>
    </>
  )
}
export default GetSitePlan
