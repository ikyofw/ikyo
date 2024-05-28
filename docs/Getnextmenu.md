## Functionality

When clicking on a directory that has subdirectories, refresh the entire page
to get the contents of the subdirectory.

## Request

  * URL: 
    *           "/api/menu/" + eventHandler 
           // eventHandler is setted in page screenDefinition, table Field(s), column widget parameters. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: 
    *           activeRow： ID
          // ID is the id of the row where the clicked plugin column is located
        

## Response

#### Response Data

None.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": null,
        "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

