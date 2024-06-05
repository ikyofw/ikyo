## Functionality

Server-side paging, requesting dataUrl to get the content of a page in a
table.

## Request

  * URL:

The content of the dataUrl attribute in the parameters obtained by the tableFg
component.

The specific parameter structure can be found in the tableFg section of the
[Widget Parameters] reference material.

  

  * Method: Post

  

  * URL Parameters: None

  

  * Data Parameters: 
    *           { "PAGEABLE_" + name + "_pageNum": pageNum}
          // name is table name
          // pageNum is the number of pages of the data to be fetched
        

## Response

#### Response Data

  * data(array): Data of table.

  

  * style(array, nullable): Styling some cells in a table 
    * row(integer, nullable): The id of the row in which the cell to be styled is located.
    * col(string, nullable): The name of the column in which the cell to be styled is located.
    * style(object, nullable): style.
    * class(string, nullable): class. Requires that the corresponding class already exists in the front-end css file.

  

  * paginatorDataAmount(number): Total length of table data.

#### Other

Same as GetScreen, see references for details.

## Example

    
    
    {
        "code": 1,
        "data": {
            "data": [
                {
                    "id": 2032,
                    "sn": "HK00001740",
                    "sts": "cancelled",
                    "claimer_id": 1013,
                    "submit_dt": "2023-06-28 15:55:17",
                    ...
                }
            ],
            "style": [
                {
                    "row": 2032,
                    "class": "row_cancelled"
                }
            ],
            "__dataLen__": 1
        },
        "messages": []
    }
    

## Reference

[GetScreen](GetScreen.md "GetScreen")

[Widget Parameters](Widget_Parameters.md "Widget Parameters")

