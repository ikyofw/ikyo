import cookie from "react-cookies"
import { useEffect, useState } from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"
import Login from "./Login"

const pyiGlobal = pyiLocalStorage.globalParams

const Logout = () => {
  const MENU_ACTION = pyiGlobal.COOKIE_MENU_ACTION
  const HttpDelete = useHttp(pyiGlobal.HTTP_TYPE_DELETE)

  const [logoutScc, setLogoutScc] = useState(Boolean)
  useEffect(() => {
    logout()
  }, [])

  const logout = async () => {
    await HttpDelete("/api/auth")
      .then((response) => response.json())
      .then((result) => {
        if (Number(result.code) === 1) {
          setLogoutScc(true)
          pyiLocalStorage.clearStore()
          cookie.remove(MENU_ACTION, { path: "/" })
          window.location.href = "/login"
        } else {
          sysUtil.showMessage(result.messages)
        }
      })
  }
  return logoutScc ? <Login /> : null
}

export default Logout
