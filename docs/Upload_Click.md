## Functionality

Triggered by clicking the button with type normal (default type) in simpleFg
or toolbar. Refresh the whole page after clicking.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column Event Handler. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: PostNoHeader

  

  * URL Parameters: None

  

  * Data Parameters: FormData object holding the parameters of the uploaded file.

## Response

### Response Data

Don't pay attention to the response data, just refresh the whole page when the
response code is normal

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

