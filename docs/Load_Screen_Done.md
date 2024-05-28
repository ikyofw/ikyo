## Functionality

Triggered when the screen component has finished loading.

## Request

  * URL: 
    *             "/api/" + screenID + "/`LOAD_SCREEN_DONE"
            // screenID is a unique id for each page
        

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: {}, Currently only an empty dictionary is passed to the backend.

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

