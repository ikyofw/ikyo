## Functionality

Get the ids and path of all pages that have been added to the iky_menu.

## Request

  * URL: 
    *             "/api/getRouters"
        

  

  * Method: Get

  

  * URL Parameters: None

  

  * Data Parameters: None

## Response

#### Response Data

  * paths(array): List of paths for each page.

  

  * screenIDs(array): List of screenIDs for each page.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": {
            "paths": [
                "aoi001", 
                "aoi002", 
                "beforedisplayadaptertest", 
                //...
            ],
            "screenIDs": [
                "aoi001", 
                "aoi002", 
                "beforedisplayadaptertest", 
                //...
            ]
        },
        "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

