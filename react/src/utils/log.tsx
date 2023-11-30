/*
2022-10-18
Usage:
    import pyiLogger from "utils/logger"

    pyiLogger.debug('text or an object');
    pyiLogger.info('text or an object');
    pyiLogger.warn('text or an object');
    pyiLogger.error('text or an object', true);  

    Each method has two parameters: 
        1) text or an object to log. 
        2) print trace. default to false. E.g. pyiLogger.error('text or an object', true); 
*/

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
