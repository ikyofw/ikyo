## Function

Configure a unique UUID (Universally Unique Identifier) for a page when
opening it, and each time the page sends a request to the backend, it will
include this unique UUID.

When opening a new page, send an UNLOADED_SCREEN request carrying the old UUID
to the backend.

## Implementation Method

Use useLocation to determine when the page address has changed and send a
UNLOADED_SCREEN request to the backend with the old UUID.

    
    
    const location = useLocation()
    React.useEffect(() => {
      unloadScreen()
    }, [location])
    
    const unloadScreen = async () => {
      try {
        // When opening a new page send a request to the backend with the path and SUUID information of the old page
        const oldPath = localStorage.getItem("__PYI_OLD_PATH__")
        const screenIDs = localStorage.getItem("__PYI_SCREEN_IDS__").split(",")
        const paths = localStorage.getItem("__PYI_PATHS__").split(",")
        if (oldPath) {
          localStorage.removeItem("__PYI_OLD_PATH__")
        }
        let oldScreenID, newScreenID
        paths.map((path1, index) => {
          // YL, 2023-03-21 bugfix - start
          if (oldPath) {
            if (path1.toLocaleLowerCase() === oldPath.slice(1).toLocaleLowerCase()) {
              oldScreenID = screenIDs[index]
            }
          }
          if (location.pathname) {
            if (path1.toLocaleLowerCase() === location.pathname.slice(1).toLocaleLowerCase()) {
              newScreenID = screenIDs[index]
            }
          }
          // YL, 2023-03-21 - end
        })
        var data = { oldScreenID: oldScreenID, newScreenID: newScreenID }
        const oldSUUID = sessionStorage.getItem("SUUID")
    
        if (oldScreenID) {
          HttpPost("/api/" + oldScreenID + "/UNLOADED_SCREEN" + (oldSUUID ? "?SUUID=" + oldSUUID : ""), JSON.stringify(data))
            .then((response) => response.json())
            .then((result) => {})
        }
      } catch (error) {
        pyiLogger.error("Unload screen failed: " + error, true)
      }
    }
    

The UUID of the page is carried in the return of the initScreen request made
by the screenRender component to the backend.

Save this UUID and pass it to the screenRender component's descendant
component using the useContext.

    
    
    const pyiGlobal = pyiLocalStorage.globalParams
    const ScreenRender = (props) => {
      const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
      const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)
    
      const screenRef = useRef<any>(null)
      const [fgNames, setFgNames] = useState([])
      const [SUUID, setSUUID] = useState("")
    
      React.useEffect(() => {
        refreshList()
      }, []) // page refresh
    
      ...
    
      const refreshList = async () => {
        try {
          const params = sessionStorage.getItem(pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME)
            ? sessionStorage.getItem(pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME)
            : null
          await HttpGet("/api/" + props.screenID + "/initScreen" + (params ? "?" + pyiGlobal.OPEN_SCREEN_PARAM_KEY_NAME + "=" + params : ""))
            .then((response) => {
              if (response.ok) return response.json()
              throw response
            })
            .then((result) => {
              let screenDfn = getScreenDfn(result, false)
              if (!screenDfn) {
                pyiLogger.error("get initScreen error, please check.", true)
                return
              } else {
                setFgNames(screenDfn["fieldGroupNames"])
                sessionStorage.setItem("SUUID", screenDfn["SUUID"])
                setSUUID(screenDfn["SUUID"])
              }
            })
        } catch (error) {
          pyiLogger.error("Load screen failed: " + error, true)
        }
      }
    
      if (fgNames.length !== 0 && SUUID !== "") {
        return (
          <suuidContext.Provider value={{ SUUID }}>
            <Screen ref={screenRef} fgNames={fgNames} screenID={props.screenID} />
          </suuidContext.Provider>
        )
      } else {
        return null
      }
    }
    
    export default ScreenRender
    

Handles all requests to the backend in the http component, adding the UUID to
the request if it is saved.

    
    
    export function useHttp(type: string) {
      const conText = useContext(componentContext)
    
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
      } else ...
    

