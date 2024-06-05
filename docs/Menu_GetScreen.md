## Functionality

Get the contents of each table on the menu page.

## Request

  * URL: 
    *           "/api/menu/getScreen"
        

  

  * Method: Get

  

  * URL Parameters: 
    *           "last=" + lastSelectedMenuId
          // lastSelectedMenuId is the address of the last opened page.
        

  

  * Data Parameters: None

## Response

#### Response Data

Same as GetScreen, see references for details.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": null,
        "messages": [
            {
                "type": "info",
                "message": "Logout."
            }
        ]
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

