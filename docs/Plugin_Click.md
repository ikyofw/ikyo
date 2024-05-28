## Functionality

Requests triggered by clicking an icon in the plugin column of the table.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column widget parameters. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: 
    *           { EditIndexField: ID }
          // ID is the id of the row where the clicked plugin column is located
        

## Response

### Response Data

  * OPEN_SCREEN(string, nullable): Save the new screen name. Click plugin icon will jump to new screen. If this parameter is not present, the page will be refreshed when clicked.

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

