## Requirement

Change an icon to another icon when it is clicked

## Options

If the icon does not need to change just pass in an icon and a callback
function for the click event.

If it needs to be changed, pass in the new image and the state of the entire
list of icons.

## Parameter

Pass around one to three icons, callback of clickevent and a list of status of
whether to change the icon.

## Api

Change the plugin create function createIconColumn:

    
    
    function createIconColumn(
      myCallback: any,
      icon: any,
      icon1?: any,
      icon2?: any,
      IconStatus?: any,
      header?: string
    ) {
      if (!header) {
        header = " "
      }
      const IconHeader = () => (
        <th className="Spreadsheet__header Spreadsheet__header__column">
          {header}
        </th>
      )
      const IconCell = (props: any) => (
        <th className="Spreadsheet__header">
          {
            // eslint-disable-next-line jsx-a11y/alt-text
            <img
              src={
                IconStatus
                  ? IconStatus[props.rowNumber] === true
                    ? icon1
                    : IconStatus[props.rowNumber] === false
                    ? icon2
                    : icon
                  : icon
              }
              onClick={() => myCallback(props.rowNumber)}
              style={{ cursor: "pointer" }}
            />
          }
        </th>
      )
      return { IconHeader, IconCell }
    }
    

Simply pass a list named "IconStatus" containing the state of the entire list
of icons. Then, based on the props.rowNumber, select the appropriate icon.

