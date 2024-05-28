## Functionality

Get the ten most recently opened pages.

## Request

  * URL: 
    *           "/api/menu/getBackMenus"
        

  

  * Method: Get

  

  * URL Parameters:None

  

  * Data Parameters: None

## Response

#### Response Data

data(array): Display contents of menu bar. Specific properties of each object
in the list:

  

  * menu_id(integer): Menu id.

  

  * menu_caption(string): Menu Caption.

  

  * screen_nm(string): The address that Clicking on this menu will go to.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
      "code": 1,
      "data": [
        {
          "menu_id": 1446,
          "menu_caption": "Screen Definition",
          "screen_nm": "ScreenDefinition"
        },
        {
          "menu_id": 246,
          "menu_caption": "Project Resource Plan",
          "screen_nm": "PrjList"
        },
        ...
      ],
      "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

