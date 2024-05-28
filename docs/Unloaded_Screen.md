## Functionality

Triggered when opening a new screen.

## Request

  * URL: 
    *             "/api/" + oldScreenID + "/UNLOADED_SCREEN"
            // oldScreenID is the id of the last opened screen.
        

  

  * Method: Post

  

  * URL Parameters: None 
    *           SUUID=" + oldSUUID
          // oldSUUID is the UUID of the last opened screen.
        

  

  * Data Parameters: 
    * oldScreenID(string): The id of the last opened screen.
    * newScreenID(string): The id of the new screen. 
      * Example
      *             {
                "oldScreenID": "task009",
                "newScreenID": "task009"
            }
            

## Response

### Response Data

None

### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": null,
        "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

