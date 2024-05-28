## Attribute

  * caption(string): The title or caption for the bar.

  

  * name(string): The unique name for the bar.(No duplicate names allowed within the page)

  

  * type(string): The type of the fields group. 
    * All possible values:
    *             iconBar: A set of widgets for search data from server side.
        

  

  * icons(array): This is an array of objects, each representing a icon within the bar. 
    * caption(string): The caption for the icon.
    * name(string): The unique name for the icon.
    * tooltip(string, nullable): This field is not valid in ToolBar.
    * enable(boolean): Whether the button is allowed to be clicked.
    * visible(booleam): This field is not valid in ToolBar.
    * eventHandler(string): The name of the method that initiates a request to the backend by clicking on the button of the ToolBar.
    * eventHandlerParameter(object): Additional parameters for the event handler. 
      * fieldGroups(array): A list holding the names of the field groups. The event handler passes the data for the specified filed groups to the backend based on this list.
    * widget(string): The type of widget to be used for the field. 
      * All possible values:
      *                 IconAndText: The icons in toolbar.
            

      * widgetParameter(object): Additional parameters for the widget. **Please refer to Reference for the corresponding parameters of different widgets.**

  

  * outerLayoutParams(object, nullable): Set the position of the component in the grid layout.

  

  * maxFieldsNum(integer): This field is not valid in tableFg.

## Example

    
    
    {
        "name": "delToolbar",
        "type": "iconBar",
        "maxFieldsNum": 1,
        "icons": [
            {
                "name": "bttDelete",
                "caption": "Delete",
                "enable": false,
                "visible": true,
                "widget": "IconAndText",
                "widgetParameter": {
                    // refer to Reference 
                },
                "eventHandler": "/api/task009/delete",
                "eventHandlerParameter": {
                    "fieldGroups": [
                        "intLogFg"
                    ]
                },
                "tooltip": null
            }
        ],
        "outerLayoutParams": null
    }
    

## Reference

[Widget Parameters](Widget_Parameters.md "Widget Parameters")

[Fields](Fields.md "Fields")

