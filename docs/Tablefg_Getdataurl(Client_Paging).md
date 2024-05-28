## Functionality

When getScreen gets the entire page definition, if it doesn't get the table
data, the tableFg component will try to continue requesting the table data
from the backend based on the dataUrl.

This feature is largely unused at the moment.

## Request

  * URL:

The content of the dataUrl attribute in the parameters obtained by the tableFg
component.

The specific parameter structure can be found in the tableFg section of the
[Widget Parameters] reference material.

  

  * Method: Get

  

  * URL Parameters: None

  

  * Data Parameters: None

## Response

#### Response Data

Data in tables.(array)

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": [
            {
                "id": 37499,
                "cre_dt": "2023-08-03 15:03:19",
                "cre_usr_id": 1013,
                "mod_dt": null,
                "mod_usr_id": null,
                ...
            }
        ],
        "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

[Widget Parameters](Widget_Parameters.md "Widget Parameters")

