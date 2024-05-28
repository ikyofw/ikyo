## Functionality

Get the parameters of the dialog from the backend.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column widget parameters. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: 
    * If button in table: 
      * Format is eventHandler: 
        *                 {
                  "id": "6526",  // the id of the row where the clicked button is located
                  "row": { 
                    "id":"6526",
                    "__STT_":None
                    "seq":"13"
                    "field_nm":"fRemarkField"
                    "caption":"Remark"
                    ...
                  }   // the iten of row where the clicked button is located
                }
                

      * The format is eventHandler(fieldGroupName): pass the data of the desired column to the backend via fieldGroupName. 
        * Example when saveDtl(appHdrFg)
        *                 {
                  "id": "6526",
                  "row": ...,
                  "appHdrFg": {
                    "id": "",
                    "year": "2023",
                    "applicant": "dexiang",
                    "approver": "david",
                    "leaveType": "EL",
                    "rmk": ""
                  },
                }
                

    * Else button not in table: 
      * Format is eventHandler: Data Parameters is null.
      * Format is eventHandler(fieldGroupName): Pass the data of the required components to the backend by fieldGroupName. 
        * Example when preview(appHdrFg, leaveDateFg)
        *                 {
                  "appHdrFg": {
                    "id": "",
                    "year": "2023",
                    "applicant": "dexiang",
                    "approver": "david",
                    "leaveType": "EL",
                    "rmk": ""
                  },
                  "leaveDateFg": {
                    "attr": [
                      "__STT_",
                      "__KEY_",
                      "date_from",
                      "date_to",
                      "duration",
                      "rmk"
                    ],
                    "data": [
                      [
                        "+",
                        null,
                        "2023-08-04",
                        "2023-08-05",
                        "FD",
                        null
                      ]
                    ]
                  }
                }
                

## Response

### Response Data

  * title(string, nullable): Title of the dialog.

  

  * dialogMessage(string): Dialog body message.

### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": {
            "dialogMessage": "Are you sure to delete the tasks corresponding to these task numbers: \n\n00001: 20 \n",
            "title": "Test diaolg title"
        },
        "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

