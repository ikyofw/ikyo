## Functionality

Get the user and token of the page.

## Request

  * URL: 
    *           "/api/auth"
        

  

  * Method: Get

  

  * URL Parameters: None

  

  * Data Parameters: None

## Response

#### Response Data

  * token(string): Get page token. Each subsequent request to the backend from this page will include this token in the url.

  

  * user(string): Get the user who opened the page.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": {
            "token": "30463dd5b667fa69ec2f2c09464d7536",
            "user": "dexiang"
        },
        "messages": [
            {
                "type": "info",
                "message": "Login already."
            }
        ]
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

