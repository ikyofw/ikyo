## Functionality

Getting the contents of the menu bar.

## Request

  * URL: 
    *             "/api/menubar/getMenubar"
        

  

  * Method: Get

  

  * URL Parameters: Decide whether to display the secondary menu according to the current page address. 
    *             "currentPath=" + path
            // path is the address of the page where the request was made.
        

  

  * Data Parameters: None

## Response

#### Response Data

data(array): Display contents of menu bar. Specific properties of each object
in the list:

  

  * id(integer): Menu id.

  

  * title(string): Menu title.

  

  * action(string): The address that Clicking on this menu will go to.

  

  * isCurrentMenu(boolean, nullable): The menu to which the current page belongs.

  

  * subMenus(array, nullable): Pages that need to display a secondary menu will only have this attribute. Save the contents of the secondary menu. 
    * id(integer): Sub-menu id.
    * title(string): Sub-menu title.
    * action(string): The address that Clicking on this sub-menu will go to.
    * isCurrentMenu(boolean, nullable): The sub-menu to which the current page belongs.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
      "code": 1,
      "data": [
        {
          "id": 612,
          "title": "Home",
          "action": "wci1/menu?id=612"
        },
        {
          "id": 48,
          "title": "Design",
          "action": "menu"
        },
        // ...other menus...
        {
          "action": "menu",
          "id": 1519,
          "isCurrentMenu": true,
          "title": "WCI 2",
          "subMenus": [
            {
              "id": 1470,
              "title": "ES000 - ES Admin",
              "action": "es000"
            },
            {
              "id": 1471,
              "title": "ES001 - Payee",
              "action": "es001"
            },
            // ...other sub-menus...
            {
              "id": 1474,
              "title": "ES004 - New Expense Details",
              "action": "es004",
              "isCurrentMenu": true
            }
            // ...other sub-menus...
          ]
        },
        // ...other menus...
        {
          "id": -1,
          "title": "Logout",
          "action": "logout"
        }
      ],
      "messages": []
    }
    

