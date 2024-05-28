## Function

Display messages contained in content returned by the backend on the frontend.

Example:

[![SysMsgExample.png](images/SysMsgExample.png)](images/SysMsgExample.png)

## Implementation Method

Put different icons in front of the message according to the different message
levels and then display them.

    
    
    const pyiGlobal = pyiLocalStorage.globalParams
    const debugIcon = pyiGlobal.PUBLIC_URL + "images/debug_icon.png"
    const infoIcon = pyiGlobal.PUBLIC_URL + "images/info_icon.gif"
    const warningIcon = pyiGlobal.PUBLIC_URL + "images/warning_icon.gif"
    const errorIcon = pyiGlobal.PUBLIC_URL + "images/error_icon.gif"
    const fatalIcon = pyiGlobal.PUBLIC_URL + "images/fatal_icon.png"
    const exceptionIcon = pyiGlobal.PUBLIC_URL + "images/exception_icon.gif"
    
    interface ISysMsgBox {
      ref: any
      label: string
      value: string
      name: string
      editable: boolean
      onBlur?: FocusEventHandler<HTMLInputElement>
    }
    const SysMsgBox: React.FC<ISysMsgBox> = forwardRef((props, ref: Ref<any>) => {
      const negativeMessages = ['error', 'exception', 'warning', 'fatal']
      return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
          {props.label.toLowerCase() === "debug" ? (
            <img src={debugIcon} alt="debug icon" />
          ) : props.label.toLowerCase() === "info" ? (
            <img src={infoIcon} alt="info icon" />
          ) : props.label.toLowerCase() === "warning" ? (
            <img src={warningIcon} alt="warning icon" />
          ) : props.label.toLowerCase() === "error" ? (
            <img src={errorIcon} alt="error icon" />
          ) : props.label.toLowerCase() === "fatal" ? (
            <img src={fatalIcon} alt="fatal icon" />
          ) : props.label.toLowerCase() === "exception" ? (
            <img src={exceptionIcon} alt="exception icon" />
          ) : (
            <img src={infoIcon} alt="info icon" />
          )}
    
          <div
            style={{
              backgroundColor: "transparent",
              border: "hidden",
              paddingLeft: "10px",
              width: "97%",
              float: "right",
              fontSize: "2em",
              whiteSpace: "pre-line",
              color: negativeMessages.indexOf(props.label.toLowerCase()) !== -1 ? "red": "",
              fontWeight: negativeMessages.indexOf(props.label.toLowerCase()) !== -1 ? "bold": "",
            }}
            ref={ref}
            id={props.name}
            contentEditable={!props.editable}
            onBlur={props.onBlur}
          >
            {props.value}
          </div>
        </div>
      )
    })
    export default SysMsgBox
    

