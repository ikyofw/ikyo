## Fields

Fields is a list of object, and the form will set the parameters of a column
according to the properties of each object in the fields. This page describes
the format of passing parameters to each field.

### Attribute

  * name(string): The unique identifier for the field.

  

  * caption(string): The caption for the field.

  

  * tooltip(string, nullable): Set a prompt statement for the field.

  

  * datafield(string): Get the name of the database field for which the field displays content.
  * dataFormat(string, nullable): This field is not valid now.
  * dataValidation(string, nullable): This field is not valid now.

  

  * widget(string): The type of widget to be used for the field. 
    * All possible values:
    *             Label: If this field is empty, system will use Label instead.
            TextBox: Text box.
            Password: Entry password text box.
            TextArea: Line feedable text box.
            DateBox: Date box.
            ComboBox: Multiple choice one.
            ListBox: Multiple choice multiple.
            AdvancedComboBox: Combobox that allow filtering and multi-selection.
            AdvancedSelection: Select the content displayed in the Label in the dialog after clicking the button.
            CheckBox: Choose one of two or three, Available options: True, False, (None).
            Button: Button.
            File: Download file.
            IconAndText: The icons in toolbar.
            Html: HTML.
            Plugin: Currently only used for the last column of the table, open the details table.
        

  * widgetParameter(object): Additional parameters for the widget. **Please refer to Reference for the corresponding parameters of different widgets.**

  

  * editable(boolean): Controlling whether the field is editable.
  * visible(boolean): Controlling whether the field is visible.
  * required(boolean): Controlling whether the field is required.

  

  * footer(object, nullable): Set the table footer display for this field. 
    * text(string, nullable): Unchanged table footer.
    * formula(string, nullable): Table footer that changes with the content of the table according to a set rule. 
      * All possible values:
      *                 sum: Get the sum of the values in this column of the table footer
                avg: Get the average of the values in this column of the table footer
                max: Get the maximum value of the column in the footer of the table.
                min: Get the minimum value of this column in the footer of the table
                
               customizable: function (columnData){let res = ''; columnData.map((data) => { //do something }); return res}
            

    * dataType(string, nullable): Only if this setting is a date, time or datetime, the result will be formatted as a time.
    * format(string, nullable): How many decimals to retain in the final result, or formatted Date.
    * colSpan(integer, nullable): Number of cells merged to the right in the table footer.
    * style(string, nullable): Setting the style of the footer content.

  

  * style(object, nullable): Set a separate style for the field.

  

  * eventHandler(string): The name of the method that initiates a request to the backend by clicking on the button.
  * eventHandlerParameter(object): Additional parameters for the event handler. 
    * fieldGroups(array): A list holding the names of the field groups. If it is a click event in searchFg, the event handler refreshes the contents of the field groups within the sub-list; otherwise, the event handler passes the data of the specified file group to the backend based on this list.

  

  * rmk(string, nullable): This field allows for any remarks or additional comments related to the TableFg.

### Example

    
    
    {
        "caption": "f6",
        "dataField": "f6",
        "dataFormat": null,
        "dataValidation": null,
        "editable": true,
        "eventHandler": null,
        "eventHandlerParameter": {
            "fieldGroups": null
        },
        "footer": {
            "formula": "function (columnData){let res = ''; columnData.map((data) => {res += data.slice(-1)}); return res}",
            "colSpan": 2,
            "style": {
                "text-align": "right"
            }
        },
        "name": "f6",
        "required": false,
        "rmk": null,
        "style": {},
        "tooltip": null,
        "visible": true,
        "widget": "TextBox",
        "widgetParameter": {
          // refer to Reference 
        }
    }
    

### Reference

[Widget Parameters](Widget_Parameters.md "Widget Parameters")

