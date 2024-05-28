## Functionality

// TODO: For pd001q pages only.

## Request

  * URL:

The content of the dataUrl attribute in the parameters obtained by the
combobox component.

The specific parameter structure can be found in the combobox section of the
[Widget Parameters] reference material.

  

  * Method: POST
  * ResponseType: blob

  

  * URL Parameters: None

  

  * Data Parameters: Mark this request as being from the front-end, not from the initialization. 
    *             { useDataUrl: true }
        

## Response

#### Response Data

Display contents of combobox.(array)

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
      "code": 1,
      "data": [
        {
          "year": 2023
        },
        {
          "year": 2022
        }
      ],
      "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

[Widget Parameters](Widget_Parameters.md "Widget Parameters")

