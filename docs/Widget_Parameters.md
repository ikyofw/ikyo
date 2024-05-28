## Widget Parameters

The following discusses the different widget parameter settings depending on
the different widget.

### TextArea, Plugin, HTML and Viewer

These widgets take no parameters

### Label, TextBox

  * format(string): Set the format of the date. 
    * All possible values:
    *             0.00    // Setting the number of decimal places to be retained and makes up zeros when there are not enough bits. (Example: 1.2 -> 1.20, 1.234 -> 1.23)
            0.##    // Setting the number of decimal places to be retained. (Example: 1.2 -> 1.2, 1.234 -> 1.23)
            00,000  // Sets the use of the thousands separator and makes up zeros when there are not enough bits. (Example: 1234 -> 01,234)
            #,###   // Sets the use of the thousands separator. (Example: 1234 -> 1,234)
            0      // Round. (Example: 1.567 -> 2)
        

  * Example: 
    *         "widgetParameter": {
          "format": "#,###.00"
        }
        

### DateBox

  * format(string): Set the format of the date. 
    * All possible values:
    *             yyyy-MM-dd  (default format)
            YYYY-MM-DD HH:mm:ss
            HH:mm:ss
        

  * Example: 
    *         "widgetParameter": {
          "format": "yyyy-MM-dd"
        }
        

### ComboBox, ListBox and AdvancedComboBox

The settings are exactly the same, except that the front-end display options
are styled differently.

  

  * data(string): Optional contents of the combobox.

  

  * dataUrl(string): If data is null, get the URL of the combobox selectable content from the backend.

  

  * onChange(string, nullable): The url that initiates a request to the backend when the combobox changes.

  

  * values(string, nullable): Parsing data.

  * Example: 
    *         "widgetParameter": {
          "data": [
            {id: 1258, nm: 'Business Development'},
            {id: 1046, nm: 'Design Section 1'},
            ...
          ],
          "dataUrl": "/api/tsinput/getSchTeams?GETDATAREQUEST=2023080220230802104312246635",
          "onChange": "/api/tsinput/updateMemberValues(schFg)",
          "values": "{\"value\": \"id\", \"display\": \"nm\"}"
        }
        

### AdvancedSelection

  * data(string): Optional contents of the combobox.

  

  * dataUrl(string): If data is null, get the URL of the combobox selectable content from the backend.

  

  * values(string, nullable): Parsing data.

  

  * dialog(object, nullable): Set the parameters of the dialog in this property. 
    * dialogName(string): The name of dialog.
    * dialogTitle(string, nullable): The title of the dialog.
    * dialogMessage(string, nullable): The message of the dialog.
    * dialogBeforeDisplayEvent(string, nullable): Request the url of the dialog content from the back-end. Requesting the backend to get the content of the dialog is prioritized higher than dialogMessage.
    * uploadLabel(string, nullable): Content of the prompt before the input box when uploading a file.
    * continueNm(string, nullable): Name of contionue button in dialog. Default name is "OK".
    * cancelNm(string, nullable): Name of cancel button in dialog. Default name is "Cancel".
    * width(string, nullable): dialog width.
    * height(string, nullable): dialog height.

  

  * Example: 
    *         "widgetParameter": {
          "data": [
            {id: 1258, nm: 'Business Development'},
            {id: 1046, nm: 'Design Section 1'},
            ...
          ],
          "dataUrl": "/api/tsinput/getSchTeams?GETDATAREQUEST=2023080220230802104312246635",
          "values": "{\"value\": \"id\", \"display\": \"nm\"}"
          "dialog": "dialogBeforeDisplayEvent:postRowItem2(dtlFg);dialogName:dialog2"
        }
        

### CheckBox

  * stateNumber(integer, nullable): Setting the number of options available for a checkBox. Default is 2.

  

  * Example: 
    *         "widgetParameter": {
          "stateNumber": "3"
        }
        

### Button

  * icon(string): The name of the button's icon. Different icons can be set to be displayed depending on the actual value of this button.

  

  * type(string, nullable): Button type. 
    * All possible values:
    *             normal: Default type, direct trigger event handler. 
            upload: Button is used to upload file(s).
            download: Button is used to download file(s).
            pdf: Click on the button to display the pdf file.
        

  

  * dialog(object, nullable): Set the parameters of the dialog in this property. 
    * dialogMessage(string, nullable): The message displayed on the dialog.
    * dialogBeforeDisplayEvent(string, nullable): Request the url of the dialog content from the back-end. Requesting the backend to get the content of the dialog is prioritized higher than dialogMessage.
    * type(string, nullable): Dialog type. 
      * All possible values:
      *                 normal: Default type, Display dialogs in the format preset by the frontend. 
                html: Display the html file passed from the backend directly in the dialog.
            

    * continueNm(string, nullable): Name of contionue button in dialog. Default name is "Continue".
    * cancelNm(string, nullable): Name of cancel button in dialog. Default name is "Cancel".

  

  * Example 
    *         "widgetParameter": {
          "icon": "images/download_button.gif",
          "type": "download",
          "dialog": "dialogMessage: testMsg; dialogBeforeDisplayEvent: getMessage; type: normal"
        }
        

### IconAndText

  * icon(string): The name of the button's icon. Different icons can be set to be displayed depending on the actual value of this button.

  

  * type(string, nullable): Button type. 
    * All possible values:
    *             normal: Default type, direct trigger event handler. 
            upload: Button is used to upload file(s).
            download: Button is used to download file(s).
        

  

  * dialog(object, nullable): Set the parameters of the dialog in this property. 
    * dialogMessage(string, nullable): The message displayed on the dialog.
    * dialogBeforeDisplayEvent(string, nullable): Request the url of the dialog content from the back-end. Requesting the backend to get the content of the dialog is prioritized higher than dialogMessage.
    * uploadLabel(string, nullable): Content of the prompt before the input box when uploading a file.
    * type(string, nullable): Dialog type. 
      * All possible values:
      *                 normal: Default type, Display dialogs in the format preset by the frontend. 
                upload: Uploading file(s) in dialog.Can only upload file if the button's type is also upload.
            

    * continueNm(string, nullable): Name of contionue button in dialog. Default name is "Continue".
    * cancelNm(string, nullable): Name of cancel button in dialog. Default name is "Cancel".

  

  * Example 
    *         "widgetParameter": {
          "icon": "images/download_button.gif",
          "type": "download",
          "dialog": "dialogMessage: testMsg; dialogBeforeDisplayEvent: getMessage; type: normal"
        }
        

### File

  * multiple(string, nullable): Whether multiple files can be uploaded.

  

  * Example 
    *         "widgetParameter": {
          "multiple": "yes"
        }
        

