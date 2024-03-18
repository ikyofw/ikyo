import "./App.css"
import "../public/static/css/menu-v1.css"
import "../public/static/css/style-v2.css"

import { useEffect, useState } from "react"
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom"

import ScreenRender from "./components/ScreenRender"
import TopBar from "./components/TopBar"
import TopTitle from "./components/TopTitle"
import BeforeLogin from "./screen/BeforeLogin"
import MenuBar from "./components/MenuBar"
import Home from "./screen/Home"
import Login from "./screen/Login"
import Logout from "./screen/Logout"
import Help from "./screen/Help"
import Menu from "./screen/Menu"

import { useHttp } from "./utils/http"
import { validateResponse, showErrorMessage } from "./utils/sysUtil"
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

  const NoMatch = () => {
    const location = useLocation()
    const screenID = location.pathname.substring(1).toLowerCase()
    useEffect(() => {
      if (screenID && screenIDs.length > 0 && !screenIDs.includes(screenID)) {
        showErrorMessage("Screen doesn't not exists: [" + screenID + "]")
      }
    }, [screenID])
    return null
  }

  const resizeObserver1 = new ResizeObserver(function (entries) {
    for (var entry of entries) {
      const topScreenHeight = entry.contentRect.height
      const style = document.getElementById("top_screen_title").style
      style.top = topScreenHeight + "px"
      style.position = "sticky"
      style.zIndex = "20"
    }
  })
  const resizeObserver2 = new ResizeObserver(function (entries) {
    for (var entry of entries) {
      const topTitleHeight = entry.contentRect.height
      if (topTitleHeight > 200) {
        const fixedTopTitleBtt = document.getElementById("sysFixedTopTitle")
        if (fixedTopTitleBtt) {
          fixedTopTitleBtt.hidden = false
          var button = document.getElementById("sysFixScrollImg")
          if (button) {
            console.log(button);
            button.click();
          }
        }
      }
    }
  })

  const topScreen = document.getElementById("top_screen")
  const topTitle = document.getElementById("top_screen_title")
  if (topScreen) {
    resizeObserver1.observe(topScreen)
  }
  if (topTitle) {
    resizeObserver2.observe(topTitle)
  }

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
            <div className="top_screen" id="top_screen">
              <TopBar />
              {pyiLocalStorage.getCurrentUser() ? <MenuBar /> : null}
            </div>
            <div className="top_screen_title" id="top_screen_title">
              <TopTitle />
            </div>
            <div className="main_screen" id="main_screen">
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
                  <Route path="*" element={<NoMatch />} />
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
