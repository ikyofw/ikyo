## Functionality

ComboBox and ListBox need exactly the same back-end content, these two are
only the front-end display of different styles.

When getScreen gets the entire page definition, if it doesn't get the combobox
display content, the combobox component will try to continue requesting
combobox content from the backend based on the dataUrl.

This feature is now largely unused.

## Request

  * URL: 
    * The content of the dataUrl attribute in the parameters obtained by the combobox component.
    * The specific parameter structure can be found in the combobox section of the [Widget Parameters] reference material.

  

  * Method: POST

  

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

