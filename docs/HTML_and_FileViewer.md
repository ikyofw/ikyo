## Attribute

  * caption(string): The title or caption for the HTML or FileViewer.

  

  * name(string): The unique name for the HTML or FileViewer.(No duplicate names allowed within the page)

  

  * type(string): The type of the fields group. 
    * All possible values:
    *             html: Show HTML.
            viewer: Show PDF, image or 3D model.
        

  

  * data(array, nullable): The initial data populated in the HTML or FileViewer.

  

  * dataUrl(string): If data doesn't exist it will try to request the dataUrl to get the data again.

  

  * outerLayoutParams(object, nullable): Set the position of the component in the grid layout.

  

  * maxFieldsNum(integer): This field is not valid in tableFg.

## Example

    
    
    {
        "name": "pdfViewer",
        "type": "viewer",
        "caption": null,
        "data": null,
        "dataUrl": "/api/es004/getPdfViewer?GETDATAREQUEST=2023080420230804093534501948",
        "outerLayoutParams": "{'grid-area': '1 / 1 / 12 / 2'}"
    }
    

