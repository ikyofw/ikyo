import { useEffect } from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"
import MenuBar from "./MenuBar"

const TopBar = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const topBarImg = pyiLocalStorage.globalParams.PUBLIC_URL + "images/IUI.png"

  useEffect(() => {
    checkLogin()
  }, [])

  const checkLogin = async () => {
    await HttpGet("/api/auth")
      .then((response) => response.json())
      .then((result) => {
        if (Number(result.code) === 1) {
          pyiLocalStorage.setCurrentUser(result.data.user)
          pyiLocalStorage.setToken(result.data.token)
        } else if (!window.location.href.endsWith("login")) {
          sysUtil.validateResponse(result, false)
        }
      })
  }

  return (
    <>
      <table id="sys_topbar" style={{ backgroundColor: "#E6FFEC" }}>
        <tbody>
          <tr>
            <td>
              <img style={{ marginLeft: "60px" }} src={topBarImg} alt="" />
            </td>
          </tr>
        </tbody>
      </table>
      {pyiLocalStorage.getCurrentUser() ? <MenuBar /> : null}
    </>
  )
}
export default TopBar
