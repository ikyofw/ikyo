## Functionality

Get the names of all the components displayed on the page, the unique UUID for
this page.

## Request

  * URL: 
    *             '/api/' + screenID + '/initScreen'
            // screenID is a unique id for each page
        

  

  * Method: Get

  

  * URL Parameters: None

  

  * Data Parameters: None

## Response

#### Response Data

  * SUUID(String): Provides a unique identifier for each page.

  

  * fieldGroupName(String array): Showing the name of each component in the page in order.

#### Other

  * code(number): Represents the status code of the request. 
    * All possible values:
    *             0: False, Failed.
            1: True, Success.
            2: System error.
            100001: Error: Please login first.
            100002: Error: Permission deny.
        

  

  * logLevel(string): Representing the log level. 
    * All possible values:
    *             debug: Show all logs
            info: Show info, warn and error log
            warn: Show warn and error log
            error: Only show error log
        

  

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

## Example

    
    
    {
      "code": 1,
      "data": {
        "SUUID": "FBr8I68mnKGpprXKjK8p",
        "fieldGroupNames": ["schFg", "missedEsFileFg", "actionBar"]
      },
      "logLevel": "debug",
      "messages": [
        {
          "type": "info",
          "message": "test message"
        }
      ]
    }
    

