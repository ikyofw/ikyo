import React from "react"
import { Dialog, DialogContent, DialogTitle } from "@material-ui/core"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { getScreenDfn } from "../utils/sysUtil"
import ImageButton from "./ImageButton"
import Screen from "./Screen"
// import "../../public/static/css/Dialog-v2.css"

const pyiGlobal = pyiLocalStorage.globalParams
const close_icon = pyiGlobal.PUBLIC_URL + "images/close1.png"

interface CustomDialogProps {
  open: boolean
  dialogPrams: any
}

export default function CustomDialog(props: CustomDialogProps) {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const { open, dialogPrams } = props

  const screenRef = React.useRef<any>(null)
  const [fgNames, setFgNames] = React.useState([])
  const [dialogName, setDialogName] = React.useState(dialogPrams.dialogName)

  React.useEffect(() => {
    if (open) {
      setDialogName(dialogPrams.dialogName)
    }
  }, [dialogPrams.dialogName, open])

  const handleCancel = () => {
    setDialogName(null)
    setFgNames([])
    dialogPrams.onCancel()
  }
  const handleContinue = () => {
    let data = {}
    if (screenRef.current) {
      data = screenRef.current.getData(dialogPrams.dialogType)
    }
    setDialogName(null)
    setFgNames([])
    dialogPrams.onContinue(data)
    dialogPrams.onCancel()
  }

  React.useEffect(() => {
    if (dialogName) {
      refreshList()  // get sub screen's field groups name
    }
  }, [dialogName])

  const refreshList = async () => {
    try {
      let params = ""
      if (dialogName) {
        params = (params ? params + "&" : "?") + pyiGlobal.SUB_SCREEN_KEY_NAME + "=" + dialogName
      }
      await HttpGet("/api/" + dialogPrams.screenID + "/initScreen" + params)
        .then((response) => {
          if (response.ok) return response.json()
          throw response
        })
        .then((result) => {
          let screenDfn = getScreenDfn(result, false)
          if (!screenDfn) {
            pyiLogger.error("get initScreen error, please check.", true)
            return
          } else {
            setFgNames(screenDfn["fieldGroupNames"])
          }
        })
    } catch (error) {
      pyiLogger.error("Load screen failed: " + error, true)
    }
  }

  return (
    <Dialog open={open} onClose={handleCancel} aria-labelledby="form-dialog-title" className="dialog">
      <DialogTitle id="form-dialog-title" className="dialog_header">
        <div className="dialog_title">{dialogPrams.dialogTitle}</div>
        <img src={close_icon} alt="Close" className="dialog_close" onClick={handleCancel}></img>
      </DialogTitle>
      <DialogContent className="dialog_content" style={{width: dialogPrams.dialogWidth, height: dialogPrams.dialogHeight}}>
        <div style={{ paddingLeft: '4px', whiteSpace: 'pre-wrap'}}>{dialogPrams.dialogMessage}</div>
        {fgNames.length !== 0 ? <Screen ref={screenRef} subScreenNm={dialogName} fgNames={fgNames} screenID={dialogPrams.screenID} /> : null}
      </DialogContent>

      <div className="dialog_button">
        <ImageButton
          key={0}
          caption={dialogPrams.cancelNm + "  "}
          name={dialogPrams.cancelNm}
          widgetParameter={{ icon: "images/cancel_button.gif" }}
          clickEvent={handleCancel}
          editable={true}
        />
        <ImageButton
          key={1}
          caption={dialogPrams.continueNm}
          name={dialogPrams.continueNm}
          widgetParameter={{ icon: "images/action_button.gif" }}
          clickEvent={handleContinue}
          editable={true}
        />
      </div>
    </Dialog>
  )
}

// YL, 2022-08-05 New get dialog event & params - start
export const getDialogEvent = (e: string) => {
  if (e.indexOf("(") !== -1) {
    return e.split("(")[0]
  }
  return e
}

export const getDialogEventParamArr = (e: string) => {
  let params = []
  if (e.indexOf("(") !== -1) {
    let tmp = e.split("(")[1].split(")")[0].trim()
    if (tmp.indexOf(",") > -1) {
      tmp.split(",").forEach((p, index) => {
        params[index] = p.trim()
      })
    } else {
      params[0] = tmp
    }
  }
  return params
}

export const getDialogParams = (dialog: string) => {
  let params = {}
  dialog &&
    dialog.split(";").forEach((param: string) => {
      const paramName = param.split(":")[0].trim()
      const content = param.split(":")[1].trim()
      params[paramName] = content
    })
  return params
}

export const getDialogEventHandler = (eventName: string, screenID: string) => {
  if (eventName.charAt(0) === "/") {
    return eventName
  } else {
    return "/api/" + screenID + "/" + eventName
  }
}
