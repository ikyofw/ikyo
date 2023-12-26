import "./App.css"
import "../public/static/css/menu-v1.css"
import "../public/static/css/style-v2.css"

import { BrowserRouter, Route, Routes } from "react-router-dom"
import TopBar from "./components/TopBar"
import TopTitle from "./components/TopTitle"
import BeforeLogin from "./screen/BeforeLogin"
import Home from "./screen/Home"
import Login from "./screen/Login"
import Logout from "./screen/Logout"

import ScreenRender from "./components/ScreenRender"
import Help from "./screen/Help"
import Menu from "./screen/Menu"
import { useHttp } from "./utils/http"
import { validateResponse } from "./utils/sysUtil"

import { useEffect, useState } from "react"
import pyiLogger from "./utils/log"
import pyiLocalStorage from "./utils/pyiLocalStorage"

function App() {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  ;(function () {
    let now = new Date().getTime()
    let unloadTime = localStorage.getItem("__PYI_UNLOAD_TIME__")
    if (unloadTime) {
      localStorage.removeItem("__PYI_UNLOAD_TIME__")
      if (now - unloadTime > 2000) {
        pyiLocalStorage.clearStore()
      }
    }
  })()
  useEffect(() => {
    window.onunload = function () {
      localStorage.setItem("__PYI_UNLOAD_TIME__", new Date().getTime())

      const path = window.location.pathname
      localStorage.setItem("__PYI_OLD_PATH__", path)
    }
    pyiLocalStorage.clearSysMsgs()
  }, [])

  const [screenIDs, setScreenIDs] = useState([])
  const [paths, setPaths] = useState([])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(async () => {
    try {
      await HttpGet("/api/getRouters")
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, false)) {
            setScreenIDs(result.data["screenIDs"])
            setPaths(result.data["paths"])

            localStorage.setItem("__PYI_SCREEN_IDS__", result.data["screenIDs"])
            localStorage.setItem("__PYI_PATHS__", result.data["paths"])
          }
        })
    } catch (error) {
      pyiLogger.error("/api/getRouters error: " + error, true)
    }
  }, [])

  return (
    <>
      {window.location.href.toLowerCase().includes("/help") ? (
        <BrowserRouter>
          <Routes>
            <Route path="/help" element={<Help />} />
          </Routes>
        </BrowserRouter>
      ) : (
        <>
          <div className="App" id="App">
            <TopBar />
            <div className="main_screen" id="main_screen">
              <TopTitle />
              <BrowserRouter>
                <Routes>
                  <Route path="/" element={<BeforeLogin />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/logout" element={<Logout />} />
                  <Route path="/home" element={<Home />} />
                  <Route path="/menu/*" element={<Menu />} />
                  {screenIDs && screenIDs.length > 0
                    ? screenIDs.map((screenID, index) => (
                        <Route path={"/" + paths[index]} element={<ScreenRender screenID={screenID} />} key={index} />
                      ))
                    : null}
                </Routes>
              </BrowserRouter>
              <div style={{ height: "10px" }}></div>
            </div>
          </div>
          <div id="pdfContainer"></div>
        </>
      )}
    </>
  )
}
export default App
