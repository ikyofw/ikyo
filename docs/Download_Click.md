## Functionality

Triggered by clicking the button with type normal (default type) in simpleFg
or toolbar. Refresh the whole page after clicking.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column Event Handler. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: POST
  * ResponseType: blob

  

  * URL Parameters: None

  

  * Data Parameters: 
    * If button in table: 
      * Format is eventHandler: 
        *                 {
                  "id": "6526"
                  // id is the id of the row where the clicked button is located
                }
                

      * The format is eventHandler(fieldGroupName): pass the data of the desired column to the backend via fieldGroupName. 
        * Example when saveDtl(file_id)
        *                 {
                  "file_id": "6526",
                  "id": "6526"
                }
                

    * Else button not in table: 
      * Data Parameters is null.

## Response

### Response Data

// TODO: download file

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

