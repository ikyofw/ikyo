## Functionality

Open wci's page in pyi.

## Request

  * URL: 
    *           "/wciapi/" + param
          // If the query parameter (i.e., the parameter after the "?") contained in the current URL is empty, then look for the last "/" in the URL, and get the content after the "/" as param, else param is null.
        

  

  * Method: Get

  

  * URL Parameters: If the query parameter (i.e., the parameter after the "?") contained in the current URL is not empty, URL Parameters is the content after the "?".

  

  * Data Parameters: None

## Response

Response is the html of the wci page.

## Example

    
    
    <html>
        <div id="__systemScreenshotDiv">
        <head>
          <title>wci</title>
          ...
        </head>
        <body>
          ...
        </body>
    </html>
    

