## Function

Parsing table data passed from the backend.

If there is a primary key set, set the actual value of the first column of the
table to the value corresponding to the primary key.

Setting the display of the second column of the table according to
TABLE_ROW_STATUS.

If is selectable table, set whether each row has been selected according to
SELECTABLE_TABLE_ROW_STATUS.

For common columns, simply find the corresponding value to display based on
the field name of the column and display it.

## Implementation Method

### Create parse function

tableUtil.tsx:

    
    
    export function parseTableData(data: string[], fields: string[]) {
      const dataArr = []
    
      data &&
        data.map((item) => {
          const dataItemArr = []
          for (let index = 0; index < fields.length; index++) {
            let element = ''
            if (fields[index] === global.TABLE_ROW_ID) {
              const primaryKey = item[global.TABLE_PRIMARY_KEY]
              element = primaryKey && primaryKey !== null ? primaryKey : 'id'
            } else {
              element = fields[index]
            }
            if (item[element] && fields[index] === global.TABLE_ROW_STATUS) {
              if (item[element] === "n") {
                dataItemArr.push({
                  value: "+",
                })
              } else if (item[element] === "m") {
                dataItemArr.push({
                  value: "~",
                })
              } else if (item[element] === "r") {
                dataItemArr.push({
                  value: "",
                })
              } else if (item[element] === "d") {
                dataItemArr.push({
                  value: "-",
                })
              }
            } else if (item[element] && fields[index] === global.SELECTABLE_TABLE_ROW_STATUS) {
              dataItemArr.push({
                value: item[element] && item[element] !== null ? "true" : "",
              })
            } else {
              dataItemArr.push({
                value: (item[element] && item[element] !== null) || item[element] === 0 || item[element] === false ? String(item[element]) : "",
              })
            }
          }
          dataArr.push(dataItemArr)
        })
      // console.log("dataArr", dataArr)
      return dataArr
    }
    

### Parse and save data

TableFg.tsx:

    
    
    const fetchData = async () => {
      if (!tableParams.dataUrl) {
        showErrorMessage("DataUrl not found, please check.")
        pyiLogger.error("DataUrl not found", true)
        return
      }
      await HttpGet(tableParams.dataUrl)
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, true)) {
            let data = getResponseData(result)
            if (data) {
              if (pageType !== pyiGlobal.SERVER_PAGING) {
                ...
                let pageData = tableUtil.parseTableData(data, fields)
                if (pageData.length > pyiGlobal.PAGE_MAX_ROWS) {
                  showInfoMessage("Display up to 1000 rows in a table.")
                  pageData = pageData.slice(0, 1000)
                }
                setTableData(pageData)
                ...
              }
            }
          }
        })
    }
    useEffect(() => {
      if (tableParams.data) {
        if (pageType !== pyiGlobal.SERVER_PAGING) {
          ...
          let pageData = tableUtil.parseTableData(tableParams.data, fields)
          if (pageData.length > pyiGlobal.PAGE_MAX_ROWS) {
            showInfoMessage("Display up to 1000 rows in a table.")
            pageData = pageData.slice(0, 1000)
          }
          setTableData(pageData)
          ...
        }
      } else if (pageType !== pyiGlobal.SERVER_PAGING) {
        fetchData()
      }
    }, [tableParams.data, tableParams.dataUrl])
    

