import { useEffect, useState } from "react"
import { SoilProfile } from "./SoilProfile"

import * as sysUtil from "../../utils/sysUtil"
import { useHttp } from "../../utils/http"
import * as Loading from "../Loading"
import pyiLogger from "../../utils/log"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

export function GetSoilData(props) {
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [soilData, setSoilData] = useState([])

  const getSoilData = async (pts) => {
    Loading.show()
    try {
      await HttpPost("/api/" + props.screenID + "/getSoilData", "segs=" + pts)
        .then((response) => response.json())
        .then((result) => {
          if (sysUtil.validateResponse(result, true)) {
            let soilDataList = result.data
            setSoilData(soilDataList)
          }
        })
    } catch (error) {
      pyiLogger.error("get soil data failed: " + error, true)
    } finally {
      Loading.remove()
    }
  }

  useEffect(() => {
    if (props.ptArray && props.ptArray.length >= 2) {
      Loading.show()
      let pts = ""
      for (let i = 0; i < props.ptArray.length; i++) {
        let pt = props.ptArray[i]
        if (i > 0) {
          pts += ","
        }
        pts += pt[0] + "," + pt[1]
      }
      getSoilData(pts)
    }
  }, [props.ptArray])

  useEffect(() => {
    if (!props.showSoilData) {
      setSoilData([])
    }
  }, [props.showSoilData])

  return <SoilProfile soilData={soilData} ptArray={props.ptArray} colorLayerSets={props.colorLayerSets} showSoilData={props.showSoilData} />
}
