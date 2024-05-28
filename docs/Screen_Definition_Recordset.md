## Online

[![ScreenDfn recoredset
online.png](images/ScreenDfn_recoredset_online.png)](images/ScreenDfn_recoredset_online.png)

Select the page definition of the page to be modified in the screenDfn page,
and then modify the recordset table

## Spreadsheet

[![ScreenDfn recoredset
spreadsheet.png](images/ScreenDfn_recoredset_spreadsheet.png)](images/ScreenDfn_recoredset_spreadsheet.png)

Find the excel file that corresponds to the definition of the page that needs
to be modified, and then modify it.

  

## Function

The settings that the form needs to use to get the content to display.

'Recordset Name' column is the most important setting. Each tableFg and some
searchFg and some comboBox need a Recordset Name to retrieve their display
content. After setting the recordset name, a corresponding [get + recordset
name] method on the backend is required to return the specific content.

The 'Models' column may point to a table that actually exists in the database,
or it may point to a dummy model. The dummy model is usually used to set
initial values for schFg, or for page tables that are related to multiple
database tables.

When the 'Models' column refers to a specific database table, the 'Select
Fields', 'Where', 'Order', and 'Limit' columns become relevant. These columns
contain parameters used for querying content from the database.

