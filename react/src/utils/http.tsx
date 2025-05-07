import axios from "axios"
import pyiLocalStorage from "./pyiLocalStorage"
import { useContext } from "react"
import { suuidContext } from "../components/ConText"
import { showErrorMessage } from "../utils/sysUtil"
import pyiLogger from "../utils/log"

const TOKEN_NAME = "token"
const SCREEN_UUID_NAME = "SUUID"

export function getUrl(url: string) {
  let url2 = url.toLowerCase()
  if (!url2.startsWith("http://") && !url2.startsWith("https://")) {
    return pyiLocalStorage.globalParams.API_URL + url
  }
  return url
}

export function useHttp(type: string) {
  const conText = useContext(suuidContext)

  const getNewUrl = (url) => {
    let newUrl = getUrl(url)
    if (conText && conText.SUUID && newUrl.indexOf(SCREEN_UUID_NAME) < 0) {
      newUrl += newUrl.indexOf("?") >= 0 ? "&" : "?"
      newUrl += SCREEN_UUID_NAME + "=" + conText.SUUID
    }
    if (is3000Port()) {
      newUrl += newUrl.indexOf("?") >= 0 ? "&" : "?"
      newUrl += TOKEN_NAME + "=" + pyiLocalStorage.getToken()
    }
    return newUrl
  }

  if (type === pyiLocalStorage.globalParams.HTTP_TYPE_GET) {
    return async function (url: string, data?: any) {
      try {
        var result = await fetch(getNewUrl(url), {
          method: "GET",
        })
        return result
      } catch (error) {
        showErrorMessage("Failed to connect to the server.")
        pyiLogger.error("Connect to the server failed: " + error, true)
      }
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_POST) {
    return async function HttpPost(url: string, data: any) {
      try {
        var result = await fetch(getNewUrl(url), {
          method: "POST",
          headers: {
            Accept: "application/json,text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: data.body ? data.body : data,
        })
        return result
      } catch (error) {
        showErrorMessage("Failed to connect to the server.")
        pyiLogger.error("Connect to the server failed: " + error, true)
      }
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_DELETE) {
    return async function HttpDelete(url: string, data?: any) {
      try {
        var result = await fetch(getNewUrl(url), {
          method: "DELETE",
        })
        return result
      } catch (error) {
        showErrorMessage("Failed to connect to the server.")
        pyiLogger.error("Connect to the server failed: " + error, true)
      }
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_POST_NO_HEADER) {
    return async function HttpPostNoHeader(url: string, data: any) {
      try {
        var result = await fetch(getNewUrl(url), {
          method: "POST",
          body: data.body ? data.body : data,
        })
        return result
      } catch (error) {
        showErrorMessage("Failed to connect to the server.")
        pyiLogger.error("Connect to the server failed: " + error, true)
      }
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD) {
    return async function HttpDownload(url: string, data?: any) {
      try {
        var result = await axios.post(getNewUrl(url), data ? data : "", {
          method: "POST",
          responseType: "blob", // Set the data type of the response to a Blob object containing binary data, MUST BE SET!!!!
        })
        return result
      } catch (error) {
        showErrorMessage("Failed to connect to the server.")
        pyiLogger.error("Connect to the server failed: " + error, true)
      }
    }
  }
}

export function is3000Port() {
  const href = window.location.href
  if (href.indexOf(":3000") > 0) {
    return true
  }
  return false
}
