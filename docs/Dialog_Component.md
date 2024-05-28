## Function

Adds an interrupt before the front-end request to the back-end. If necessary,
a dialog box can be popped up at this stage to display a prompt message and
let the user decide whether to continue the request.

## Pre-processing

The dialog component requires a set of parameters to be passed. All possible
parameters:

    
    
        dialogName: the name of dialog.
        dialogTitle: the title of the dialog.
        dialogMessage: the message of the dialog.
        dialogBeforeDisplayEvent: the parameters of click event before display dialog.
        continueNm: the name of continue button in dialog.
        cancelNm: the name of cancel button in dialog.
        width: dialog width.
        height: dialog height.
    

  
First, parse the parameters to confirm whether the dialog needs to be
displayed, and if so, parse the required parameters passed to the dialog
component,

If the given parameter contains "dialogBeforeDisplayEvent", get the dialog box
information from this given address to the backend

    
    
      const btnClick = async (e: any) => {
        let removeLoadingDiv = true
        Loading.show()
        pyiLocalStorage.clearSysMsgs()
        const eventHandler = e.eventHandler[0]
        const eventHandlerParameter = e.eventHandler[1].fieldGroups
        // YL, 2022-07-18 NEW encapsulates all pages - start
        const btnType = e.eventHandler[2]["type"] ? e.eventHandler[2]["type"] : "normal"
    
        try {
          let buttonData = {}
          if (btnType === pyiGlobal.UPLOAD_BTN_TYPE) {
            eventHandlerParameter.forEach((fgName: string) => {
              buttonData = refs[fgName].current.formData()
            })
          } else {
            buttonData = createEventData(eventHandlerParameter)
          }
    
          if (Object.keys(e.eventHandler[2]).toString().trim().toLowerCase().indexOf("dialog") > -1) {
            // If there is a dialog, show the dialog first.
            const dialogParams = getDialogParams(e.eventHandler[2]["dialog"])
            showDialog(dialogParams, btnType, eventHandler, buttonData)
            removeLoadingDiv = false
          } else {
            // If there is no dialog, the button click event is triggered directly.
            onClickEvent(btnType, eventHandler, buttonData)
            removeLoadingDiv = false
          }
          // YL, 2022-07-18 - end
        } catch (error) {
          showErrorMessage("System error, please ask administrator to check.")
          pyiLogger.error(eventHandler + " error: " + error)
          removeLoadingDiv = true
        } finally {
          if (removeLoadingDiv) {
            Loading.remove() // can't delete
          }
        }
      }
    

Show dialog.

    
    
    const showDialog = async (dialogParams, btnType, eventHandler, buttonData) => {
      Loading.show()
      try {
        const dialogName = dialogParams["dialogName"]
        const title = dialogParams["dialogTitle"]
        const message = dialogParams["dialogMessage"]
        const eventWithParams = dialogParams["dialogBeforeDisplayEvent"]
        const continueNm = dialogParams["continueNm"] ? dialogParams["continueNm"] : "OK"
        const cancelNm = dialogParams["cancelNm"] ? dialogParams["cancelNm"] : "Cancel"
        const dialogWidth = dialogParams["width"]
        const dialogHeight = dialogParams["height"]
        // YL, 2022-10-08 BUGFIX if no dialog will error - start
        let eventName
        let eventParams
        let beforeDisplayData = {}
        if (eventWithParams) {
          eventName = getDialogEvent(eventWithParams)
          eventParams = getDialogEventParamArr(eventWithParams)
          beforeDisplayData = createEventData(eventParams)
        }
    
        if (eventName) {
          const dialogEventHandler = getDialogEventHandler(eventName, props.screenID)
          await HttpPost(dialogEventHandler, JSON.stringify(beforeDisplayData))
            .then((response) => response.json())
            .then((result) => {
              if (result.data && result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]) {
                sessionStorage.setItem(pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME, JSON.stringify(result.data))
                if (result.data[pyiGlobal.CMD_IS_WCI_MENU]) {
                  // go to wci menu
                  window.location.href = "wci1/menu?id=" + result.data[pyiGlobal.ACTION_COMMAND]
                } else {
                  // pyi menu
                  window.location.href = result.data[pyiGlobal.OPEN_SCREEN_KEY_NAME]
                }
              }
              if (validateResponse(result, false)) {
                const dialogTitle = result.data && result.data["title"] ? result.data["title"] : ""
                const dialogMessage = result.data && result.data["dialogMessage"] ? result.data["dialogMessage"] : ""
                const params = {
                  dialogTitle: dialogTitle,
                  dialogMessage: dialogMessage,
                  dialogType: btnType,
                  screenID: props.screenID,
                  dialogName: dialogName,
                  onCancel: () => closeDialog(),
                  onContinue: (dialogData) => {
                    if (btnType === pyiGlobal.UPLOAD_BTN_TYPE) {
                      onClickEvent(btnType, eventHandler, dialogData)
                    } else {
                      onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData })
                    }
                  },
                  continueNm: continueNm,
                  cancelNm: cancelNm,
                  dialogWidth: dialogWidth,
                  dialogHeight: dialogHeight
                }
                openDialog(params)
              }
            })
        } else {
          const params = {
            dialogTitle: title,
            dialogMessage: message,
            dialogType: btnType,
            screenID: props.screenID,
            dialogName: dialogName,
            onCancel: () => closeDialog(),
            onContinue: (dialogData) => {
              if (btnType === pyiGlobal.UPLOAD_BTN_TYPE) {
                onClickEvent(btnType, eventHandler, dialogData)
              } else {
                onClickEvent(btnType, eventHandler, { ...buttonData, ...dialogData })
              }
            },
            continueNm: continueNm,
            cancelNm: cancelNm,
            dialogWidth: dialogWidth,
            dialogHeight: dialogHeight
          }
          openDialog(params)
        }
      } catch (error) {
        pyiLogger.error(error)
        Loading.remove()
      } finally {
        Loading.remove()
      }
    }
    

## Component Implementation

### Initially, a method is established to control the display status of the
dialog box and to configure the required parameters for the dialog box

    
    
    const [dialogOpen, setDialogOpen] = React.useState(false)
    const [dialogPrams, setDialogPrams] = React.useState({ onCancel: () => closeDialog() })
    
    ...
    
    const subScreenNode = React.useMemo(() => {
      return <>{!props.subScreenNm ? <CustomDialog open={dialogOpen} dialogPrams={dialogPrams} /> : null}</>
    }, [dialogOpen, props.subScreenNm])
    
    return (
      <>
        ...
        {subScreenNode}
      </>
    )
    

### Then comes the main part of the dialog component

    
    
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
            <div style={{ paddingLeft: '4px'}}>{dialogPrams.dialogMessage}</div>
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
    

### Finally, some functions that need to be used in the dialog implementation
are placed at the end of the component

    
    
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
          tmp.split(",").map((p, index) => {
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
      dialog && dialog.split(";").map((param: string) => {
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
    

