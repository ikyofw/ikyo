## Function

The console in the front section displays a message based on the logger level.

## Implementation Method

### Get Logger Level

Cache the logger level when initializing the page.

ScreenRender.tsx:

    
    
    React.useEffect(() => {
      refreshList()
    }, []) // page refresh
    
    ...
    
    const refreshList = async () => {
      try {
        ...
        await HttpGet("/api/" + props.screenID + "/initScreen" + (params ? "?" + pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME + "=" + params : ""))
          .then((response) => {
            if (response.ok) return response.json()
            throw response
          })
          .then((result) => {
            let screenDfn = getScreenDfn(result, false)
            ...
          })
      } catch (error) {
        pyiLogger.error("Load screen failed: " + error, true)
      }
    }
    

sysUtil.tsx:

    
    
    export function getScreenDfn(responseJson: any, refreshPage: Boolean) {
      ...
    
      if (responseJson.logLevel) {
        localStorage.setItem("__LOG_LEVEL__", responseJson.logLevel)
      }
    
      ...
    }
    

### Create Logger Function

    
    
    import moment from "moment"
    
    const LOG_LEVEL_DEBUG = 1
    const LOG_LEVEL_INFO = 2
    const LOG_LEVEL_WARN = 3
    const LOG_LEVEL_ERROR = 4
    
    function Logger() {}
    
    Logger.prototype = {
      __log: function (level, text, printTrace = false) {
        let logLevelStr = localStorage.getItem("__LOG_LEVEL__")
        let logLevel = 1
        if (logLevelStr === "debug") {
          logLevel = 1
        } else if (logLevelStr === "info") {
          logLevel = 2
        } else if (logLevelStr === "warn") {
          logLevel = 3
        } else if (logLevelStr === "error") {
          logLevel = 4
        }
        if (!logLevelStr) {
          logLevelStr = "debug"
        }
    
        if (level < logLevel) {
          return
        }
    
        console.log(moment().format("YYYY-MM-DD hh:mm:ss.SSS") + " " + text)
        if (typeof text == "object") {
          console.log(">>>>>>>>")
          console.log(text)
          console.log("<<<<<<<<")
        }
        if (printTrace === true) {
          console.trace()
        }
      },
      debug: function (text, printTrace = false) {
        this.__log(LOG_LEVEL_DEBUG, text, printTrace)
      },
      info: function (text, printTrace = false) {
        this.__log(LOG_LEVEL_INFO, text, printTrace)
      },
      warn: function (text, printTrace = false) {
        this.__log(LOG_LEVEL_WARN, text, printTrace)
      },
      error: function (text, printTrace = false) {
        this.__log(LOG_LEVEL_ERROR, text, printTrace)
      },
    }
    
    const pyiLogger = new Logger()
    export default pyiLogger
    

### Use Logger Function

Four api's are provided corresponding to the four logger levels, the first
parameter accepted by the method is the displayed message, the second
parameter determines whether to print the location of the error or not.

    
    
    pyiLogger.debug("message", true)
    pyiLogger.info("message", true)
    pyiLogger.warn("message", true)
    pyiLogger.error("message", true)
    

