## Attribute

  * caption(string): The title or caption for the table.

  

  * name(string): The unique name for the table.(No duplicate names allowed within the page)

  

  * type(string): The type of the fields group. 
    * All possible values:
    *             table: A controlable table.
            resultTable: A non-editable tables.
        

  

  * data(array): The initial data populated in the tableFg.

  

  * dataUrl(string): If data doesn't exist it will try to request the dataUrl to get the data again. If the form is server-side paged, it will also get the data for a particular page based on this dataUrl.

  

  * editable(boolean): Controls whether the user can edit the tableFg.
  * deletable(boolean): Controls whether a row of a tableFgcan be deleted.
  * visible(boolean): Controls whether the tableFg is visible to the user.
  * insertable(boolean): Controls whether a new row can be added to the tableFg.

  

  * selectionMode(string): Controls whether a form is selectable, effective only when the table is resultTable. 
    * All possible values:
    *             Single: Allows selection of one row in the table.
            Multiple: Allows selection of multiple rows.
            None: Not selectable.
        

  

  * cols(integer): This field is not valid in tableFg.

  

  * showRowNo(boolean): Controls whether to display the leftmost column of the table that displays the row number.

  

  * sortNewRows(boolean): Controls whether new rows are sorted when double-clicking a table header to sort the table by the contents of a column.

  

  * fields(array): This is an array of objects, each representing a sub-field within the TableFg. **Please refer to the information for the specific content of each object**

  

  * pageType(string, nullable): Setting the paging type of TableFg. 
    * All possible values:
    *             client
            server
        

    * If it's server-side paging, the dataUrl will be re-requested for the page content on each page turn. Please refer to Reference
  * pageSize(integer, nullable): Setting the number of rows per page for table paging.

  

  * style(array): Styling some cells in a table 
    * row(integer, nullable): The id of the row in which the cell to be styled is located.
    * col(string, nullable): The name of the column in which the cell to be styled is located.
    * style(object): style.

  

  * rmk(string, nullable): This field allows for any remarks or additional comments related to the TableFg.

  

  * beforeDisplayAdapter(string, nullable): Triggered before the table is displayed. This allows direct modification of the DOM, style modifications, or making certain DOM elements not display. Because this method is not secure enough and requires direct writing of front-end manipulation of DOM code in the backend, it has been basically abandoned!

  

  * outerLayoutParams(object, nullable): Set the position of the component in the grid layout.

  

  * maxFieldsNum(integer): This field is not valid in tableFg.

## Example

    
    
    {
      "caption": "dexiang from 2023-07-23 To 2023-08-05",
      "name": "workFg",
      "type": "table",
      "data": [
        {
          "act_id": 302,
          "act_nm": "Bug fixing",
          "act_tp_with_id": "P302@1936",
          "cre_dt": "2023-08-03 15:03:19",
          "cre_usr_id": 1013,
          "d12_dt": "2023-08-03 00:00:00",
          "d12_id": 281717,
          "d12_qty": 12,
          "d12_version_no": 0,
          "dlv": "Task No. 115: 1213",
          "id": 37499,
          "mod_dt": null,
          "mod_usr_id": null,
          "prj_id": 57,
          "prj_no": "00001",
          "row_no": 1,
          "task_dsc": "1213",
          "task_id": 1936,
          "task_no": 115,
          "tp": "P",
          "usr_id": 1013,
          "version_no": 0
        },
        {
          ...
        },
        ...
      ],
      "dataUrl": "/api/tsinput/getWorkRcs?GETDATAREQUEST=2023080320230803094656711209",
      "editable": true,
      "deletable": true,
      "visible": true,
      "insertable": false,
      "cols": null,
      "sortNewRows": false,
      "fields": [
        // refer to Reference 
      ],
      "pageType": "client",
      "pageSize": "20",
      "rmk": null,
      "beforeDisplayAdapter": null,
      "showRowNo": true,
      "style": [
        {
            "col": "id",
            "row": 1,
            "style": {
                "backgroundColor": "#66CCFF"
            }
        },
        {
            "row": 5,
            "style": {
                "height": "50px"
            }
        },
        {
            "col": "rmk2",
            "style": {
                "fontWeight": "bold"
            }
        }
      ],
      "outerLayoutParams": null,
      "maxFieldsNum": 17,
      "pluginParams": []
    }
    

## Reference

[Fields](Fields.md "Fields")

