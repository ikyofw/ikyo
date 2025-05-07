import JSEncrypt from "jsencrypt"
import { ChangeEvent, useEffect, useRef, useState } from "react"
import cookie from "react-cookies"
import * as Loading from "../components/Loading"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"

const pyiGlobal = pyiLocalStorage.globalParams
const MENU_ACTION = pyiGlobal.COOKIE_MENU_ACTION

const Login = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const HttpPostNoHeader = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST_NO_HEADER)

  const [userName, setUserName] = useState<string>("")
  const [userPwd, setUserPwd] = useState<string>("")
  const lastSelectedMenu = cookie.load(MENU_ACTION)
  const [publicKey, setPublicKey] = useState<string>("")
  const [errorMessage, setErrorMessage] = useState<string>("\u00A0")

  const inputRef1 = useRef(null)
  const inputRef2 = useRef(null)

  useEffect(() => {
    HttpGet("/api/auth")
      .then((response) => response.json())
      .then((result) => {
        if (Number(result.code) == 1) {
          window.location.href = lastSelectedMenu ? lastSelectedMenu : "/home"
        } else {
          setPublicKey(result.data[pyiGlobal.RSA_PUBLIC_KEY])
        }
      })
  }, [])

  const onChangeUserName = (e: ChangeEvent<HTMLInputElement>) => {
    setUserName(e.target.value)
  }
  const onChangeUserPwd = (e: ChangeEvent<HTMLInputElement>) => {
    setUserPwd(e.target.value)
  }

  const login = async () => {
    Loading.show()
    try {
      // RSA encryption
      let _u = userName
      let _p = userPwd
      if (publicKey && publicKey != "") {
        _u = "" + encrypt(userName)
        _p = "" + encrypt(userPwd)
      }
      let formData = new FormData()
      formData.append("username", _u)
      formData.append("password", _p)
      await HttpPostNoHeader("/api/auth", formData)
        .then((response) => response.json())
        .then((result) => {
          if (Number(result.code) === 100001) {
            pyiLocalStorage.clearStore()
            window.location.href = "/login"
            sysUtil.showMessage(result.messages)
          } else if (result.code === 1) {
            pyiLocalStorage.setCurrentUser(userName)
            pyiLocalStorage.setToken(result.data.token)
            window.location.href = lastSelectedMenu ? lastSelectedMenu : "/home"
          } else if (result.code === 0) {
            if (result.messages && result.messages.length > 0) {
              setErrorMessage(result.messages[0]?.message)
            }
          }
        })
    } catch (error) {
      console.error("Login error:", error)
    } finally {
      Loading.remove()
    }
  }

  const encrypt = (text) => {
    const encrypt = new JSEncrypt()
    encrypt.setPublicKey(publicKey)
    const encrypted = encrypt.encrypt(text)
    return encrypted
  }

  const keyUp = (e) => {
    if (e.keyCode === 13) {
      if (userName && userPwd) {
        login()
      } else if (e.target === inputRef1.current) {
        inputRef2.current.focus()
      } else if (e.target === inputRef2.current) {
        inputRef1.current.focus()
      }
    }
  }

  return (
    <div className="div_center">
      <table style={{ margin: "0 auto" }}>
        <tbody>
          <tr>
            <td id="lr">
              <fieldset>
                <h3>Log In</h3>
                <form name="loginForm" id="loginForm" method="POST" action="">
                  <table style={{ margin: "10px" }}>
                    <tbody>
                      <tr>
                        <td colSpan={2}>
                          <label id="__msg" style={{ color: "red" }}>
                            {errorMessage}
                          </label>
                        </td>
                      </tr>
                      <tr>
                        <td height="5px" colSpan={2}></td>
                      </tr>
                      <tr>
                        <td>
                          <label htmlFor="__u" style={{ paddingRight: "10px" }}>
                            Username *
                          </label>
                        </td>
                        <td>
                          <input
                            ref={inputRef1}
                            type="text"
                            name="__u"
                            id="__u"
                            value={userName}
                            onChange={onChangeUserName}
                            onKeyUp={keyUp}
                            autoComplete="username"
                          />
                        </td>
                      </tr>
                      <tr>
                        <td height="5px"></td>
                      </tr>
                      <tr>
                        <td>
                          <label htmlFor="__p" style={{ paddingRight: "10px" }}>
                            Password *
                          </label>
                        </td>
                        <td>
                          <input
                            ref={inputRef2}
                            type="password"
                            name="__p"
                            id="__p"
                            value={userPwd}
                            onChange={onChangeUserPwd}
                            onKeyUp={keyUp}
                            autoComplete="current-password"
                          />
                        </td>
                      </tr>
                      <tr>
                        <td height="10px"></td>
                      </tr>
                      <tr>
                        <td colSpan={2} style={{ textAlign: "right" }}>
                          <input id="__login" type="button" style={{ padding: "0.2em 1em" }} value="Log In" onClick={login} onKeyUp={keyUp} />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </form>
              </fieldset>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

export default Login
