## Functionality

Request new page content from the backend when switching the options of a
dropdown box.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column widget parameters. Format:[onChange: eventHandler] or [onChange: eventHandler(fieldGroupName)]
        

  

  * Method: Post

  

  * URL Parameters: 
    *             "COMBOX_CHANGE_EVENT=true"
        

    * Used by the backend to parse the data passed to the backend by the comboboxOnchange request. If COMBOX_CHANGE_EVENT is true without verifying that data matches the database settings.

  

  * Data Parameters: The data of the component where the combobox is currently located. 
    * Example
    *         {
          "searchFg": {
            "schYear": "2023",
            "schOffice": "SG",
            "schTeam": "",
            "schTeamMember": "",
            "schUserStatus": "Employed",
            "schKeys": ""
          }
        }
        

## Response

### Response Data

#### Format:[onChange: eventHandler]

If the eventHandler is not followed by a parameter, it means that the
comboboxonchange event will refresh the entire page.

Don't pay attention to what the backend of this method returns at this point.

#### Format:[onChange: eventHandler(fieldGroupName)]

If eventHandler is followed by an argument, it means that the comboboxonchange
event will refresh the specified fieldgroup.

  

  * field group name(object): It contains the following properties: 
    * field name(array): The key is valid when the corresponding field widget is a combobox, and the value is an optional value for that combobox.
    * field group name(object): The key is valid when the field group name already exists on the page, and the value is new data for that field group.

### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
      "code": 1,
      "data": {
        "searchFg": {
          "schTeamMember": [
            {
              "value": 1351,
              "display": "kuang.lin"
            },
            {
              "value": 1101,
              "display": "liucui"
            }
            // ...
          ],
          "searchFg": {
            "schYear": "2023",
            "schOffice": "WH",
            // ...
          }
        }
      },
      "logLevel": "debug",
      "messages": [
        {
          "type": "info",
          "message": "test message"
        }
      ]
    }
    

  

## Reference

[GetScreen](GetScreen.md "GetScreen")

