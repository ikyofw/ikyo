import { useEffect } from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"

const Home = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  useEffect(() => {
    checkLogin()
  }, [])

  const checkLogin = async () => {
    await HttpGet("/api/auth")
      .then((response) => response.json())
      .then((result) => {
        if (Number(result.code) === 100001) {
          pyiLocalStorage.clearStore()
          window.location.href = "/login"
        } else if (Number(result.code) !== 1) {
          sysUtil.showMessage(result.messages)
        }
      })
  }

  return pyiLocalStorage.getCurrentUser() ? <h2>Thanks for using IUI</h2> : null
}

export default Home
