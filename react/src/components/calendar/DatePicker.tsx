import transform, { StyleTuple } from "css-to-react-native"
import classnames from "classnames"
import moment from "moment"
import React, { ChangeEvent, forwardRef, Ref, useEffect, useState } from "react"
import pyiLogger from "../../utils/log"
import pyiLocalStorage from "../../utils/pyiLocalStorage"
import { verifyIsDate, verifyIsTime } from "../../utils/sysUtil"
import * as calendar from "./calendar"
import "./calendar-blue.css"

const pyiGlobal = pyiLocalStorage.globalParams
const img_cal = pyiGlobal.PUBLIC_URL + "images/calendar_sbutton.gif"

export type Props = {
  ref: any
  calType: calendarTypes
  cid?: string
  textStr?: string
  format?: number // LHH 2022-05-09
  hideInputAndCal?: boolean
  editable: boolean
  inCell?: boolean // LHH 2022-04-26
  style?: any
}

// flat:display a calendar on the window directly, slect a date won't call any function.
// input: input filed+button,click button to show calendar, and then select a date to show on input field
// displayare: select a date, then the date content show in display area
// button:click the button to show a calendar.
type calendarTypes = "flat" | "input" | "displayArea" | "button"

var calendarGID: number = 0

// LHH 2022-05-09 start
// format option 1
const dateStringFormat = "YYYY-MM-DD"
// format option 2
const dateTimeStringFormat = "YYYY-MM-DD HH:mm:ss"
// format option 3
const timeStringFormat = "HH:mm:ss"
const defaultFormat = dateStringFormat
// LHH 2022-05-09 end

export const Calendar: React.FC<Props> = forwardRef((props, ref: Ref<any>) => {
  const { calType, cid, textStr, format } = props
  var stringFormat = getDateFormatStr(format) // LHH 2022-05-09

  // YL, 2022-04-14 define date format - start
  let dateFormat = "%Y-%m-%d"
  if (stringFormat && String(stringFormat).trim() === dateTimeStringFormat) {
    // LHH 2022-05-09
    dateFormat = "%Y-%m-%d %H:%M:%S"
  } else if (String(stringFormat).trim() === timeStringFormat) {
    // LHH 2022-05-09
    dateFormat = "%H:%M:%S"
  }

  // YL, 2022-04-14 define date format - end

  const hideInputAndCal = props.hideInputAndCal ? props.hideInputAndCal : false

  const [spanClass, setSpanClass] = useState(hideInputAndCal ? "span_h" : "span_s")

  const [dtValue, setDtValue] = useState<string>(
    textStr ? formatDate(textStr, stringFormat) : "" // LHH 2022-05-09
  )

  const [dtErrorMsg, setDtErrorMsg] = useState("")

  const loadInFlat = (flatId: string) => {
    {
      calendar.setup({
        flat: flatId,
        flatCallback: "",
        ifFormat: dateFormat,
        timeFormat: "24",
        showsTime: false,
        weekNumbers: false,
        displayStatusBars: false,
      })
    }
  }

  const loadInDisplayArea = (displayAreaId: string) => {
    {
      calendar.setup({
        displayArea: displayAreaId,
        ifFormat: dateFormat,
        timeFormat: "24",
        showsTime: false,
        weekNumbers: false,
        displayStatusBars: false,
      })
    }
  }

  const loadInButton = (buttonId: string, divId: string) => {
    {
      calendar.setup({
        button: buttonId,
        displayArea: divId,
        ifFormat: dateFormat,
        timeFormat: "24",
        showsTime: false,
        weekNumbers: false,
        displayStatusBars: false,
      })
    }
  }

  const loadInputIn = (inputId: string, buttonId: string) => {
    {
      calendar.setup({
        inputField: inputId,
        ifFormat: dateFormat,
        button: buttonId,
        timeFormat: "24",
        showsTime: false,
        weekNumbers: false,
        displayStatusBars: false,
        // YL, 2023-04-17 It just can works on the first time select date on table.
        // onSelect: function(date: Date, dateStr: string, event) {
        //   var formatValue = formatDate(dateStr, stringFormat)
        //   console.log(dateStr, formatValue, event);
        //   setDtValue(formatValue)
        // }
      })
    }
  }

  const setDate = (dtValue: string) => {
    const calInstance = (window as any).calendar
    if (calInstance && dtValue) {
      const dt = new Date(dtValue)
      calInstance.setDate(dt)
    }
  }

  const setDateValue = (e: ChangeEvent<HTMLInputElement>) => {
    let validatedDt = e.target.value
    if (verifyIsTime(e.target.value)) {
      validatedDt = getValidatedDate(props.format, e.target.value)
    }
    setDtValue(validatedDt)
  }

  useEffect(() => {
    setDtValue(textStr ? formatDate(textStr, stringFormat) : "") // LHH 2022-05-09
  }, [textStr])

  // LHH 2022-04-26 start
  var mRef = ref as React.MutableRefObject<any>

  // YL, 2022-07-13 add date validate - start
  const handleFocus = () => {
    setDtErrorMsg("")
  }

  const handleBlur = () => {
    if (mRef?.current) {
      var curValue = mRef?.current?.value
      if (curValue && !validateSpecifiedFormat(stringFormat, curValue)) {
        setDtErrorMsg("Invalidate format")
        pyiLogger.error("date format error:" + curValue, true)
        return
      }
      // YL, 2022-07-13 - end
      var formatValue = formatDate(curValue, stringFormat) // LHH 2022-05-09
      setDtValue(formatValue)
      mRef.current.value = formatValue
    }
  }
  // LHH 2022-04-26 end

  if (calType.trim().toLocaleLowerCase() === "flat") {
    var divId = cid === undefined ? "div".concat(generateCalWidgetId()) : cid
    return (
      <div id={divId} onLoad={() => loadInFlat(divId)} className="calendar_div1">
        <img src={img_cal} alt="calendar" className="calendar_img_hide"></img>
      </div>
    )
  } else if (calType.trim().toLocaleLowerCase() === "displayArea") {
    var divId = cid === undefined ? "div".concat(generateCalWidgetId()) : cid
    return (
      <div id={divId} onLoad={() => loadInDisplayArea(divId)} className="calendar_div1" ref={ref}>
        {dtValue}
        <img src={img_cal} alt="calendar" className="calendar_img_hide"></img>
      </div>
    )
  } else if (calType.trim().toLocaleLowerCase() === "button") {
    var divId = cid === undefined ? "div".concat(generateCalWidgetId()) : cid
    var buttonId = cid === undefined ? "button".concat(generateCalWidgetId()) : "button".concat(cid)
    return (
      <div className="calendar_div1">
        <div id={divId} ref={ref}>
          {dtValue}
        </div>
        <a id={buttonId}>
          <img src={img_cal} alt="calendar" onLoad={() => loadInButton(buttonId, divId)}></img>
        </a>
      </div>
    )
  } else if (calType.trim().toLocaleLowerCase() === "input") {
    var inputId = cid === undefined ? "input_".concat(generateCalWidgetId()) : cid
    var buttonId = cid === undefined ? "button".concat(generateCalWidgetId()) : "button".concat(cid)
    // LHH 2022-04-26 start
    var inputStyle: StyleTuple[] = []
    let inputClass = []
    if (props.style) {
      const properties = Object.keys(props.style)
      properties.forEach((property) => {
        if (property.toLocaleLowerCase() === "class") {
          inputClass = props.style[property].split(",").map((str) => str.trim())
        } else {
          inputStyle.push([property, props.style[property]])
        }
      })
    }

    var cellStyle = {}
    const inCell = props?.inCell ?? false
    if (inCell) {
      cellStyle = { position: "absolute", right: "0px", width: "auto", bottom: "0px", top: "0px" }
    }
    // LHH 2022-04-26 end

    return (
      <>
        <span style={{ position: "relative", width: "100%", height: "100%" }} onClick={() => setSpanClass("span_s")}>
          <input
            type="text"
            id={inputId}
            className={classnames(inputClass, spanClass)}
            defaultValue={dtValue} // LHH 2022-04-26
            value={props.inCell ? null : dtValue} // YL, 2023-04-17 for simpleFg can set '' date and tableFg can select date.
            onChange={setDateValue}
            ref={(e: HTMLInputElement) => {
              if (e) {
                mRef.current = e
              }
            }}
            disabled={!props.editable}
            onFocus={handleFocus}
            onBlur={handleBlur} // LHH 2022-04-26
            style={inputStyle.length > 0 ? transform(inputStyle) : null}
          />
          {stringFormat == defaultFormat ? ( // LHH 2022-05-09
            <a
              id={buttonId}
              className={spanClass}
              style={cellStyle} // LHH 2022-04-26
            >
              <img
                className="calendar_img"
                onClick={() => setDate(dtValue)}
                onLoad={props.editable ? () => loadInputIn(inputId, buttonId) : null}
                src={img_cal}
                alt="calendar"
              />
            </a>
          ) : null}
        </span>
        <span style={{ paddingLeft: "2px", color: "red" }}>{dtErrorMsg}</span>
      </>
    )
  }

  return <div></div>
})

function generateCalWidgetId() {
  calendarGID = calendarGID + 1
  return "Calendar_auto_".concat(String(calendarGID))
}

export function getDateFormatStr(formatNumber: number | undefined) {
  var format
  switch (formatNumber) {
    case 1:
      format = dateStringFormat
      break
    case 2:
      format = dateTimeStringFormat
      break
    case 3:
      format = timeStringFormat
      break
    default:
      format = defaultFormat
  }
  return format
}

export function formatDate(dateString: string, format: string) {
  if (format == timeStringFormat) {
    return verifyIsTime(dateString) ? dateString : ""
  } else {
    return verifyIsDate(dateString) ? moment(dateString).format(format) : ""
  }
}
// LHH 2022-05-09 end
export default Calendar

function getValidatedDate(formatNumber: number | undefined, date: string) {
  const format = getDateFormatStr(formatNumber)
  return date ? moment(date).format(format) : date
}

// YL, 2022-07-13 - date validate
function validateSpecifiedFormat(format: string, date: string) {
  if (format == timeStringFormat) {
    return verifyIsTime(date)
  } else {
    return verifyIsDate(date)
  }
}

export function isDateBoxColumn(column: number, dateBoxCols: Array<{ colIndex: number; formatFlag?: 1 | 2 | 3 }>) {
  var isDateBox = false
  if (typeof dateBoxCols != "undefined") {
    for (var i = 0; i < dateBoxCols.length; i++) {
      let item = dateBoxCols[i]
      if (item.colIndex === column) {
        isDateBox = true
        break
      }
    }
  }
  return isDateBox
}
