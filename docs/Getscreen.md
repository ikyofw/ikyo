## Functionality

Get the names of all the components displayed on the page, the unique UUID for
this page.

## Request

  * URL: 
    *             '/api/' + screenID + '/getScreen'
            // screenID is a unique id for each page
        

  

  * Method: Get

  

  * URL Parameters: None

  

  * Data Parameters: None

## Response

#### Response Data

  * viewID(string): Provides a unique identifier for each page.

  

  * viewTitle(string): The title of page.

  

  * viewDesc(string): The Description of page.

  

  * layoutType(number): The type of layout used in page. 
    * All possible values:
    *             1: grid
        

  * layoutParams(string): Any parameters that are needed for the layout.If no parameter is set, it will be displayed in the default way from top to bottom. 
    * Example:
    *         {
          "layoutParams": {
            "display": "grid",
            "grid-template-columns": "1fr 1fr",
            "grid-template-rows": "auto",
            "grid-gap": "5px",
            "grid-auto-flow": "column"
          }
        }
        

  

  * helpUrl(string): The url to open the help page. 
    * If helpUrl is not null and does not exist "?", helpUrl is the url of get HTML help content.
    * If helpUrl is not null and exist "?". The content before the "?" is the url of get HTML help content. The content after the "docType" is the url of get PDF help content.

  

  * autoRefreshInterval(number): The interval in which the page automatically refreshes.

  * autoRefreshAction(string): The action to be performed when the view is automatically refreshed. // TODO: No relevant code on the front end at the moment

  

  * editable(boolen): A boolean value (true or false) indicating whether the page is editable.

  

  * rmk(string): Remarks or any other extra information related to the view.

  

  * See references for others. 
    * This other part of the attribute is dynamically changed based on the content of the page. Each field group in the page corresponds to one attribute, the key of the new attribute is filed group name, and the value is the parameter of the new filedgroup.
    * See reference for details of the parameters

#### Other

  * code(number): Represents the status code of the request. 
    * All possible values:
    *             0: False, Failed.
            1: True, Success.
            2: System error.
            100001: Error: Please login first.
            100002: Error: Permission deny.
        

  

  * messages(array of objects): Each object contains: 
    * type(string): Indicates the type of the message. 
      * All possible values:
      *                 debug
                info
                warning
                error
                fatal
                exception
            

    * message(string): Provides the content of the message.

  

  * resources(array of objects, nullable): Static resources for the page. Each object contains: 
    * properties(boject, nullable): Properties of static files.
    * resource(string): Addresses of static files.

## Example

    
    
    {
      "code": 1,
      "data": {
        "code": 1,
        "data": {
          "autoRefreshAction": null,
          "autoRefreshInterval": null,
          "editable": true,
          "helpUrl": "/api/help/screen/task003",
          "layoutParams": null,
          "layoutType": 1,
          "rmk": null,
          "viewDesc": "Task Type",
          "viewID": "Task003",
          "viewTitle": "Task Type"
          // Parameters of each component refer to Reference 
        },
        "messages": []
      },
      "logLevel": "debug",
      "messages": [
        {
          "type": "info",
          "message": "test message"
        }
      ],
      "resources": [
        {
          "properties": {
            "title": "es"
          },
          "resource": "static/wci1/css/wci/es-v3.css"
        }
      ]
    }
    

## Reference

[SearchFg and SimpleFg](SearchFg_and_SimpleFg.md "SearchFg and SimpleFg")

[TableFg](TableFg.md "TableFg")

[ToolBar](ToolBar.md "ToolBar")

[HTML and FileViewer](HTML_and_FileViewer.md "HTML and FileViewer")

