## Function

The purpose of this component is to create a page, by entering different
screenID to get different page contents from different addresses in the
backend, and then create different pages.

## Pre-processing

Pass in the screenID of the page to create, assuming the corresponding page is
configured in the background.

First, get all the Field Group Names saved as "screenDfn" for the page based
on the screenID passed in. Then, pass screenDfn and screenID together to the
screen component to create the page.

    
    
    import React, { useRef, useState } from "react"
    import { HttpGet, HttpPost } from "../utils/http"
    import Screen from "../components/Screen"
    import { showErrorMessage, getScreenDfn } from "./sysUtil"
    
    const ScreenRender = (props) => {
      const screenRef = useRef<any>(null)
    
      const [screenDfn, setScreenDfn] = useState([])
    
      React.useEffect(() => {
        refreshList()
      }, []) // page refresh
    
      const refreshList = async () => {
        try {
          await HttpGet("/api/" + props.screenID + "/getScreenFgNm")
            .then((response) => response.json())
            .then((result) => {
              let screenDfn_0 = getScreenDfn(result)
              if (!screenDfn_0) {
                showErrorMessage("get getScreenFgNm error, please check.")
                return
              }
              let screenDfnKeys = []
              for (let key of Object.keys(screenDfn_0)) {
                if (screenDfn_0[key].type) {
                  screenDfnKeys.push(key)
                }
              }
              setScreenDfn(screenDfnKeys)
            })
        } catch (error) {
          console.log("Load screen failed: " + error)
        }
      }
    
      return (
        <>
          {screenDfn.length !== 0 ? (
            <Screen
              ref={screenRef}
              screenDfn={screenDfn}
              screenID={props.screenID}
            />
          ) : null}
        </>
      )
    }
    
    export default ScreenRender
    

## Component Implementation Method

### First we need a skeleton: pass in the ID and Dfn, pass out all the refs of
the page, return the page

Create the corresponding useRef based on the screenDfn passed in.

    
    
    interface IScreenBox {
      ref: any
      screenDfn: any
      screenID: any
    }
    
    const Screen: React.FC<IScreenBox> = forwardRef((props, ref: Ref<any>) => {
      let refs: { [key: string]: React.MutableRefObject<any> } = {}
      const _useRef = useRef
      props.screenDfn.map((screenName: string) => {
        refs[screenName] = _useRef(null)
      })
    
      useImperativeHandle(ref, () => {
        // send data to parent component
        return {
          refs,
        }
      })
    
      xxxx // Main part
    
      return(
        <>
          <searchFg xxx >
          <TableFg xxx > 
          <SimpleFg xxx >
          <ToolBar xxx > 
        <>
    )}
    

### Then we fetch and process the data from the backend based on the screenID

setScreenJson holds the order and contents of the all search bar, button bar
and individual forms in this page;

setScreenPlugin save information for all plug-in columns in each table.

    
    
    const [screenJson, setScreenJson] = useState(Object)
    const [screenPlugin, setScreenPlugin] = useState(Object)
    
    React.useEffect(() => {
      refreshList()
    }, []) // page refresh
    
    // set page data
    const refreshList = async () => {
      Loading.show()
      // get table data
      try {
        await HttpGet("/api/" + props.screenID + "/getScreen")
          .then((response) => response.json())
          .then((result) => {
            let screenDfn_0 = getScreenDfn(result)
            if (!screenDfn_0) {
              showErrorMessage("get screenDfn error, please check.")
              return
            }
            let screenDfnDic = {}
            let screenPlugin = {}
            props.screenDfn.map((screenName: string) => {
              if (screenDfn_0[screenName] && screenDfn_0[screenName].type === pyiGlobal.TABLE_TYPE) {
                const pluginParams = getPluginParams(screenDfn_0[screenName])
                screenPlugin[screenName] = pluginParams
                screenDfn_0[screenName]["pluginParams"] = pluginParams
              }
              screenDfnDic[screenName] = screenDfn_0[screenName]
            })
            setScreenJson(screenDfnDic)
            setScreenPlugin(screenPlugin)
          })
      } catch (error) {
        console.log("Load screen failed: " + error)
      } finally {
        Loading.remove()
      }
    }
    
    function getPluginParams(screenDfn: any) {
      const fields = screenDfn.fields
      let pluginParams = []
      for (let i = fields.length - 1; i >= 0; i--) {
        if (fields[i].widget === "plugin") {
          const field = fields.pop()
          pluginParams.push(field)
        }
      }
      pluginParams.reverse()
      return pluginParams
    }
    

### Create the click events for the search bar

    
    
    const searchBarIconClick = async (e: any) => {
      Loading.show()
      const eventHandler = e.eventHandler
      let data = {}
      data[e.screenName] = refs[e.screenName].current.formDataToJson()
      try {
        await HttpPost(eventHandler, JSON.stringify(data))
          .then((response) => response.json())
          .then((result) => {
            if (validateResponse(result)) {
              refreshList()
            }
          })
      } catch (error) {
        console.log(eventHandler + " error: " + error)
      } finally {
        Loading.remove()
      }
    }
    

### Create the click events for the action bar

Different data is passed to the backend depending on the eventHandlerParameter
set for each button click event, and depending on the type of form passed.

It is important to note that for the click event of the button bar, the name
of each key in the dictionary data passed back to the backend needs to
correspond to the name of the form.

    
    
    const btnClick = async (e: any) => {
      Loading.show()
      const eventHandler = e.eventHandler[0]
      const eventHandlerParameter = e.eventHandler[1].fieldgroups
      let data = {}
      if (eventHandlerParameter && eventHandlerParameter.length <= 0) {
        data = {}
      } else if (eventHandlerParameter[0] === "*") {
        props.screenDfn.map((screenName: string) => {
          data[screenName] = createDatabyScreenName(screenName, screenJson, refs)
        })
      } else {
        eventHandlerParameter.map((screenName: string) => {
          data[screenName] = createDatabyScreenName(screenName, screenJson, refs)
        })
      } 
    
      try {
        await HttpPost(eventHandler, JSON.stringify(data))
          .then((response) => response.json())
          .then((result) => {
            if (validateResponse(result)) {
              refreshList()
            }
          })
      } catch (error) {
        console.log(eventHandler + " error: " + error)
      } finally {
        Loading.remove()
      }
    }
    
    function createDatabyScreenName(screenName: string, screenJson: [], refs: any) {
      let data
      if (screenJson[screenName] && refs[screenName].current) {
        if (screenJson[screenName].type === pyiGlobal.TABLE_TYPE) {
          data = refs[screenName].current.data
        } else if (screenJson[screenName].type === pyiGlobal.TABLE_TYPE_RESULT) {
          data = refs[screenName].current.data
        } else if (screenJson[screenName].type === pyiGlobal.SIMPLE_TYPE) {
          data = refs[screenName].current.formDataToJson()
        }
      }
      return data
    }
    

### Then Create button click events for each plugin column

Create click events based on the previously saved plugin information for each
list.

    
    
    const [screenPluginLists, setScreenPluginLists] = useState(Object)
    
    React.useEffect(() => {
      if (JSON.stringify(screenPlugin) === "{}") {
        return
      }
      let screenPluginLists = {}
      props.screenDfn.map((screenName: string) => {
        if (
          screenJson[screenName] &&
          screenJson[screenName].type === pyiGlobal.TABLE_TYPE &&
          screenPlugin[screenName] &&
          screenPlugin[screenName].length !== 0
        ) {
          let pluginCallBack = []
          let pluginLists = []
          screenPlugin[screenName].map((plugin: any, index: number) => {
            pluginCallBack[index] = async (id: number) => {
              Loading.show()
              try {
                await HttpPost(plugin.eventHandler, JSON.stringify({ EditIndexField: id }))
                  .then((response) => response.json())
                  .then((result) => {
                    if (validateResponse(result)) {
                      refreshList()
                    }
                  })
              } catch (error) {
                console.log(plugin.eventHandler + " error: " + error)
              } finally {
                Loading.remove()
              }
            }
            pluginLists[index] = createIconColumn(expand_icon, pluginCallBack[index], plugin.caption)
          })
          screenPluginLists[screenName] = pluginLists
        }
      })
      setScreenPluginLists(screenPluginLists)
    }, [screenPlugin])
    

### Finally, Display search fields, button fields and forms in order on the
page

screenDfn holds the order of the button bar, the search bar and the form, we
just need to iterate through them and display different content according to
the different names:

    
    
    return (
      <>
        {props.screenDfn.map((screenName: any, index: number) => (
          <>
            {screenJson[screenName] &&
            String(screenJson[screenName].type) === pyiGlobal.SEARCH_TYPE ? (
              <SearchFg
                ref={refs[screenName]}
                searchParams={screenJson[screenName]}
                clickEvent={() =>
                  searchBarIconClick({
                    screenName: screenName,
                    eventHandler: screenJson[screenName].fields[0].eventHandler,
                  })
                }
              />
            ) : null}
    
            {screenJson[screenName] &&
            String(screenJson[screenName].type).trim() === pyiGlobal.SIMPLE_TYPE ? (
              <SimpleFg ref={refs[screenName]} simpleParams={screenJson[screenName]} />
            ) : null}
    
            {screenJson[screenName] &&
            (String(screenJson[screenName].type).trim() === pyiGlobal.TABLE_TYPE ||
              String(screenJson[screenName].type).trim() === pyiGlobal.TABLE_TYPE_RESULT) ? (
              <TableFg
                ref={refs[screenName]}
                tableParams={screenJson[screenName]}
                pluginList={screenPluginLists[screenName]}
              />
            ) : null}
    
            {screenJson[screenName] &&
            String(screenJson[screenName].type) === pyiGlobal.ICON_BAR &&
            screenJson[screenName].icons ? (
              <ToolBar
                params={screenJson[screenName]}
                clickEvent={(eventHandler) => btnClick({ screenName, eventHandler })}
              />
            ) : null}
          </>
        ))}
      </>
    )
    

