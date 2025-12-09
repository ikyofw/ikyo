import { getDialogEvent, getDialogEventParamArr, getDialogParams } from "../components/Dialog"
import pyiLocalStorage from "./pyiLocalStorage"

/**
 *  parse data for table
 *  table data format: [[{value: "a"}, {value: "b"}], [{value: "aa"}, {value: "bb"}]]
 * @param data table data(json format)
 * @param fields table data fields
 * @returns
 */

const global = pyiLocalStorage.globalParams
export function parseTableData(data: any[], fieldsParams: any[], fields: string[]) {
  const dataArr = []

  data &&
    data.forEach((item) => {
      const dataItemArr = []
      for (let index = 0; index < fields.length; index++) {
        let element = ""
        if (fields[index] === global.TABLE_ROW_ID) {
          const primaryKey = item[global.TABLE_PRIMARY_KEY]
          element = primaryKey && primaryKey !== null ? primaryKey : "id"
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
          if (index > 1 && fieldsParams[index - 2].widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_LINK) {
            let valueDisplay = fieldsParams[index - 2].widgetParameter.values
            if (valueDisplay) {
              valueDisplay = valueDisplay.replace(/'/g, '"')
              valueDisplay = JSON.parse(valueDisplay)
            } else {
              valueDisplay = { value: "value", display: "display" }
            }
            const value = item[valueDisplay["value"]]
            const display = item[valueDisplay["display"]]
            dataItemArr.push({
              value: (value && value !== null) || value === 0 || value === false ? String(value) : "",
              display: (display && display !== null) || display === 0 || display === false ? String(display) : "",
            })
          } else {
            dataItemArr.push({
              value: (item[element] && item[element] !== null) || item[element] === 0 || item[element] === false ? String(item[element]) : "",
            })
          }
        }
      }
      dataArr.push(dataItemArr)
    })
  // console.log("dataArr", dataArr)
  return dataArr
}

/**
 * get table data fields
 * @param table
 * @returns
 */
export function parseTableDataField(table: any, selectionMode: string | null) {
  const tableFgFieldArr = []

  tableFgFieldArr.push(global.TABLE_ROW_ID)
  tableFgFieldArr.push(selectionMode ? global.SELECTABLE_TABLE_ROW_STATUS : global.TABLE_ROW_STATUS)
  table.fields && table.fields.forEach((field) => tableFgFieldArr.push(field.dataField))
  // console.log("tableFgFieldArr", tableFgFieldArr)
  return tableFgFieldArr
}

/**
 * get table column caption
 * @param table
 * @returns
 */
export function getTableHeaderPrams(table: any) {
  const tableHeaderPrams = { headerLabels: [], headerLabelTips: [], headerLines: [] }
  const headerLabels = []
  const headerLabelTips = []
  let headerLines = []

  headerLabels.push(table.type === global.TABLE_TYPE && table.deletable ? "img_insert" : null)
  headerLabelTips.push("")
  headerLabels.push("")
  headerLabelTips.push("")
  table.fields &&
    table.fields.forEach((field) => {
      headerLabels.push(field.caption)
      headerLabelTips.push(field.tooltip)
    })
  if (table.fields && table.fields.length > 0 && Array.isArray(table.fields[0].caption)) {
    for (let i = 2; i < table.fields[0].caption.length + 2; i++) {
      headerLines.push(i)
    }
  } else {
    headerLines = [2] // headerLines saves the serial numbers of all lines in the header, starting from 2 because the ids of the lines in the header are decreasing from -2.
  }

  tableHeaderPrams["headerLabels"] = headerLabels
  tableHeaderPrams["headerLabelTips"] = headerLabelTips
  tableHeaderPrams["headerLines"] = headerLines
  // console.log("table real field:", tableHeaderPrams)
  return tableHeaderPrams
}

/**
 * get table footer style parameters
 * @param table
 * @returns
 */
export function getTableHeadStylePrams(table: any) {
  const tableHeadStylePrams = []
  if (table.fields) {
    for (let index_1 = 0; index_1 < table.fields.length; index_1++) {
      let columnPrams = []
      let caption = table.fields[index_1].caption
      if (Array.isArray(caption)) {
        caption.forEach((item, index_2) => {
          let cellPrams = { rowSpan: 0, colSpan: 0, style: null }
          if (item && item.style) {
            let style = []
            if (item.style && typeof item.style === "string") {
              item.style = parsePrams(item.style)
            }
            if (item.style && typeof item.style === "object") {
              const properties = Object.keys(item.style)
              properties.forEach((property) => {
                style.push([property, item.style[property]])
              })
            }
            cellPrams.style = style
          }

          if (item && item.text !== null) {
            cellPrams.rowSpan = 1
            cellPrams.colSpan = 1 // Cells with rowSpan and colSpan of 0 will be merged.
            for (
              let columnIndex = index_1 + 1;
              table.fields[columnIndex] && // Determine if a cell extends beyond the entire table to the right
              !table.fields[columnIndex].caption[index_2] && // Determine if a cell is empty
              !isOtherSubColumn(table.fields[columnIndex].caption, index_2); // Determine if a cell is already a cell below another column
              columnIndex += 1
            ) {
              // Loop right through the cell, the cell is empty and does not reach the bottom of another column of cells and does not exceed the entire table is merged into the cell
              cellPrams.colSpan += 1
            }
            for (let rowIndex = index_2 + 1; rowIndex < caption.length && !table.fields[index_1].caption[rowIndex]; rowIndex += 1) {
              cellPrams.rowSpan += 1 // Loop down through the cell, the cell is empty and does not exceed the header is merged into the cell
            }
          }
          columnPrams.push(cellPrams)
        })
      }
      tableHeadStylePrams.push(columnPrams)
    }
  }
  // console.log("tableHeadStylePrams", tableHeadStylePrams);
  return tableHeadStylePrams
}
function isOtherSubColumn(captionList: any[], index: number) {
  let res = false
  for (let i = index - 1; i >= 0; i--) {
    if (captionList[i]) {
      res = true // Determine if a cell is already a cell below another column
    }
  }
  return res
}

/**
 * get table combo cell columns
 * @param table
 * @returns
 */
export function getTableComboBoxColNos(table: any) {
  const tableFgComboBoxColsArr = []
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_COMBO_BOX) {
        tableFgComboBoxColsArr.push(index + 2)
      }
    }
  }
  //console.log("tableFgComboBoxColsArr", tableFgComboBoxColsArr);
  return tableFgComboBoxColsArr
}

/**
 * get table plugin params
 * @param table
 * @returns
 */
export function getTablePluginParams(fields: string[], pluginParams: any) {
  const TablePluginParamsArr = []
  for (let index = 0; index < pluginParams.length; index++) {
    const fieldGroups = pluginParams[index].eventHandlerParameter.fieldGroups
    if (!fieldGroups || fieldGroups.length <= 0) {
      TablePluginParamsArr.push(0)
    } else {
      const pluginParam = fieldGroups[0].substring(1)
      if (pluginParam === "id") {
        TablePluginParamsArr.push(0)
      } else {
        TablePluginParamsArr.push(fields.indexOf(pluginParam))
      }
    }
  }
  // console.log('TablePluginParamsArr', TablePluginParamsArr);
  return TablePluginParamsArr
}

/**
 * get table combo cell selections
 * @param table
 * @returns
 */
export function getTableComboBoxPrams(table: any) {
  const tableFgComboBoxPrams: {
    columns: number[]
    comboData: { [key: string]: any }[]
  } = { columns: [], comboData: [] }
  let columns = []
  let comboData = []
  let required = []

  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      const widget = field.widget?.trim().toLocaleLowerCase()
      if ((widget === global.FIELD_TYPE_COMBO_BOX || widget === global.FIELD_TYPE_LABEL) && field.widgetParameter && field.widgetParameter.data) {
        columns.push(index + 2)
        required.push(field.required)

        let options = []
        const data = field.widgetParameter.data
        if (data) {
          let values = field.widgetParameter.values
          if (values) {
            values = values.replace(/'/g, '"')
            values = JSON.parse(values)
          } else {
            values = { value: "value", display: "display" }
          }

          if (typeof data === "string") {
            options = JSON.parse(data)
          } else if (Array.isArray(data)) {
            if (typeof data[0] !== "object") {
              data.forEach((option) => {
                options.push({ value: String(option), display: String(option) })
              })
            } else {
              if ("value" in data[0] && "display" in data[0]) {
                options = data
              } else {
                data.forEach((option) => {
                  options.push({ value: option[values.value], display: option[values.display] })
                })
              }
            }
          }
        }
        comboData.push({ data: options })
      }
    }
  }
  tableFgComboBoxPrams["columns"] = columns
  tableFgComboBoxPrams["comboData"] = comboData
  tableFgComboBoxPrams["required"] = required

  // console.log("tableFgComboBoxPrams", tableFgComboBoxPrams)
  return tableFgComboBoxPrams
}

export function getTableCheckBoxPrams(table: any) {
  const tableFgCheckBoxPrams = []
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      let prams = {}
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_CHECK_BOX) {
        if (field.widgetParameter.stateNumber) {
          let stateNumber = field.widgetParameter.stateNumber
          if (stateNumber.startsWith('"') || stateNumber.startsWith("'")) {
            stateNumber = stateNumber.slice(1, -1)
          }
          prams["stateNumber"] = Number(stateNumber)
        } else {
          prams["stateNumber"] = 2
        }
      }
      prams["editable"] = field.editable
      tableFgCheckBoxPrams.push(prams)
    }
  }
  // console.log('tableFgCheckBoxPrams', tableFgCheckBoxPrams);
  return tableFgCheckBoxPrams
}

export function parsePrams(prams: string, split?: string) {
  if (!prams || prams.length === 0) {
    return
  }
  const splitPram = split ? split : ","
  const items = prams.startsWith("{") ? prams.slice(1, -1).split(splitPram) : prams.split(splitPram)
  let checkItems = {}
  items.forEach((item) => {
    let key = item.slice(0, item.indexOf(":")).trim()
    let value = item.slice(item.indexOf(":") + 1).trim()
    if (key.startsWith('"') || key.startsWith("'")) {
      key = key.slice(1, -1)
    }
    if (value.startsWith('"') || value.startsWith("'")) {
      value = value.slice(1, -1)
    }
    checkItems[key] = value
  })
  return checkItems
}

export function getTableFormatPrams(table: any) {
  const tableFgFormatInfoArr = [null, null]
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const widgetParameter = table.fields[index].widgetParameter
      if (widgetParameter) {
        let format = widgetParameter["format"]
        tableFgFormatInfoArr.push(format)
      } else {
        tableFgFormatInfoArr.push(null)
      }
    }
  }
  // console.log("tableFgFormatInfoArr", tableFgFormatInfoArr)
  return tableFgFormatInfoArr
}

export function getTableDateBoxColsInfo(table: any) {
  const tableFgDateBoxColInfoArr = []
  if (table.type === global.TABLE_TYPE && table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_DATE_BOX) {
        let format = field.widgetParameter["format"]
        let flag = format
          ? format.trim().toLocaleLowerCase() === "yyyy-mm-dd"
            ? 1
            : format.trim().toLocaleLowerCase() === "yyyy-mm-dd hh:mm:ss"
            ? 2
            : 3
          : 1
        let dateBoxColInfo = {
          colIndex: index + 2,
          formatFlag: flag,
        }
        tableFgDateBoxColInfoArr.push(dateBoxColInfo)
      }
    }
  }
  // console.log("tableFgDateBoxColInfoArr", tableFgDateBoxColInfoArr)
  return tableFgDateBoxColInfoArr
}

export function getTableLinkColsNos(table: any) {
  const tableFgLinkColNosArr = []
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      const widget = field.widget?.trim().toLocaleLowerCase()
      if (widget === global.FIELD_TYPE_LINK) {
        tableFgLinkColNosArr.push(index + 2)
      }
    }
  }
  // console.log("tableFgDisableColNosArr", tableFgDisableColNosArr)
  return tableFgLinkColNosArr
}

/**
 * get table disable columns
 * @param table
 * @returns
 */
export function getTableDisableColNos(table: any) {
  const tableFgDisableColNosArr = []
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      const widget = field.widget?.trim().toLocaleLowerCase()
      if (
        widget === global.FIELD_TYPE_LABEL ||
        widget === global.FIELD_TYPE_LINK ||
        widget === global.FIELD_TYPE_CHECK_BOX ||
        widget === global.FIELD_TYPE_BUTTON ||
        widget === global.FIELD_TYPE_HTML ||
        widget === global.FIELD_TYPE_ADVANCED_SELECTION ||
        !field.editable
      ) {
        tableFgDisableColNosArr.push(index + 2)
      }
    }
  }
  // console.log("tableFgDisableColNosArr", tableFgDisableColNosArr)
  return tableFgDisableColNosArr
}

/**
 * get table inVisible columns
 * @param table
 * @returns
 */
export function getTableInVisibleColNos(table: any) {
  const hiddenColumnIndexes = []
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (!field.visible) {
        hiddenColumnIndexes.push(index + 2)
      }
    }
  }
  // console.log("tableFgInVisibleColNosArr", tableFgInVisibleColNosArr);
  return hiddenColumnIndexes
}

/**
 * get table TextArea columns
 * @param table
 * @returns
 */
export function getTableTextAreaColNos(table: any) {
  const tableFgTextAreaColNosArr = []
  if (table.type === global.TABLE_TYPE && table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_TEXTAREA) {
        tableFgTextAreaColNosArr.push(index + 2)
      }
    }
  }
  // console.log("tableFgTextAreaColNosArr", tableFgTextAreaColNosArr)
  return tableFgTextAreaColNosArr
}

/**
 * get table TextArea columns
 * @param table
 * @returns
 */
export function getTableHtmlColNos(table: any) {
  const tableFgHtmlColNosArr = []
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_HTML) {
        tableFgHtmlColNosArr.push(index + 2)
      }
    }
  }
  // console.log("tableFgTextAreaColNosArr", tableFgTextAreaColNosArr)
  return tableFgHtmlColNosArr
}

/**
 * get table dialog parameters
 * @param table
 * @returns
 */
export function getTableDialogPrams(fields: any, table: any) {
  const tableDialogPrams: {
    columns: number[]
    dialog: { [key: string]: any }[]
    eventHandler: { [key: string]: any }[]
  } = { columns: [], dialog: [], eventHandler: [] }
  let columns = []
  let dialog = []
  let eventHandler = []

  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      const widget = field.widget?.trim().toLocaleLowerCase()
      if (widget === global.FIELD_TYPE_BUTTON || widget === global.FIELD_TYPE_ADVANCED_SELECTION || widget === global.FIELD_TYPE_HTML) {
        columns.push(index + 2)

        const btnType = field.widgetParameter["type"] ? field.widgetParameter["type"] : global.BTN_TYPE_NORMAL
        const multiple = field.widgetParameter["multiple"] ? field.widgetParameter["multiple"] : false
        const dialogParams = getDialogParams(field.widgetParameter.dialog)
        if (Object.keys(dialogParams).length !== 0 || btnType === global.BTN_TYPE_UPLOAD_DIALOG) {
          const dialogName = dialogParams["name"]
          const dialogTitle = dialogParams["title"]
          const uploadTip = dialogParams["uploadTip"]
          const dialogContent = dialogParams["content"]
          const eventWithParams = dialogParams["beforeDisplayEvent"]
          const continueName = dialogParams["continueName"] ? dialogParams["continueName"] : "OK"
          const cancelName = dialogParams["cancelName"] ? dialogParams["cancelName"] : "Cancel"
          const dialogWidth = dialogParams["width"]
          const dialogHeight = dialogParams["height"]
          let eventName
          let eventParams
          if (eventWithParams) {
            eventName = getDialogEvent(eventWithParams)
            eventParams = getDialogEventParamArr(eventWithParams)
          }
          let dialogGroups = []
          if (eventParams) {
            if (eventParams.length > 0) {
              eventParams.forEach((pram) => {
                if (pram.substring(1) !== "id" && pram.startsWith("@")) {
                  // Button column of the dialog to the back-end of the method to get the parameters of the dialog to the back-end post the name of the parameters and which column.
                  dialogGroups.push([pram.substring(1), fields.indexOf(pram.substring(1))])
                }
              })
            }
          }
          dialog.push({
            multiple: multiple,
            dialogName: dialogName,
            dialogTitle: dialogTitle,
            uploadTip: uploadTip,
            dialogContent: dialogContent,
            eventName: eventName,
            dialogGroups: dialogGroups,
            continueName: continueName,
            cancelName: cancelName,
            dialogWidth: dialogWidth,
            dialogHeight: dialogHeight,
          })
        } else {
          dialog.push(null)
        }

        eventHandler.push({
          url: field.eventHandler,
          fieldGroups: field.eventHandlerParameter.fieldGroups,
          refreshPrams: field.eventHandlerParameter.refreshPrams,
          fields: fields,
        }) //The click request url for the button column, and the name and column number of the parameters that this url posts to the backend.
      }
    }
  }
  tableDialogPrams["columns"] = columns
  tableDialogPrams["dialog"] = dialog
  tableDialogPrams["eventHandler"] = eventHandler

  // console.log("tableDialogPrams", tableDialogPrams)
  return tableDialogPrams
}

/**
 * get table Button parameters
 * @param table
 * @returns
 */
export function getTableButtonPrams(fields: any, table: any) {
  const tableFgButtonPrams: {
    columns: number[]
    btnIcon: number[]
    type: string[]
  } = { columns: [], btnIcon: [], type: [] }
  let columns = []
  let btnIcon = []
  let type = []

  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_BUTTON) {
        columns.push(index + 2)

        if (field.widgetParameter && field.widgetParameter.icon) {
          btnIcon.push(field.widgetParameter.icon)
        } else {
          btnIcon.push("")
        }
        if (field.widgetParameter && field.widgetParameter.type) {
          type.push(field.widgetParameter.type)
        } else {
          type.push("normal") // The type of the button column, defaults to normal.
        }
      }
    }
  }
  tableFgButtonPrams["columns"] = columns
  tableFgButtonPrams["btnIcon"] = btnIcon
  tableFgButtonPrams["type"] = type

  // console.log("tableFgButtonPrams", tableFgButtonPrams)
  return tableFgButtonPrams
}

/**
 * get table Advanced Selection Cell parameters
 * @param table
 * @returns
 */
export function getTableAdvancedSelectionPrams(fields: any, table: any) {
  const tableFgAdvancedSelectionPrams: {
    columns: number[]
    btnIcon: number[]
    comboData: { [key: string]: any }[]
  } = { columns: [], btnIcon: [], comboData: [] }
  let columns = []
  let btnIcon = []
  let comboData = []

  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      const field = table.fields[index]
      if (field.widget?.trim().toLocaleLowerCase() === global.FIELD_TYPE_ADVANCED_SELECTION) {
        columns.push(index + 2)

        if (field.widgetParameter && field.widgetParameter.icon) {
          btnIcon.push(field.widgetParameter.icon)
        }

        if (field.widgetParameter) {
          let options = []
          let data = field.widgetParameter.data
          if (data) {
            let values = field.widgetParameter.values
            if (values) {
              values = values.replace(/'/g, '"')
              values = JSON.parse(values)
            } else {
              values = { value: "value", display: "display" }
            }

            if (typeof data === "string") {
              options = JSON.parse(data)
            } else if (Array.isArray(data)) {
              if (typeof data[0] !== "object") {
                data.forEach((option) => {
                  options.push({ value: String(option), display: String(option) })
                })
                data = options
              } else {
                if ("value" in data[0] && "display" in data[0]) {
                  options = data
                } else {
                  data.forEach((option) => {
                    options.push({ value: option[values.value], display: option[values.display] })
                  })
                }
              }
            }
          }
          comboData.push(options)
        }
      }
    }
  }
  tableFgAdvancedSelectionPrams["columns"] = columns
  tableFgAdvancedSelectionPrams["btnIcon"] = btnIcon
  tableFgAdvancedSelectionPrams["comboData"] = comboData

  // console.log("tableFgAdvancedSelectionPrams", tableFgAdvancedSelectionPrams)
  return tableFgAdvancedSelectionPrams
}

/**
 * get table body style parameters
 * @param table
 * @returns
 */
export function getTableBodyStylePrams(tableName: string, tableFields: any, tableData, tableStyle) {
  if (tableData.length === 0) {
    return []
  }

  const dataLength = tableData.length
  const fieldLength = tableFields ? tableFields.length : 0
  let tableBodyStylePrams = []
  for (var i = 0; i < dataLength; i++) {
    tableBodyStylePrams.push(Array(fieldLength).fill(null))
  }
  if (tableStyle) {
    if (tableStyle.length === 1 && Object.keys(tableStyle[0]).length === 1 && Object.keys(tableStyle[0])[0].toLocaleLowerCase() === "style") {
      // If there is only one dictionary in the style list, and that dictionary has only one key, 'style', it means that the style is applied to the whole form.
      tableBodyStylePrams = Array(dataLength).fill(Array(fieldLength).fill(tableStyle[0]["style"]))
    } else {
      tableStyle.forEach((style) => {
        // index for -2: modify the style of a whole row or column; index for -1: to find the row/column, do not deal with; other cases index is to modify the coordinates of the cell
        let rowIndex = -2
        let colIndex = -2
        if (style["row"] !== undefined) {
          rowIndex = -1
          tableData.forEach((rowData, index) => {
            if (String(rowData["id"]) === String(style["row"])) {
              rowIndex = index
            }
          })
        }
        if (style["col"] !== undefined) {
          colIndex = -1
          tableFields.forEach((field, index) => {
            if (field.name === style["col"]) {
              colIndex = index
            }
          })
        }

        if (rowIndex === -2 && colIndex >= 0) {
          tableBodyStylePrams.forEach((rowStyle) => {
            rowStyle[colIndex] = { ...rowStyle[colIndex], ...style["style"] }
            if (style.class) {
              const classStyle = { class: style.class }
              rowStyle[colIndex] = { ...rowStyle[colIndex], ...classStyle }
            }
          })
        } else if (colIndex === -2 && rowIndex >= 0) {
          for (var i = 0; i < fieldLength; i++) {
            tableBodyStylePrams[rowIndex][i] = { ...tableBodyStylePrams[rowIndex][i], ...style["style"] }
            if (style.class) {
              const classStyle = { class: style.class }
              tableBodyStylePrams[rowIndex][i] = { ...tableBodyStylePrams[rowIndex][i], ...classStyle }
            }
          }
        } else if (colIndex >= 0 && rowIndex >= 0) {
          tableBodyStylePrams[rowIndex][colIndex] = { ...tableBodyStylePrams[rowIndex][colIndex], ...style["style"] }
          if (style.class) {
            const classStyle = { class: style.class }
            tableBodyStylePrams[rowIndex][colIndex] = { ...tableBodyStylePrams[rowIndex][colIndex], ...classStyle }
          }
        } else {
          let info = "Style setting failure! Table name: " + tableName
          if (rowIndex >= -1) {
            info += ", rowID: " + style["row"]
          }
          if (colIndex >= -1) {
            info += ", columnFieldName: " + style["col"]
          }
          info += ", style: " + JSON.stringify(style["style"])
          console.log(info)
        }
      })
    }
  }

  if (tableFields) {
    for (let index = 0; index < fieldLength; index++) {
      const field = tableFields[index]
      if (field.style && Object.keys(field.style).length > 0) {
        tableBodyStylePrams.forEach((rowStyle) => {
          rowStyle[index] = { ...rowStyle[index], ...field.style }
        })
      }
    }
  }
  // console.log("tableBodyStylePrams", tableBodyStylePrams);
  return tableBodyStylePrams
}

/**
 * get table add row style parameters
 * @param table
 * @returns
 */
export function getAddRowStyle(tbodyStylePrams: any, tableFields: any) {
  let addRowStyle = []
  if (tableFields) {
    const fieldLength = tableFields.length
    for (let index = 0; index < fieldLength; index++) {
      addRowStyle[index] = tableFields[index].style
    }
  }
  const newTbodyStylePrams = [...tbodyStylePrams, addRowStyle]
  // console.log("newTbodyStylePrams", newTbodyStylePrams);
  return newTbodyStylePrams
}

/**
 * get table footer style parameters
 * @param table
 * @returns
 */
export function getTableFootStylePrams(table: any) {
  const tableFootStylePrams = []
  let colSpan = 0
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      let footer = table.fields[index].footer
      let pram = { colSpan: null, style: null }
      if (footer) {
        if (footer.colSpan && colSpan <= 1) {
          colSpan = Number(footer.colSpan)
          pram.colSpan = colSpan
        } else if (colSpan > 1) {
          colSpan -= 1
          pram.colSpan = 0
        }

        let style = []
        if (footer.style && typeof footer.style === "string") {
          footer.style = parsePrams(footer.style)
        }
        if (footer.style && typeof footer.style === "object") {
          const properties = Object.keys(footer.style)
          properties.forEach((property) => {
            style.push([property, footer.style[property]])
          })
        }
        pram.style = style
      } else if (colSpan > 1) {
        colSpan -= 1
        pram.colSpan = 0
      }
      tableFootStylePrams.push(pram)
    }
  }
  // console.log("tableFootStylePrams", tableFootStylePrams);
  return tableFootStylePrams
}

/**
 * get table footer parameters
 * @param table
 * @returns
 */
export function getTableFooterPrams(table: any) {
  const tableFooterPrams = {}
  if (table.fields) {
    for (let index = 0; index < table.fields.length; index++) {
      let footer = table.fields[index].footer
      if (footer) {
        tableFooterPrams[index] = footer
      }
    }
  }
  // console.log("tableFooterPrams", tableFooterPrams);
  return tableFooterPrams
}

/**
 * get table plugin active rows
 * @param table
 * @returns
 */
export function getTablePluginActiveRows(data: any[], fields: string[], pluginParams: number[]) {
  const pluginActiveRows = []

  const key = fields[pluginParams[0]]
  data &&
    data.forEach((item) => {
      if (item[global.PLUGIN_ACTIVE_STATUS]) {
        if (key === "__KEY_") {
          pluginActiveRows.push(item.id)
        } else {
          pluginActiveRows.push(item[key])
        }
      }
    })
  // console.log("pluginActiveRows", pluginActiveRows)
  return pluginActiveRows
}
