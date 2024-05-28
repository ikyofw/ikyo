## Functionality

Triggered by clicking the button with type normal (default type) in simpleFg
or toolbar. Refresh the whole page after clicking.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column Event Handler. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: Post

  

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
      * Format is eventHandler: Data Parameters is null.
      * Format is eventHandler(fieldGroupName): Pass the data of the required components to the backend by fieldGroupName. 
        * Example when saveDtl(logDtlFg, logDtlFg2, msgFg)
        *                 {
                  "logDtlFg": {
                    "id": "",
                    "no": "0",
                    "master_no": "",
                    "prj_id": "",
                    "mod_id": "",
                    "expect_hr": "",
                    "remains_hr": "",
                    "assign_to": "",
                    "task_seq": "",
                    "task_sts": ""
                  },
                  "logDtlFg2": {
                    "id": "",
                    "dsc": ""
                  },
                  "msgFg": {
                    "attr": [
                      "__STT_",
                      "__KEY_",
                      "cre_dt",
                      "_cre_usr_nm",
                      "sts_id",
                      "msg"
                    ],
                    "data": [
                      [
                        "+",
                        null,
                        "2023-08-04 14:57:34",
                        "dexiang",
                        null,
                        null
                      ]
                    ]
                  }
                }
                

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

