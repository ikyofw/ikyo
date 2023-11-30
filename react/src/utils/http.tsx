import axios from "axios"
import { useContext } from "react"
import { suuidContext } from "../components/ConText"
import pyiLocalStorage from "./pyiLocalStorage"

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
    return function (url: string, data?: any) {
      var result = fetch(getNewUrl(url), {
        method: "GET",
      })
      return result
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_POST) {
    return function HttpPost(url: string, data: any) {
      var result = fetch(getNewUrl(url), {
        method: "POST",
        headers: {
          Accept: "application/json,text/plain, */*",
          "Content-Type": "application/json",
        },
        body: data.body ? data.body : data,
      })
      return result
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_DELETE) {
    return function HttpDelete(url: string, data?: any) {
      var result = fetch(getNewUrl(url), {
        method: "DELETE",
      })
      return result
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_POST_NO_HEADER) {
    return function HttpPostNoHeader(url: string, data: any) {
      var result = fetch(getNewUrl(url), {
        method: "POST",
        body: data.body ? data.body : data,
      })
      return result
    }
  } else if (type === pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD) {
    return function HttpDownload(url: string, data?: any) {
      var result = axios.post(getNewUrl(url), data ? data : "", {
        method: "POST",
        responseType: "blob", // Set the data type of the response to a Blob object containing binary data, MUST BE SET!!!!
      })
      return result
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
