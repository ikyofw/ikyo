## Functionality

When getScreen gets the entire page definition, if it doesn't get the content
of the html component, the html component will try to continue requesting html
content from the backend based on the dataUrl.

## Request

  * URL: 
    * The content of the dataUrl attribute in the parameters obtained by the html component.
    * The specific parameter structure can be found in the html section of the [Widget Parameters] reference material.

  

  * Method: Get

  

  * URL Parameters: None

  

  * Data Parameters: None

## Response

#### Response Data

Display content of html components.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
      "code": 1,
      "data": "<div style='color: #606060;padding-top: 10px;padding-left: 10px'>Created at: 2014-07-24 10:05:23 by dexiang;&nbsp;&nbsp;&nbsp;Modified at: 2023-07-24 15:30:24 by dexiang;&nbsp;&nbsp;&nbsp;Assigner: david.</div>",
      "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

