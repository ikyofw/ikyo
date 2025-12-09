/*
 * @Description:
 * @version:
 * @Author: Lucy
 * @Date: 2022-04-06 08:55:14
 */
import React from "react"
import DropdownList from "react-widgets/DropdownList"
import * as Types from "./types"
import { moveCursorToEnd } from "./util"
// TODO
// DropdownList cant set required
import { formatDate, getDateFormatStr } from "../../utils/sysUtil"
import { Calendar as DatePicker } from "../calendar/DatePicker" // LHH.ikyo 2022-05-09
// LHH.ikyo 2022-05-20 start
import * as Actions from "./actions"
import useDispatch from "./use-dispatch"
// LHH.ikyo 2022-05-20 end

/** The default Spreadsheet DataEditor component */
const DataEditor: React.FC<Types.DataEditorProps> = ({ onChange, cell, column, comboPrams, dateBoxCols, textareaCols, style }) => {
  // for combobox cell
  let isComboCell = false
  const index = comboPrams["columns"].indexOf(column)
  let options: Array<{ value: string; display: string }> = []
  if (index !== -1 && comboPrams["comboData"].length > 0) {
    isComboCell = true
    options = comboPrams["comboData"][index]["data"]
    const required = comboPrams["required"][index]
    // YL, 2024-02-23 show empty value - start
    options.forEach((op) => {
      if (op.display == "" || op.display == null) {
        op.display = " "
      }
      if (typeof op.display == "string" && op.display.trim() == "") {
        op.display = op.display.replace(/\s/g, "\u00a0")
      }
    })
    if (!required && !options.some(op => op.value === null)) {
      options = [{"value": null, "display": "\u00a0"}, ...options]
    }
    // YL, 2024-02-23 - end
  }

  // LHH.ikyo 2022-05-09 start: please delete the commented lines in the former version and replace with the new lines
  var isCalendar = false
  var defaultFormatNo = 1
  var calendarFormatNo = defaultFormatNo
  if (typeof dateBoxCols != "undefined") {
    for (var i = 0; i < dateBoxCols.length; i++) {
      if (dateBoxCols[i].colIndex === column) {
        isCalendar = true
        calendarFormatNo = dateBoxCols[i]?.formatFlag ?? defaultFormatNo
        break
      }
    }
  }
  var calendarFormatString = getDateFormatStr(calendarFormatNo)
  // LHH.ikyo 2022-05-09 end

  var isTextarea = false
  if (textareaCols.indexOf(column) !== -1) {
    isTextarea = true
  }

  React.useEffect(() => {
    let textarea = document.getElementById("textarea_box") as any
    if (!textarea) {
      return
    }
    if (textarea.setSelectionRange) {
      //not ie
      textarea.focus()
      textarea.setSelectionRange(-1, -1) // Setting the cursor to the end
    } else if (textarea.createTextRange) {
      var range = textarea.createTextRange()
      range.collapse(true)
      range.moveEnd("character", textarea)
      range.moveStart("character", textarea)
      range.select()
    }
  }, [])

  const handleChange = React.useCallback(
    (event: any) => {
      const inputBox = isTextarea ? (document.getElementById("textarea_box") as any) : (document.getElementById("input_box") as any)
      if (!inputBox) {
        return
      }
      setValue(event.target.value)
      onChange({ ...cell, value: event.target.value })
    },
    [isTextarea, onChange, cell]
  )

  const inputRef = React.useRef<HTMLInputElement>(null)
  React.useEffect(() => {
    if (inputRef.current) {
      moveCursorToEnd(inputRef.current)
    }
  }, [inputRef])

  // LHH.ikyo 2022-05-20 start
  const dispatch = useDispatch()
  const view = React.useCallback(() => dispatch(Actions.view()), [dispatch])
  // LHH.ikyo 2022-05-20 end

  // const value = cell?.value ?? ""
  const [value, setValue] = React.useState(cell?.value ?? "")

  // LHH.ikyo 2022-05-09 start
  React.useEffect(() => {
    return () => {
      if (isCalendar) {
        var curValue = inputRef.current ? inputRef.current?.value ?? "" : ""
        var formatValue = formatDate(curValue, calendarFormatString)
        if (formatValue !== value) {
          setValue(formatValue)
          onChange({ ...cell, value: formatValue })
          view() // LHH.ikyo 2022-05-20
        }
      }
    }
  }, [inputRef, onChange, view]) // LHH.ikyo 2022-05-20

  const [key, setKey] = React.useState(value)
  const handleDropdownList = React.useCallback(
    (nextValue) => {
      setKey(String(nextValue.display))
      onChange({ ...cell, value: nextValue.display, comboKey: nextValue.value })
    },
    [onChange, cell, setKey]
  )

  return (
    <div className="Spreadsheet__data-editor">
      {isComboCell ? (
        <DropdownList
          id="dropdownList"
          data={options}
          dataKey="value"
          textField="display"
          autoFocus={true}
          value={key}
          onChange={handleDropdownList}
          messages={{ emptyFilter: "", emptyList: "" }}
        />
      ) : isCalendar ? (
        <DatePicker
          calType="input"
          ref={inputRef}
          textStr={value}
          format={calendarFormatNo} // LHH.ikyo 2022-05-09
          editable={true}
          inCell={true}
        />
      ) : isTextarea ? (
        <textarea
          id="textarea_box"
          style={style}
          onChange={(e) => handleChange(e)}
          value={value} // TODO: alt+enter line feed
          autoFocus
        ></textarea>
      ) : (
        <input id="input_box" ref={inputRef} type="text" onChange={handleChange} value={value} autoFocus />
      )}
    </div>
  )
}

export default DataEditor

// function parseData(data) {
//   let options = []
//   if (typeof data[0] === "object") {
//     options = data
//   } else if (typeof data[0] === "string") {
//     data.forEach((option) => {
//       options.push({ value: option, display: option })
//     })
//   }
//   return options
// }
