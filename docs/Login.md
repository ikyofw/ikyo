## Functionality

User login.

## Request

  * URL: 
    *           "/api/auth"
        

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: ForData with username and password

## Response

#### Response Data

  * token(string): Get page token. Each subsequent request to the backend from this page will include this token in the url.

  

  * user(string， nullable): Get the user who opened the page.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": null,
        "messages": [
            {
                "type": "info",
                "message": "Logout."
            }
        ]
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

