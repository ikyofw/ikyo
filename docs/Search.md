## Functionality

Request new page content from the backend after clicking the search button.

## Request

  * URL: 
    *             '/api/' + screenID + eventHandler
            // screenID is a unique id for each page
            // eventHandler is setted in page screenDefinition, table Field(s), column Event Handler. Format:eventHandler or eventHandler(fieldGroupName).
        

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: The data of the component where the search icon is currently located. 
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

#### Format:eventHandler

If the eventHandler is not followed by a parameter, it means that the search
event will refresh the entire page.

Don't pay attention to what the backend of this method returns at this point.

#### Format:eventHandler(fieldGroupNames)

data(array): Displays the contents of all components that need to be updated.
Specific properties of each object in the list:

  * field group name(object): It contains the following properties: 
    * fgData(object): New data for the component corresponding to field group name.
    * fgDataStyle(object): New component tyle for the component corresponding to field group name.

### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
      "code": 1,
      "data": [
        {
          "hdrFg": {
            "fgData": [
              {
                "seq": 0,
                "id": 381,
                "cre_dt": "2023-03-22 17:24:26",
                "cre_usr_id": 1010,
                "mod_dt": null,
                ...
              },
              // ...
            ],
            "fgDataStyle": []
          }
        }
      ],
      "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

