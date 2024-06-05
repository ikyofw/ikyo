## Attribute

  * caption(string): The caption for SearchFg or SimpleFg.

  

  * name(string): The unique name for the SearchFg or SimpleFg.(No duplicate names allowed within the page)

  

  * type(string): The type of the fields group. 
    * All possible values:
    *             search: SearchFg.
            fields: SimpleFg.
        

  

  * data(object): The initial data populated in the SearchFg or SimpleFg.

  

  * dataUrl(string): If data doesn't exist it will try to request the dataUrl to get the data again.(Currently abandoned)

  

  * editable(boolean): Controls whether the user can edit the SearchFg or SimpleFg.
  * visible(boolean): Controls whether the SearchFg or SimpleFg is visible to the user.

  

  * cols(integer, nullable): Controls how many fields are displayed on each line of SearchFg or SimpleFg.

  

  * sortNewRows(boolean, nullable): This field is not valid in SearchFg and SimpleFg.

  

  * fields(array of objects): Each representing a sub-field within the TableFg. **Please refer to the information for the specific content of each object**

  

  * pageType(string, nullable): This field is not valid in SearchFg or SimpleFg.
  * pageSize(integer, nullable): This field is not valid in SearchFg or SimpleFg.

  

  * rmk(string, nullable): This field allows for any remarks or additional comments related to a field in SearchFg or SimpleFg.

  

  * beforeDisplayAdapter(string, nullable): This field is not valid in SearchFg or SimpleFg.

  

  * outerLayoutParams(string, nullable): Set the position of the component in the grid layout.

  

  * maxFieldsNum(integer): The maximum number of sub-fields in the SearchFg or SimpleFg.

## Example

    
    
    {
      "caption": null,
      "name": "schFg",
      "type": "search",
      "data": {
        "teamField": null,
        "memberField": null,
        "dtField": "2023-08-05"
      },
      "dataUrl": "/api/tsinput/getSchRc?GETDATAREQUEST=2023080220230802090603106247",
      "editable": true,
      "visible": true,
      "cols": 4,
      "sortNewRows": false,
      "fields": [
        // refer to Reference 
      ],
      "pageType": null,
      "pageSize": null,
      "rmk": null,
      "beforeDisplayAdapter": null,
      "outerLayoutParams": "{'grid-area': '1 / 1 / 12 / 2'}",
      "maxFieldsNum": 4
    }
    

## Reference

[Fields](Fields.md "Fields")

