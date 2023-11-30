// XH 2022-07-05 start
import classNames from "classnames"
import transform from "css-to-react-native"
import { columnIndexToLabel } from "hot-formula-parser"
import moment from "moment"
import * as React from "react"
import { Tooltip } from "react-tooltip"
import "react-tooltip/dist/react-tooltip.css"
import pyiLocalStorage from "../../utils/pyiLocalStorage"
import * as Actions from "./actions"
import * as Selection from "./selection"
import * as Types from "./types"
import useDispatch from "./use-dispatch"
import useSelector from "./use-selector"

// YL, 2023-05-06 Add tooltip - start
const pyiGlobal = pyiLocalStorage.globalParams
const sort_icon = pyiGlobal.PUBLIC_URL + "images/sort_icon.png"
const sort_icon_asc = pyiGlobal.PUBLIC_URL + "images/sort_icon_asc.png"
const sort_icon_desc = pyiGlobal.PUBLIC_URL + "images/sort_icon_desc.png"
const img_tip = pyiGlobal.PUBLIC_URL + "images/tips_icon.gif"
// YL, 2023-05-06 - end

const ColumnIndicator: Types.ColumnIndicatorComponent = ({ tableName, row, column, stylePrams, label, columnStatus, tip, onSelect, onSorted }) => {
  // YL, 2023-05-06 Add tooltip - start
  let tooltip
  if (tip) {
    if (tip.includes("\\r\\n")) {
      tooltip = tip.replace(/\\r\\n/g, "\r\n")
    } else if (tip.includes("\\n")) {
      tooltip = tip.replace(/\\n/g, "\r\n")
    } else if (tip.includes("\\r")) {
      tooltip = tip.replace(/\\r/g, "\r\n")
    } else {
      tooltip = tip
    }
  }
  // YL, 2023-05-06 - end
  const handleClick = React.useCallback(
    (event: React.MouseEvent) => {
      onSelect(column, event.shiftKey)
    },
    [onSelect, column]
  )
  const handleDoubleClick = React.useCallback(
    (event: React.MouseEvent) => {
      onSorted(column, event.shiftKey)
    },
    [onSorted, column]
  )
  const rowSpan = stylePrams?.rowSpan
  const colSpan = stylePrams?.colSpan
  const style = stylePrams?.style

  const isLastColumn = (captionList: any[], index: number) => {
    let res = false
    for (let i = index + 1; i <= captionList.length; i++) {
      if (captionList[i]) {
        res = true //  Determine if it's already the bottom headerRow.
      }
    }
    return res
  }
  if (row < 0 && Array.isArray(label)) {
    if (isLastColumn(label, -row - 2) && label.length !== -row - 2) {
      columnStatus = 0
    }
    label = label[-row - 2] ? label[-row - 2].text : ""
  }
  // YL, 2023-05-06 Add tooltip - start
  return (
    <>
      {row < 0 ? (
        colSpan !== 0 || rowSpan !== 0 ? (
          <th
            id={"cell_" + row + "_" + (column - 2) + " " + tableName}
            className={classNames("Spreadsheet__header", "Spreadsheet__header__column", {
              Spreadsheet__header__index: column < 0,
            })}
            onClick={handleClick}
            onDoubleClick={handleDoubleClick}
            tabIndex={0}
            rowSpan={rowSpan}
            colSpan={colSpan}
            style={style ? transform(style) : null}
          >
            <span className="sort">
              {label !== undefined ? label : columnIndexToLabel(column)}
              {/* tooltip icon */}
              {tooltip ? (
                <>
                  <img
                    src={img_tip}
                    alt="tooltip img"
                    style={{ paddingLeft: "3px" }}
                    data-tooltip-id={"th-tooltip_" + row + "_" + (column - 2) + " " + tableName}
                    data-tooltip-place="top"
                    data-tooltip-content={tooltip}
                  ></img>
                  <Tooltip id={"th-tooltip_" + row + "_" + (column - 2) + " " + tableName} />
                </>
              ) : null}
              {columnStatus === 1 ? (
                <img className="sort_img" alt="sort img" src={sort_icon} />
              ) : columnStatus === 2 ? (
                <img className="sort_img" alt="sort img" src={sort_icon_desc} />
              ) : columnStatus === 3 ? (
                <img className="sort_img" alt="sort img" src={sort_icon_asc} />
              ) : null}
            </span>
          </th>
        ) : null
      ) : colSpan !== 0 ? (
        <th
          id={"cell_" + row + "_" + (column - 2) + " " + tableName}
          className="Spreadsheet__header Spreadsheet__footer__column"
          tabIndex={0}
          colSpan={colSpan}
          style={style ? transform(style) : null}
        >
          <span className="Spreadsheet__data-viewer">
            {label !== undefined ? label : columnIndexToLabel(column)}
            {/* tooltip icon */}
            {tooltip ? (
              <>
                <img
                  src={img_tip}
                  alt="tooltip img"
                  style={{ paddingLeft: "3px" }}
                  data-tooltip-id={"th-tooltip_" + row + "_" + (column - 2) + " " + tableName}
                  data-tooltip-place="top"
                  data-tooltip-content={tooltip}
                ></img>
                <Tooltip id={"th-tooltip_" + row + "_" + (column - 2) + " " + tableName} />
              </>
            ) : null}
          </span>
        </th>
      ) : null}
    </>
  )
}
// YL, 2023-05-06 - end

export default ColumnIndicator

export const enhance = (
  ColumnIndicatorComponent: Types.ColumnIndicatorComponent
): React.FC<Omit<Types.ColumnIndicatorProps, "selected" | "onSelect" | "onSorted" | "onMouseEnter" | "onMouseLeave">> => {
  return function ColumnIndicatorWrapper(props) {
    const dispatch = useDispatch()
    const selectEntireColumn = React.useCallback(
      (column: number, extend: boolean) => dispatch(Actions.selectEntireColumn(column, extend)),
      [dispatch]
    )
    const sortByThisColumn = React.useCallback((column: number, extend: boolean) => dispatch(Actions.sortByThisColumn(column, extend)), [dispatch])
    const selected = useSelector((state) => Selection.hasEntireColumn(state.selected, props.column) || Selection.isEntireTable(state.selected))
    return <ColumnIndicatorComponent {...props} selected={selected} onSelect={selectEntireColumn} onSorted={sortByThisColumn} />
  }
}
// XH 2022-07-05 end

export const getFooterData = (footerPram, columnNumber, tableData, showRange) => {
  if (!footerPram) {
    return ""
  } else if (footerPram.text) {
    return footerPram.text
  }
  let formula = footerPram.formula ? footerPram.formula.trim() : ""
  let format = footerPram.format ? footerPram.format.trim() : ""
  let dataType = footerPram.dataType ? footerPram.dataType.trim().toLocaleLowerCase() : "float"
  let columnDataList = []
  tableData.forEach((row, index) => {
    if (showRange.indexOf(index) !== -1) {
      columnDataList.push(row[columnNumber].value)
    }
  })
  if (!formula) {
    return ""
  }
  if (tableData.length === 0 || showRange.length === 0) {
    if (formula.startsWith("function")) {
      return customFunctions(formula, [])
    } else {
      return ""
    }
  }

  let res
  if (formula === "sum") {
    if (dataType === "int" || dataType === "float") {
      columnDataList.forEach((data) => {
        data = Number(data.replace(/,/g, ''))
        res ? (res += data) : (res = data)
      })
    } else if ((dataType === "date" || dataType === "time" || dataType === "datetime") && format === "HH:mm:ss") {
      const resList = columnDataList[0].split(":")
      columnDataList.forEach((data, index) => {
        if (index === 0) {
          resList[0] = Number(resList[0])
          resList[1] = Number(resList[1])
          resList[2] = Number(resList[2])
        } else {
          const dataList = data.split(":")
          resList[0] += Number(dataList[0])
          resList[1] += Number(dataList[1])
          resList[2] += Number(dataList[2])
        }
      })
      let addMin,
        addHour = 0
      if (resList[2] >= 60) {
        addMin = Math.floor(resList[2] / 60)
        resList[2] = resList[2] % 60
      }
      if (resList[1] + addMin >= 60) {
        addHour = Math.floor(resList[1] / 60)
        resList[1] = (resList[1] + addMin) % 60
      }
      resList[0] += addHour
      res = String(resList[0]) + ":" + String(resList[1]) + ":" + String(resList[2])
      format = ""
    }
  } else if (formula === "avg") {
    if (dataType === "int" || dataType === "float") {
      columnDataList.forEach((data) => {
        data = Number(data.replace(/,/g, ''))
        res ? (res += data / columnDataList.length) : (res = data / columnDataList.length)
      })
    } else if ((dataType === "date" || dataType === "time" || dataType === "datetime") && format === "HH:mm:ss") {
      const resList = columnDataList[0].split(":")
      columnDataList.forEach((data, index) => {
        if (index === 0) {
          resList[0] = Number(resList[0]) / columnDataList.length
          resList[1] = Number(resList[1]) / columnDataList.length
          resList[2] = Number(resList[2]) / columnDataList.length
        } else {
          const dataList = data.split(":")
          resList[0] += Number(dataList[0]) / columnDataList.length
          resList[1] += Number(dataList[1]) / columnDataList.length
          resList[2] += Number(dataList[2]) / columnDataList.length
        }
      })
      res = String(resList[0].toFixed(0)) + ":" + String(resList[1].toFixed(0)) + ":" + String(resList[2].toFixed(0))
      format = ""
    }
  } else if (formula === "max") {
    if (dataType === "int" || dataType === "float") {
      columnDataList.forEach((data) => {
        data = Number(data.replace(/,/g, ''))
        if (!res || res < data) {
          res = data
        }
      })
    } else if (dataType === "date" || dataType === "time" || dataType === "datetime") {
      res = columnDataList[0]
      columnDataList.forEach((data) => {
        if (moment(res).isBefore(data)) {
          res = data
        }
      })
    }
  } else if (formula === "min") {
    if (dataType === "int" || dataType === "float") {
      columnDataList.forEach((data) => {
        data = Number(data.replace(/,/g, ''))
        if (!res || res > data) {
          res = data
        }
      })
    } else if (dataType === "date" || dataType === "time" || dataType === "datetime") {
      res = columnDataList[0]
      columnDataList.forEach((data) => {
        if (moment(res).isAfter(data)) {
          res = data
        }
      })
    }
  } else if (formula.startsWith("function")) {
    res = customFunctions(formula, columnDataList)
  }

  if (res && dataType && format) {
    if (dataType === "date" || dataType === "time" || dataType === "datetime") {
      res = moment(res).format(format)
    } else {
      const index = format.indexOf(".")
      if (index !== -1) {
        const digits = format.slice(index + 1).length
        res = res.toFixed(Number(digits))
        res = res.replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",")
      }
    }
  } else if (!res) {
    res = ""
  }
  return res
}

function customFunctions(formula, columnDataList) {
  const pramsIndexLeft = formula.indexOf("(")
  const pramsIndexRight = formula.indexOf(")")
  const funcIndexLeft = formula.indexOf("{")
  const funcIndexRight = formula.lastIndexOf("}")
  const prams = formula.slice(pramsIndexLeft + 1, pramsIndexRight).split(",")
  const func = formula.slice(funcIndexLeft + 1, funcIndexRight)

  const __formula = new Function(prams[0].trim(), func)
  return __formula(columnDataList)
}
