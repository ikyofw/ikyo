import { useEffect } from "react"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"
import { useHttp } from "../utils/http"

const TopBar = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const topBarImg = pyiLocalStorage.globalParams.PUBLIC_URL + "images/IUI.png"

  useEffect(() => {
    checkLogin()
  }, [])

  const checkLogin = async () => {
    const response = (await HttpGet("/api/auth")) as Response
    if (!response || typeof response.json !== "function") {
      console.error("No valid response from server.")
      return
    }

    const result = await response.json()
    if (Number(result.code) === 1) {
      pyiLocalStorage.setCurrentUser(result.data.user)
      pyiLocalStorage.setToken(result.data.token)
    } else if (!window.location.href.endsWith("login")) {
      sysUtil.validateResponse(result, false)
    }
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
    </>
  )
}
export default TopBar
