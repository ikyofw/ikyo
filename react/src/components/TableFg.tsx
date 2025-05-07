import classNames from "classnames"
import moment from "moment"
import React, { forwardRef, Ref, useEffect, useImperativeHandle, useState } from "react"
import ReactDOM from "react-dom"
import ReactHTMLTableToExcel from "react-html-table-to-excel"
import { Tooltip } from "react-tooltip"
import * as Loading from "./Loading"
import * as Actions from "./tableFg/actions"
import * as Matrix from "./tableFg/matrix"
import * as Point from "./tableFg/point"
import * as PointMap from "./tableFg/point-map"
import * as Selection from "./tableFg/selection"
import * as Types from "./tableFg/types"

import "../../public/static/css/TableFg.css"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { showErrorMessage, showInfoMessage, validateResponse } from "../utils/sysUtil"
import * as tableUtil from "../utils/tableUtil"
import ActiveCell from "./tableFg/ActiveCell"
import { Cell as DefaultCell, enhance as enhanceCell } from "./tableFg/Cell"
import DefaultColumnIndicator, { enhance as enhanceColumnIndicator, getFooterData } from "./tableFg/ColumnIndicator"
import { handleData as handleRowData } from "./tableFg/ButtonCell"
import context from "./tableFg/context"
import DefaultDataEditor from "./tableFg/DataEditor"
import DefaultDataViewer from "./tableFg/DataViewer"
import DefaultFooterRow from "./tableFg/FooterRow"
import DefaultHeaderRow from "./tableFg/HeaderRow"
import reducer, { hasKeyDownHandler, INITIAL_STATE } from "./tableFg/reducer"
import DefaultRow from "./tableFg/Row"
import DefaultRowIndicator, { enhance as enhanceRowIndicator } from "./tableFg/RowIndicator"
import Selected from "./tableFg/Selected"
import DefaultTable from "./tableFg/Table"
import {
  calculateSpreadsheetSize,
  getCSV,
  isFocusedWithin,
  range,
  readTextFromClipboard,
  shouldHandleClipboardEvent,
  writeTextToClipboard,
} from "./tableFg/util"

const pyiGlobal = pyiLocalStorage.globalParams
const img_insert = pyiGlobal.PUBLIC_URL + "images/insertline_sbutton.gif"
const img_delete = pyiGlobal.PUBLIC_URL + "images/delete_sbutton.gif"
const img_select = pyiGlobal.PUBLIC_URL + "images/checkbox_true.gif"
const img_unselect = pyiGlobal.PUBLIC_URL + "images/checkbox_false.gif"
const img_firstButton = pyiGlobal.PUBLIC_URL + "images/first_button.gif"
const img_lastButton = pyiGlobal.PUBLIC_URL + "images/last_button.gif"
const img_nextButton = pyiGlobal.PUBLIC_URL + "images/next_button.gif"
const img_previousButton = pyiGlobal.PUBLIC_URL + "images/previous_button.gif"
const img_refreshButton = pyiGlobal.PUBLIC_URL + "images/refresh_button.gif"
const img_showAllButton = pyiGlobal.PUBLIC_URL + "images/config.gif"
const img_excel = pyiGlobal.PUBLIC_URL + "images/excel_icon.png" // XH 2022-07-05
const img_filter = pyiGlobal.PUBLIC_URL + "images/search_button.gif"
const img_cancel = pyiGlobal.PUBLIC_URL + "images/cancel_button.gif"
const img_reset = pyiGlobal.PUBLIC_URL + "images/refresh_button.gif"
const img_goToTop = pyiGlobal.PUBLIC_URL + "images/go_to_top.png"
const img_goToBottom = pyiGlobal.PUBLIC_URL + "images/go_to_bottom.png"
const img_tip = pyiGlobal.PUBLIC_URL + "images/tips_icon.gif"
const current_icon = pyiGlobal.PUBLIC_URL + "images/current_sbutton.gif"
const expand_icon = pyiGlobal.PUBLIC_URL + "images/expand_sbutton.gif"

/** The Spreadsheet component props */
export type Props<CellType extends Types.CellBase> = {
  ref: any
  tableParams: any
  editable: boolean
  /** Class to be added to the spreadsheet element */
  className?: string
  /** Use dark colors that complenent dark mode */
  darkMode?: boolean
  /**
   * Labels to use in row indicators.
   * Defaults to: row index labels.
   */
  rowLabels?: string[]
  /**
   * If set to true, hides the row indicators of the spreadsheet.
   * Defaults to: `false`.
   */
  hideRowIndicators?: boolean
  /**
   * If set to true, hides the column indicators of the spreadsheet.
   * Defaults to: `false`.
   */
  hideColumnIndicators?: boolean
  pluginList?: any // XH 2022-04-24
  /** refresh page. */
  refresh?: any
  // Custom Components
  /** Component rendered above each column. */
  ColumnIndicator?: Types.ColumnIndicatorComponent
  /** Component rendered in the corner of row and column indicators. */
  CornerIndicator?: Types.CornerIndicatorComponent
  /** Component rendered next to each row. */
  RowIndicator?: Types.RowIndicatorComponent
  /** The Spreadsheet's table component. */
  Table?: Types.TableComponent
  /** The Spreadsheet's row component. */
  Row?: Types.RowComponent
  /** The spreadsheet's header row component */
  HeaderRow?: Types.HeaderRowComponent
  /** The spreadsheet's footer row component */
  FooterRow?: Types.FooterRowComponent
  /** The Spreadsheet's cell component. */
  Cell?: Types.CellComponent<CellType>
  /** Component rendered for cells in view mode. */
  DataViewer?: Types.DataViewerComponent<CellType>
  DataViewerColumn01?: Types.DataViewerComponent<CellType>
  /** Component rendered for cells in edit mode. */
  DataEditor?: Types.DataEditorComponent<CellType>
  // Handlers
  /** Callback called on key down inside the spreadsheet. */
  onKeyDown?: (event: React.KeyboardEvent) => void
  /** Callback called when the Spreadsheet's data changes. */
  onChange?: (data: Matrix.Matrix<CellType>) => void
  /** Callback called when the Spreadsheet's edit mode changes. */
  onModeChange?: (mode: Types.Mode) => void
  onEditable?: (editable: boolean) => void
  /** Callback called when the Spreadsheet's selection changes. */
  onSelect?: (selected: Point.Point[]) => void
  /** Callback called when Spreadsheet's active cell changes. */
  onActivate?: (active: Point.Point) => void
  /** Callback called when the Spreadsheet loses focus */
  onBlur?: () => void
  onCellCommit?: (prevCell: null | CellType, nextCell: null | CellType, coords: null | Point.Point) => void
}

/**
 * The Spreadsheet component
 */
const TableFg = forwardRef(<CellType extends Types.CellBase>(props: Props<CellType>, ref: Ref<any>): React.ReactElement => {
  const {
    tableParams,
    editable: screenEditable,
    className,
    darkMode,
    rowLabels,
    hideColumnIndicators,
    hideRowIndicators,
    pluginList,
    onKeyDown,
    Table = DefaultTable,
    Row = DefaultRow,
    HeaderRow = DefaultHeaderRow,
    FooterRow = DefaultFooterRow,
    DataEditor = DefaultDataEditor,
    DataViewer = DefaultDataViewer,
    onChange = () => {},
    onModeChange = () => {},
    onEditable = () => {},
    onSelect = () => {},
    onActivate = () => {},
    onBlur = () => {},
    onCellCommit = () => {},
  } = props

  useImperativeHandle(ref, () => {
    // send data to parent component
    return {
      data: handleData(state.data, fields),
    }
  })
  const handleData = (data: Matrix.Matrix<CellType>, fields: string[]): any => {
    let attrArr = []
    for (let index = 0; index < fields.length; index++) {
      const element = fields[index]
      if (
        element &&
        element !== pyiLocalStorage.globalParams.TABLE_ROW_STATUS &&
        element !== pyiLocalStorage.globalParams.SELECTABLE_TABLE_ROW_STATUS
      ) {
        attrArr.push(element)
      }
    }
    const firstAttr = selectionMode ? pyiLocalStorage.globalParams.SELECTABLE_TABLE_ROW_STATUS : pyiLocalStorage.globalParams.TABLE_ROW_STATUS
    attrArr = [firstAttr, ...attrArr]
    // get table data
    const dataArr = []

    data.forEach((rowItem, rowIndex) => {
      const dataItemArr = []
      dataItemArr.push(state.data[rowIndex][1]?.value ? state.data[rowIndex][1]?.value : "")
      for (let index = 0; index < rowItem.length; index++) {
        if (index === 1) {
          continue
        }
        let value = rowItem[index]?.comboKey !== undefined ? rowItem[index]?.comboKey : rowItem[index]?.value ? rowItem[index]?.value : null
        if (checkBoxPrams[index - 2] && checkBoxPrams[index - 2].stateNumber === 2) {
          value = String(value).toLocaleLowerCase() === "true" ? true : false
        }
        dataItemArr.push(value)
      }
      dataArr.push(dataItemArr)
    })
    const jsonData = { attr: attrArr, data: dataArr }
    // console.log("getTableData", jsonData)
    return jsonData
  }

  const TABLE = pyiLocalStorage.globalParams.TABLE_TYPE
  const RESULT_TABLE = pyiLocalStorage.globalParams.TABLE_TYPE_RESULT

  const sortNewRows = tableParams.additionalProps?.sortNewRows
  const tableScrollHeight = tableParams.additionalProps?.tableHeight ? parseInt(tableParams.additionalProps.tableHeight, 10) : null

  //init page
  const [tableData, setTableData] = useState([])
  const [pluginParams, setPluginParams] = useState([0])
  const [pageNation, setPageNation] = React.useState(1) // Actual page number
  const [pageSelect, setPageSelect] = React.useState(1) // Selected page number
  const [totalPageNm, setTotalPageNm] = React.useState(1) // Total page numbers
  const [messageFlag, setMessageFlag] = React.useState(true) // Server-side paging flags whether the current page has been modified or not
  const [preShowRange, setPreShowRange] = React.useState([]) // When filtering data in the paging case, the showRange before filtering is saved, which is used to exit filtering and fallback when filtering is initialized.
  const [filterRow, setFilterRow] = React.useState(false) // Whether to display the filterRow
  const [filterContent, setFilterContent] = React.useState({}) // Save the filterRow search
  const [showTopIcon, setShowTopIcon] = React.useState(false) // Whether or not to display the icon to the right of the headerRow
  const [showBottomIcon, setShowBottomIcon] = React.useState(false) // Whether or not to display the icon to the right of the lastRow
  const [showColumns, setShowColumns] = React.useState([]) // ColumnNumber of the visible column
  const [scrollTimes, setScrollTimes] = React.useState(0) // Scrollbar scrolling times
  const [tableParamsData, setTableParamsData] = React.useState([]) // Raw data passed to the table from the backend
  const [tbodyStylePrams, setTbodyStylePrams] = React.useState([]) // The table body style settings that are processed for use by the cell component.
  const [pluginActiveRows, setPluginActiveRows] = React.useState([]) // The id of the active row of the table plugin column
  const [scrollPrams, setScrollPrams] = useState({
    tableHeight: tableScrollHeight,
    handleScroll: null,
  }) // Parameters of the scrollbar

  const type = tableParams.type
  const name = tableParams.name
  const caption = tableParams.caption

  const showRowNo = tableParams.showRowNo ? tableParams.showRowNo : true
  const insertable = type === RESULT_TABLE ? false : screenEditable && tableParams.insertable
  const deletable = screenEditable && tableParams.deletable
  const selectionMode = type === RESULT_TABLE && screenEditable ? tableParams.selectionMode : null
  const editable = type === RESULT_TABLE ? false : screenEditable && tableParams.editable
  const highlightRow = tableParams.highlightRow
  const pageSize = parseInt(tableParams.pageSize)
  const pageType = tableParams.pageType
  const beforeDisplayAdapter = tableParams.beforeDisplayAdapter

  const fields = tableUtil.parseTableDataField(tableParams, selectionMode)
  const comboPrams = tableUtil.getTableComboBoxPrams(tableParams)
  const dateBoxCols = tableUtil.getTableDateBoxColsInfo(tableParams)
  const disableCols = tableUtil.getTableDisableColNos(tableParams)
  const inVisibleCols = tableUtil.getTableInVisibleColNos(tableParams)
  const dialogPrams = tableUtil.getTableDialogPrams(fields, tableParams)
  const htmlCols = tableUtil.getTableHtmlColNos(tableParams)
  const textareaCols = tableUtil.getTableTextAreaColNos(tableParams)
  const buttonPrams = tableUtil.getTableButtonPrams(fields, tableParams)
  const advancedSelectionPrams = tableUtil.getTableAdvancedSelectionPrams(fields, tableParams)
  const checkBoxPrams = tableUtil.getTableCheckBoxPrams(tableParams)
  const formatPrams = tableUtil.getTableFormatPrams(tableParams)
  const theadStylePrams = tableUtil.getTableHeadStylePrams(tableParams)
  const tfootStylePrams = tableUtil.getTableFootStylePrams(tableParams)
  const headerPrams = tableUtil.getTableHeaderPrams(tableParams)
  const footerPrams = tableUtil.getTableFooterPrams(tableParams)

  // gat table data
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)
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
          let data = result.data
          if (data) {
            if (pageType !== pyiGlobal.SERVER_PAGING) {
              setTableParamsData(data)
              setTbodyStylePrams(tableUtil.getTableBodyStylePrams(name, tableParams.fields, data, tableParams.style))
              setPluginActiveRows(tableUtil.getTablePluginActiveRows(data, fields, pluginParams))
              let pageData = tableUtil.parseTableData(data, fields)
              if (pageData.length > pyiGlobal.PAGE_MAX_ROWS) {
                showInfoMessage("Display up to 1000 rows in a table.")
                pageData = pageData.slice(0, 1000)
              }
              setTableData(pageData)
              setData(pageData, headerPrams.headerLabels)
              const dataLength = pageData.length
              setTotalPageNm(Math.ceil(dataLength / pageSize))
            }
          }
        }
      })
  }
  useEffect(() => {
    if (tableParams.data) {
      if (pageType !== pyiGlobal.SERVER_PAGING) {
        setTableParamsData(tableParams.data)
        setTbodyStylePrams(tableUtil.getTableBodyStylePrams(name, tableParams.fields, tableParams.data, tableParams.style))
        setPluginActiveRows(tableUtil.getTablePluginActiveRows(tableParams.data, fields, pluginParams))
        let pageData = tableUtil.parseTableData(tableParams.data, fields)
        if (pageData.length > pyiGlobal.PAGE_MAX_ROWS) {
          showInfoMessage("Display up to 1000 rows in a table.")
          pageData = pageData.slice(0, 1000)
        }
        setTableData(pageData)
        setData(pageData, headerPrams.headerLabels)

        const dataLength = pageData.length
        setTotalPageNm(Math.ceil(dataLength / pageSize))
      }
    } else if (pageType !== pyiGlobal.SERVER_PAGING) {
      fetchData()
    }
  }, [tableParams.data, tableParams.dataUrl])

  useEffect(() => {
    if (pluginList && tableParams.pluginParams) {
      setPluginParams(tableUtil.getTablePluginParams(fields, tableParams.pluginParams)) // Get a list from the backend that holds the number of columns of data passed by the plugin
    }
  }, [pluginList])

  // XH 2022-04-13 start
  // Add two blank columns in columnLabels
  const initialState = React.useMemo(
    () =>
      ({
        ...INITIAL_STATE,
        editable: editable,
        headerLabels: headerPrams.headerLabels,
        headerLabelTips: headerPrams.headerLabelTips, // YL, 2023-05-06 add tooltip
        disableCols: disableCols, // XH 2022-04-28
        inVisibleCols: inVisibleCols, // XH 2022-05-09 visible
        sortNewRows: sortNewRows,
      } as Types.StoreState<CellType>),
    [tableData, editable]
  )

  const reducerElements = React.useReducer(reducer as unknown as React.Reducer<Types.StoreState<CellType>, any>, initialState)

  const [state, dispatch] = reducerElements

  const refreshTable = React.useCallback((refreshFlag: boolean) => dispatch(Actions.refreshTable(refreshFlag)), [dispatch])
  React.useEffect(() => {
    refreshTable(false)
    if (props.refresh && state.refreshFlag) {
      props.refresh()
    }
  }, [state.refreshFlag])

  const size = React.useMemo(() => {
    return calculateSpreadsheetSize(state.data, rowLabels, state.headerLabels)
  }, [state.data, rowLabels, state.headerLabels])

  // XH 2022-04-13 end

  const mode = state.mode
  const rootRef = React.useRef<HTMLDivElement>(null)
  const prevStateRef = React.useRef<Types.StoreState<CellType>>({
    ...INITIAL_STATE,
    data: tableData,
    selected: null,
    copied: PointMap.from([]),
    lastCommit: null,
  })

  const copy = React.useCallback(() => dispatch(Actions.copy()), [dispatch])
  const cut = React.useCallback(() => dispatch(Actions.cut()), [dispatch])
  const paste = React.useCallback((data) => dispatch(Actions.paste(data, comboPrams, formatPrams)), [dispatch, comboPrams])
  const onKeyDownAction = React.useCallback((event) => dispatch(Actions.keyDown(event)), [dispatch])
  const onKeyPress = React.useCallback((event) => dispatch(Actions.keyPress(event)), [dispatch])
  const onDragStart = React.useCallback(() => dispatch(Actions.dragStart()), [dispatch])
  const onDragEnd = React.useCallback(() => dispatch(Actions.dragEnd()), [dispatch])
  const setData = React.useCallback(
    (data, headerLabels) => dispatch(Actions.setData(data, textareaCols, comboPrams, headerLabels, formatPrams)),
    [dispatch, comboPrams]
  )
  const blur = React.useCallback(() => dispatch(Actions.blur()), [dispatch])

  const setShowRange = React.useCallback((showRange) => dispatch(Actions.setShowRange(showRange)), [dispatch])
  const addRow = React.useCallback(() => dispatch(Actions.addRow(comboPrams)), [dispatch, comboPrams])
  const addRowAndShowData = () => {
    if (filterRow) {
      resetFilterRow()
    }
    addRow()
    if (pageType === pyiGlobal.CLIENT_PAGING) {
      const theLastPage = Math.ceil((state.data.length + 1) / pageSize)
      setPageSelect(theLastPage)
      setPageNation(theLastPage)
      setTotalPageNm(theLastPage)
      setShowRange(range(state.data.length + 1, (theLastPage - 1) * pageSize))
      setPreShowRange(range(state.data.length + 1, (theLastPage - 1) * pageSize))
    }
    setTbodyStylePrams(tableUtil.getAddRowStyle(tbodyStylePrams, tableParams.fields))
  }
  const delRow = React.useCallback((point) => dispatch(Actions.delRow(point)), [dispatch])
  const delRowAndShowData = (point: Point.Point) => {
    delRow(point)
    if (pageType === pyiGlobal.CLIENT_PAGING && state.data[point.row][1].value === "+") {
      const theLastRow = state.showRange.slice(-1)[0]
      const theCurrentPage = Math.ceil(theLastRow / pageSize)
      setPageSelect(theCurrentPage)
      setPageNation(theCurrentPage)
      if (theCurrentPage * pageSize >= state.data.length) {
        setShowRange(range(state.data.length - 1, (theCurrentPage - 1) * pageSize))
        setPreShowRange(range(state.data.length - 1, (theCurrentPage - 1) * pageSize))
      } else {
        setShowRange(range(theCurrentPage * pageSize, (theCurrentPage - 1) * pageSize))
        setPreShowRange(range(theCurrentPage * pageSize, (theCurrentPage - 1) * pageSize))
      }
    }
    if (state.data[point.row][1].value === "+") {
      tbodyStylePrams.pop()
      setTbodyStylePrams(tbodyStylePrams)
    }
  }

  const selectAll = React.useCallback(() => dispatch(Actions.selectAll()), [dispatch])
  const selectRow = React.useCallback((rowNumber, selectionMode) => dispatch(Actions.selectRow(rowNumber, selectionMode)), [dispatch])
  const activate = React.useCallback((point: Point.Point) => dispatch(Actions.activate(point)), [dispatch])
  const edit = React.useCallback(() => dispatch(Actions.edit()), [dispatch])
  const activateInput = (point: Point.Point) => {
    activate(point)
    edit()
  }
  const setEditable = React.useCallback((editable) => dispatch(Actions.setEditable(editable)), [dispatch])

  React.useEffect(() => {
    setEditable(editable)
  }, [editable])

  React.useEffect(() => {
    const prevState = prevStateRef.current
    if (state.lastCommit && state.lastCommit !== prevState.lastCommit) {
      for (const change of state.lastCommit) {
        onCellCommit(change.prevCell, change.nextCell, state.active)
      }
    }

    if (state.data !== prevState.data) {
      // Call on change only if the data change internal
      if (state.data !== tableData) {
        onChange(state.data)
      }
    }

    if (state.mode !== prevState.mode) {
      onModeChange(state.mode)
    }

    if (state.editable !== prevState.editable) {
      onEditable(state.editable)
    }

    // XH 2022-04-28 start
    if (state.selected !== prevState.selected) {
      const points = Selection.getPoints(state.selected, state.data)
      onSelect(points)
    }
    // XH 2022-04-28 end

    if (state.active !== prevState.active) {
      if (state.active) {
        onActivate(state.active)
      } else {
        const root = rootRef.current
        if (root && isFocusedWithin(root) && document.activeElement) {
          ;(document.activeElement as HTMLElement).blur()
        }
        onBlur()
      }
    }

    prevStateRef.current = state
  }, [tableData, state, onActivate, onBlur, onCellCommit, onChange, onModeChange, onEditable, onSelect, rowLabels, state.headerLabels])

  const clip = React.useCallback(
    (event: ClipboardEvent): void => {
      const { data, selected } = state
      const selectedData = Selection.getSelectionFromMatrix(selected, data) // XH 2022-04-28
      const csv = getCSV(selectedData)
      writeTextToClipboard(event, csv)
    },
    [state]
  )

  const handleCut = React.useCallback(
    (event: ClipboardEvent) => {
      if (shouldHandleClipboardEvent(rootRef.current, mode)) {
        event.preventDefault()
        event.stopPropagation()
        clip(event)
        cut()
      }
    },
    [mode, clip, cut]
  )

  const handleCopy = React.useCallback(
    (event: ClipboardEvent) => {
      if (shouldHandleClipboardEvent(rootRef.current, mode)) {
        event.preventDefault()
        event.stopPropagation()
        clip(event)
        copy()
      }
    },
    [mode, clip, copy]
  )

  const handlePaste = React.useCallback(
    (event: ClipboardEvent) => {
      if (shouldHandleClipboardEvent(rootRef.current, mode)) {
        event.preventDefault()
        event.stopPropagation()
        if (event.clipboardData) {
          const text = readTextFromClipboard(event)
          paste(text)
        }
      }
    },
    [mode, paste]
  )

  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent) => {
      if (onKeyDown) {
        onKeyDown(event)
      }
      // Do not use event in case preventDefault() was called inside onKeyDown
      if (!event.defaultPrevented) {
        // Only disable default behavior if an handler exist
        if (hasKeyDownHandler(state, event)) {
          event.nativeEvent.preventDefault()
        }
        onKeyDownAction(event)
      }
    },
    [state, onKeyDown, onKeyDownAction]
  )

  const handleMouseUp = React.useCallback(() => {
    onDragEnd()
    document.removeEventListener("mouseup", handleMouseUp)
  }, [onDragEnd])

  const handleMouseMove = React.useCallback(
    (event: React.MouseEvent) => {
      if (state.mode === "edit") {
        return
      }

      if (!state.dragging && event.buttons === 1) {
        // LHH 2022-05-20 start: fix the bug that the dragging affects the calendar
        // if (state.active != null && typeof dateBoxCols != "undefined") {
        //   for (var i = 0; i < dateBoxCols.length; i++) {
        //     if (dateBoxCols[i].colIndex === state.active.column) {
        //       return
        //     }
        //   }
        // }
        // LHH 2022-05-20 end
        onDragStart()
        document.addEventListener("mouseup", handleMouseUp)
      }
    },
    [state, onDragStart, handleMouseUp]
  )

  const handleBlur = React.useCallback(
    (event) => {
      const { currentTarget } = event
      setTimeout(() => {
        if (!isFocusedWithin(currentTarget)) {
          blur()
        }
      }, 0)
    },
    [blur]
  )

  const Cell = React.useMemo(() => {
    // @ts-ignore
    return enhanceCell(props.Cell || DefaultCell)
  }, [props.Cell])

  const RowIndicator = React.useMemo(() => enhanceRowIndicator(props.RowIndicator || DefaultRowIndicator), [props.RowIndicator])

  const ColumnIndicator = React.useMemo(() => enhanceColumnIndicator(props.ColumnIndicator || DefaultColumnIndicator), [props.ColumnIndicator])
  // XH 2022-04-28 end

  React.useEffect(() => {
    document.addEventListener("cut", handleCut)
    document.addEventListener("copy", handleCopy)
    document.addEventListener("paste", handlePaste)

    return () => {
      document.removeEventListener("cut", handleCut)
      document.removeEventListener("copy", handleCopy)
      document.removeEventListener("paste", handlePaste)
    }
  }, [handleCut, handleCopy, handlePaste])

  React.useEffect(() => {
    let columns = []
    range(size.columns - 2).forEach((column: number) => {
      if (state.inVisibleCols.indexOf(column + 2) === -1) {
        columns.push(column)
      }
    })
    setShowColumns(columns)
  }, [size.columns, state.inVisibleCols])

  const getPageDataWithServer = async (pageNum: number | undefined, ignoreModifyFlag?: boolean) => {
    let modifyFlag = 0
    state.data.forEach((row) => {
      if (row[1].value !== "") {
        modifyFlag += 1
      }
    })

    if (modifyFlag !== 0 && messageFlag && !ignoreModifyFlag) {
      showInfoMessage("There are unsaved changes on the current page, continuing to page will lose them")
      setMessageFlag(false)
      return
    }
    if (modifyFlag !== 0) {
      setMessageFlag(true) // If this page has changed, a prompt will appear when you turn the page
      modifyFlag = 0
      // clearMessage()
    }

    // call api
    const key = "PAGEABLE_" + name + "_pageNum"
    let data = {}
    data[key] = pageNum

    if (!tableParams.dataUrl) {
      showErrorMessage("DataUrl not found when fetching paging data on server side, please check.")
      pyiLogger.error("DataUrl not found when fetching paging data on server side", true)
      return
    }
    try {
      Loading.show()
      await HttpPost(tableParams.dataUrl, JSON.stringify(data))
        .then((response) => response.json())
        .then((result) => {
          if (validateResponse(result, true)) {
            let data = result.data
            if (data) {
              let serverPageData = []
              if (data["data"]) {
                serverPageData = data["data"]
                if (serverPageData.length === 0 && pageNum !== 0 && pageNum !== 1) {
                  getPageDataWithServer(1)
                  return
                }

                if (data["cssStyle"]) {
                  setTbodyStylePrams(tableUtil.getTableBodyStylePrams(name, tableParams.fields, data["data"], data["cssStyle"]))
                } else {
                  setTbodyStylePrams(tableUtil.getTableBodyStylePrams(name, tableParams.fields, data["data"], tableParams.style))
                }
              }

              setTableParamsData(serverPageData)
              setPluginActiveRows(tableUtil.getTablePluginActiveRows(serverPageData, fields, pluginParams))
              let pageData = tableUtil.parseTableData(serverPageData, fields)
              if (pageData.length > pyiGlobal.PAGE_MAX_ROWS) {
                showInfoMessage("Display up to 1000 rows in a table.")
                pageData = pageData.slice(0, 1000)
              }
              setTableData(pageData)
              setData(pageData, headerPrams.headerLabels)
              if (filterRow) {
                setNewShowRange(range(serverPageData.length, 0)) // If there is a filterRow, filter the fetched data
              } else {
                setShowRange(range(serverPageData.length, 0))
              }
              setTotalPageNm(Math.ceil(data["paginatorDataAmount"] / pageSize))
              if (pageNum !== undefined) {
                setPageSelect(pageNum)
                setPageNation(pageNum)
              }
            }
          }
        })
    } catch (error) {
      Loading.remove()
      pyiLogger.error("Load screen error: " + error, true)
    } finally {
      Loading.remove() // can't delete
    }
  }

  const getPageDataWithClient = (pageNum: number | undefined) => {
    if (pageNum !== undefined) {
      setPageSelect(pageNum)
      setPageNation(pageNum)
      if (pageNum === 0) {
        setShowRange(range(state.data.length, 0))
        setPreShowRange(range(state.data.length, 0)) // Show all data
      } else {
        const start = (pageNum - 1) * pageSize
        let end = 0
        if (pageNum === totalPageNm) {
          end = state.data.length
        } else {
          end = pageNum * pageSize
        }
        setShowRange(range(end, start))
        setPreShowRange(range(end, start))
      }
    }
  }

  const getTheFirstPage = () => {
    if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(1)
    } else if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(1)
    }
  }

  const getPreviousPage = () => {
    if (pageNation === 0) {
      return
    }
    if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(Number(pageNation) - 1)
    } else if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(Number(pageNation) - 1)
    }
  }

  const getNextPage = () => {
    if (pageNation === 0) {
      return
    }
    if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(Number(pageNation) + 1)
    } else if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(Number(pageNation) + 1)
    }
  }

  const getTheLastPage = () => {
    if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(totalPageNm)
    } else if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(totalPageNm)
    }
  }

  const setPageNum = (event: any) => {
    const value = event.target.value.trim()
    const numericValue = Number(value)
    setPageSelect(numericValue)
  }

  const refreshPage = () => {
    if (filterRow) {
      resetFilterRow()
    }
    if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(Number(pageSelect))
    } else if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(Number(pageSelect))
    }
  }

  const showAllData = () => {
    if (filterRow) {
      resetFilterRow()
    }
    if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(0)
    } else if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(0)
    }
  }

  React.useEffect(() => {
    if (preShowRange.slice(-1)[0] >= tableData.length) {
      let newShowRange = []
      preShowRange.forEach((rowNumber) => {
        if (rowNumber < tableData.length) {
          newShowRange.push(rowNumber)
        }
      })
      setShowRange(newShowRange)
      setPreShowRange(newShowRange)
      if (newShowRange.length === 0 && pageType === pyiGlobal.CLIENT_PAGING && pageNation > 1) {
        getPageDataWithClient(pageNation - 1)
      }
      if (newShowRange.length === 0 && pageType === pyiGlobal.SERVER_PAGING && pageNation > 1) {
        getPageDataWithServer(pageNation - 1)
      }
    }
  }, [tableData]) // Display the previous page after deleting all rows in a page when paging.

  React.useEffect(() => {
    if (pageType === pyiGlobal.CLIENT_PAGING) {
      getPageDataWithClient(pageNation)
    } else {
      setShowRange(range(state.data.length, 0))
      setPreShowRange(range(state.data.length, 0))
    }
  }, [state.data.length]) // triggered when add row or delete row, count the new total page number.

  React.useEffect(() => {
    if (filterRow) {
      resetFilterRow()
    }
    if (pageType === pyiGlobal.SERVER_PAGING) {
      getPageDataWithServer(pageNation, true)
    }
  }, [tableParams]) // Clear the search when the page is refreshed; if there is a pagination you need to re-fetch the current pagination's data

  const filterData = () => {
    // Filter current page
    let preShowRange = []
    if (pageType === pyiGlobal.CLIENT_PAGING) {
      if (pageNation === totalPageNm) {
        preShowRange = range(state.data.length, (pageNation - 1) * pageSize)
      } else {
        preShowRange = range(pageNation * pageSize, (pageNation - 1) * pageSize)
      }
    } else {
      preShowRange = range(state.data.length, 0)
    }
    setNewShowRange(preShowRange)
  }

  const setNewShowRange = (showRange: number[], e?: any, index?: number) => {
    if (e) {
      filterContent[index] = e.target.value
      setFilterContent(filterContent)
    }

    // Filter the specified showRange
    if (state.data.length <= showRange.slice(-1)[0]) {
      return
    }
    let preShowRange = showRange
    let newShowRange = []
    showColumns.length &&
      showColumns.forEach((column: number, index: number) => {
        if (filterContent[index] && column >= 0) {
          const search = filterContent[index].toLowerCase()
          preShowRange.forEach((rowNumber: number) => {
            let cell = state.data[rowNumber][column + 2]
            let data: string
            if (!cell.value) {
              data = ""
            } else {
              data = cell.value.toLowerCase()
            }
            if (data.indexOf(search) !== -1) {
              newShowRange.push(rowNumber)
            }
          })
          preShowRange = newShowRange
          newShowRange = []
        }
      })
    setShowRange(preShowRange)
  }

  React.useEffect(() => {
    if (!filterRow) {
      return
    }
    if (pageType === pyiGlobal.SERVER_PAGING) {
      filterData()
    } else {
      setNewShowRange(preShowRange)
    }
  }, [pageNation]) // Refiltering when turning pages

  const showFilterRow = () => {
    setFilterRow(true)
  }
  const hideFilterRow = () => {
    setFilterRow(false)
    setFilterContent({})
    if (pageType === pyiGlobal.CLIENT_PAGING) {
      setShowRange(preShowRange) // Show last unfiltered showRange when hiding search bar
    } else {
      setShowRange(range(state.data.length, 0)) // Show all data showRange when hiding search bar
    }
  }
  const resetFilterRow = () => {
    if (pageType === pyiGlobal.CLIENT_PAGING) {
      setShowRange(preShowRange)
    } else {
      setShowRange(range(state.data.length, 0))
    }
    setFilterContent({})
  }
  React.useEffect(() => {
    if (state.active && state.active.row === -1) {
      const inputCell = document.getElementById("cell_-1_" + (state.active.column - 2) + " " + name)
      if (inputCell) {
        const input = inputCell.querySelector("input")
        input.focus() // Use tab or shift+tab to activate the corresponding search box when the search bar is eh moved.
      }
    }
  }, [state.active])

  const handleScroll = React.useCallback(() => {
    setScrollTimes((prevScrollTimes) => prevScrollTimes + 1)
  }, [])
  const enterScrollingMode = () => {
    let tbody = document.getElementById("tbody " + name) as HTMLElement
    const newTableHeight = tableScrollHeight ? tableScrollHeight : 400
    if (tbody) {
      const tbodyHeight = tbody.getBoundingClientRect().height
      if (tbodyHeight < newTableHeight) {
        return
      }
    }
    setScrollPrams({
      tableHeight: newTableHeight,
      handleScroll: handleScroll,
    })
  }
  const exitScrollingMode = () => {
    setScrollPrams({
      tableHeight: null,
      handleScroll: handleScroll,
    })
  }

  React.useEffect(() => {
    let newTableHeight = tableScrollHeight
    let tbody = document.getElementById("tbody " + name) as HTMLElement
    if (tbody && newTableHeight) {
      const tbodyHeight = tbody.getBoundingClientRect().height
      if (tbodyHeight < newTableHeight) {
        newTableHeight = null
      }
    }
    setScrollPrams({
      tableHeight: newTableHeight,
      handleScroll: handleScroll,
    })
  }, [state.showRange, name, handleScroll, tableScrollHeight])

  const getInputWidth = (column: number) => {
    let width = 0
    const header = getLastHeader(headerPrams.headerLines, column)
    const input = document.getElementById("cell_-1_" + column + " " + name)
    if (header && !input) {
      width = header.offsetWidth - 10
    } else if (input) {
      width = input.querySelector("input").offsetWidth
    }
    return width // Set the width of the input box by the column corresponding to the input box in the header.
  }
  const getLastHeader = (headerLines: number[], column: number) => {
    let lastHeader
    headerLines.forEach((line) => {
      const header = document.getElementById("cell_-" + line + "_" + column + " " + name)
      if (header && lastHeader && header.offsetWidth < lastHeader.offsetWidth) {
        lastHeader = header
      } else if (header) {
        lastHeader = header
      }
    })
    return lastHeader
  }

  React.useEffect(() => {
    if (!beforeDisplayAdapter) {
      return
    }
    try {
      const pramsIndexLeft = beforeDisplayAdapter.indexOf("(")
      const pramsIndexRight = beforeDisplayAdapter.indexOf(")")
      const funcIndexLeft = beforeDisplayAdapter.indexOf("{")
      const funcIndexRight = beforeDisplayAdapter.lastIndexOf("}")
      const prams = beforeDisplayAdapter.slice(pramsIndexLeft + 1, pramsIndexRight).split(",")
      const func = beforeDisplayAdapter.slice(funcIndexLeft + 1, funcIndexRight)

      // eslint-disable-next-line no-new-func
      const __tableDisplay = new Function(prams[0].trim(), prams[1].trim(), prams[2].trim(), prams[3].trim(), prams[4].trim(), func)
      let tableData = []
      state.showRange &&
        state.showRange.forEach((row) => {
          tableData.push(tableParamsData[row])
        })
      const pluginColNm = pluginList ? pluginList.length : 0

      state.showRange &&
        state.showRange.forEach((rowIndex) => {
          const rowData = tableParamsData[rowIndex] ? tableParamsData[rowIndex] : []
          for (let columnIndex = 0; columnIndex < size.columns + pluginColNm; columnIndex++) {
            const cell = document.getElementById("cell_" + rowIndex + "_" + (columnIndex - 2) + " " + name)
            if (cell) {
              __tableDisplay(tableData, rowData, rowIndex, columnIndex - 2, cell)
            }
          }
        })
    } catch (error) {
      showErrorMessage("Function error, please check: " + error)
    }
  }, [state.showRange, state.data])

  let timeOutFunc1 = null
  let timeOutFunc2 = null
  const showHeaderRowIcon = () => {
    clearTimeout(timeOutFunc1)
    setShowTopIcon(true)
  }
  const showLastRowIcon = () => {
    clearTimeout(timeOutFunc2)
    setShowBottomIcon(true)
  }
  const hideHeaderRowIcon = () => {
    timeOutFunc1 = setTimeout(function () {
      setShowTopIcon(false)
    }, 2000)
  }
  const hideLastRowIcon = () => {
    timeOutFunc2 = setTimeout(function () {
      setShowBottomIcon(false)
    }, 2000)
  }

  const highlightTableRow = (e) => {
    let target = e.target
    while (target && target.nodeName !== "TR") {
      target = target.parentNode
    }
    if (target) {
      target.classList.add("highlight-row")
    }
  }

  const removeHighlightFromRow = (e) => {
    let target = e.target
    while (target && target.nodeName !== "TR") {
      target = target.parentNode
    }
    if (target) {
      target.classList.remove("highlight-row")
    }
  }

  React.useEffect(() => {
    const headerRow = document.getElementById("row_-2 " + name)
    const lastRowNm = state.showRange.slice(-1)[0]
    const lastRow = document.getElementById("row_" + lastRowNm + " " + name)
    const tbody = document.getElementById("tbody " + name)
    if (headerRow && lastRow) {
      headerRow.addEventListener("mouseenter", showHeaderRowIcon)
      lastRow.addEventListener("mouseenter", showLastRowIcon)
      headerRow.addEventListener("mouseleave", hideHeaderRowIcon)
      lastRow.addEventListener("mouseleave", hideLastRowIcon)
      if (highlightRow) {
        tbody.addEventListener("mouseover", highlightTableRow)
        tbody.addEventListener("mouseout", removeHighlightFromRow)
      }

      return () => {
        headerRow.removeEventListener("mouseenter", showHeaderRowIcon)
        headerRow.removeEventListener("mouseleave", hideHeaderRowIcon)
        lastRow.removeEventListener("mouseenter", showLastRowIcon)
        lastRow.removeEventListener("mouseleave", hideLastRowIcon)
        if (highlightRow) {
          tbody.removeEventListener("mouseover", hideHeaderRowIcon)
          tbody.removeEventListener("mouseout", hideLastRowIcon)
        }
      }
    }
  }, [state.showRange]) // Show icon when mouse over column header or last row

  const goToBottom = () => {
    const lastRowNm = state.showRange.slice(-1)[0]
    const lastRow = document.getElementById("row_" + lastRowNm + " " + name)
    if (lastRow) {
      lastRow.scrollIntoView({ block: "center" })
    }
  }
  const goToTop = () => {
    const headerRow = document.getElementById("row_-2 " + name)
    if (headerRow) {
      headerRow.scrollIntoView({ block: "center" })
    }
  }

  const tableNode = React.useMemo(() => {
    if (fields.length !== size.columns) {
      return null
    } else {
      return (
        <Table columns={size.columns} hideColumnIndicators={hideColumnIndicators} tableName={name} scrollPrams={scrollPrams}>
          {/* HeaderRow */}
          {headerPrams.headerLines.map((rowNumber) => (
            <HeaderRow id={"row_-" + rowNumber + " " + name} key={-rowNumber}>
              {showRowNo && rowNumber === 2 ? (
                <ColumnIndicator
                  key={-rowNumber}
                  row={-rowNumber}
                  column={-1}
                  tableName={name}
                  stylePrams={{ rowSpan: headerPrams.headerLines.length }}
                  label={"#"}
                />
              ) : null}
              {type === TABLE
                ? range(size.columns).map((columnNumber) =>
                    rowNumber === 2 && columnNumber === 0 && (insertable || deletable) ? (
                      <ColumnIndicator
                        tableName={name}
                        key={columnNumber}
                        row={-rowNumber}
                        column={columnNumber}
                        stylePrams={{ rowSpan: headerPrams.headerLines.length }}
                        label={
                          insertable ? <img src={img_insert} alt="insert" onClick={addRowAndShowData} style={{ cursor: "pointer" }}></img> : null
                        }
                      />
                    ) : rowNumber === 2 && columnNumber === 1 && (editable || insertable || deletable) ? (
                      <ColumnIndicator
                        tableName={name}
                        key={columnNumber}
                        row={-rowNumber}
                        column={columnNumber}
                        stylePrams={{ rowSpan: headerPrams.headerLines.length }}
                        label={""}
                      />
                    ) : columnNumber > 1 && state.headerLabels ? (
                      inVisibleCols && inVisibleCols.indexOf(columnNumber) !== -1 ? null : (
                        <ColumnIndicator
                          tableName={name}
                          key={columnNumber}
                          row={-rowNumber}
                          column={columnNumber}
                          columnStatus={state.columnStatus[columnNumber]} // XH 2022-07-04 column sort
                          stylePrams={theadStylePrams[columnNumber - 2][rowNumber - 2]}
                          label={columnNumber in state.headerLabels ? state.headerLabels[columnNumber] : null}
                          tip={columnNumber in state.headerLabelTips ? state.headerLabelTips[columnNumber] : null} // YL, 2023-05-06 add tooltip
                        />
                      )
                    ) : null
                  )
                : range(size.columns).map((columnNumber) =>
                    rowNumber === 2 && columnNumber === 1 && selectionMode ? (
                      <ColumnIndicator
                        tableName={name}
                        key={columnNumber}
                        row={-rowNumber}
                        column={columnNumber}
                        stylePrams={{ rowSpan: headerPrams.headerLines.length }}
                        label={
                          selectionMode === pyiGlobal.SELECTION_MODE_MULTIPLE ? (
                            <img
                              src={state.headerLabels[1] === "true" ? img_select : img_unselect}
                              alt="select all"
                              onClick={selectAll}
                              style={{ cursor: "pointer" }}
                            ></img>
                          ) : (
                            ""
                          )
                        }
                      />
                    ) : columnNumber > 1 && state.headerLabels ? (
                      inVisibleCols && inVisibleCols.indexOf(columnNumber) !== -1 ? null : (
                        <ColumnIndicator
                          tableName={name}
                          key={columnNumber}
                          row={-rowNumber}
                          column={columnNumber}
                          columnStatus={state.columnStatus[columnNumber]} // XH 2022-07-04 column sort
                          stylePrams={theadStylePrams[columnNumber - 2][rowNumber - 2]}
                          label={columnNumber in state.headerLabels ? state.headerLabels[columnNumber] : null}
                          tip={columnNumber in state.headerLabelTips ? state.headerLabelTips[columnNumber] : null} // YL, 2023-05-06 add tooltip
                        />
                      )
                    ) : null
                  )}
              {rowNumber === 2
                ? pluginList &&
                  pluginList.map((plugin: any, index: number) => (
                    <plugin.IconHeader
                      key={size.columns + pluginList.indexOf(plugin) + 1}
                      position={"-2_" + (size.columns + index - 2) + " " + name}
                      rowSpan={headerPrams.headerLines.length}
                    />
                  ))
                : null}
            </HeaderRow>
          ))}

          {/* FilterRow */}
          {filterRow ? (
            <Row key={-1} row={-1} tableName={name}>
              {showRowNo ? <th id={"cell_-1_-3 " + name} key={-3} className="Spreadsheet__cell-filter" /> : null}
              {insertable || deletable ? <th id={"cell_-1_-2 " + name} key={-2} className="Spreadsheet__cell-filter" /> : null}
              {editable || insertable || deletable || selectionMode ? (
                <th id={"cell_-1_-1 " + name} key={-1} className="Spreadsheet__cell-filter" />
              ) : null}
              {showColumns.length &&
                showColumns.map((columnNumber, index) => (
                  <td id={"cell_-1_" + columnNumber + " " + name} key={columnNumber} className="Spreadsheet__cell-filter">
                    <input
                      className={"filter_input " + name}
                      style={{ width: getInputWidth(columnNumber) + "px" }}
                      onClick={() => activateInput({ row: -1, column: columnNumber + 2 })}
                      onChange={(e) => setNewShowRange(preShowRange, e, index)}
                      value={filterContent[index] ? filterContent[index] : ""}
                    />
                  </td>
                ))}
              {pluginList && pluginList.map((index: number) => <th key={index} className="Spreadsheet__cell-filter" />)}
            </Row>
          ) : null}

          {/* NormalRow */}
          {state.showRange.map((rowNumber) =>
            state.data[rowNumber] ? (
              <Row key={rowNumber} row={rowNumber} tableName={name}>
                {showRowNo ? (
                  <RowIndicator key={-1} row={rowNumber} column={-1} tableName={name} label={getRowNo(rowNumber, pageSelect, pageType, pageSize)} />
                ) : null}
                {type === TABLE
                  ? range(size.columns).map((columnNumber) =>
                      columnNumber === 0 && (insertable || deletable) ? (
                        <RowIndicator
                          key={columnNumber}
                          row={rowNumber}
                          column={columnNumber}
                          tableName={name}
                          label={
                            deletable || state.data[rowNumber][1].value === "+" ? (
                              <img
                                src={img_delete}
                                alt="delete row"
                                onClick={() => delRowAndShowData({ row: rowNumber, column: columnNumber })}
                                style={{ cursor: "pointer" }}
                              ></img>
                            ) : null
                          }
                        />
                      ) : columnNumber === 1 && (editable || insertable || deletable) ? (
                        <RowIndicator
                          key={columnNumber}
                          row={rowNumber}
                          column={columnNumber}
                          tableName={name}
                          label={state.data[rowNumber][1]?.value}
                        />
                      ) : columnNumber > 1 && DataViewer ? (
                        inVisibleCols && inVisibleCols.indexOf(columnNumber) !== -1 ? null : (
                          <Cell
                            key={columnNumber}
                            row={rowNumber}
                            column={columnNumber}
                            newRow={state.data[rowNumber][1].value === "+" ? true : false}
                            tableName={name}
                            // @ts-ignore
                            DataViewer={DataViewer}
                            stylePrams={tbodyStylePrams[rowNumber]}
                            dialogPrams={dialogPrams}
                            buttonBoxPrams={buttonPrams}
                            advancedSelectionBoxPrams={advancedSelectionPrams}
                            htmlCols={htmlCols}
                            checkBoxPrams={checkBoxPrams}
                            columnStatus={state.columnStatus[columnNumber]} // XH 2022-07-04 column sort
                            scrollTimes={scrollTimes}
                            initialData={tableData}
                            tableHeight={scrollPrams.tableHeight}
                          />
                        )
                      ) : null
                    )
                  : range(size.columns).map((columnNumber) =>
                      columnNumber === 1 && selectionMode ? (
                        <RowIndicator
                          key={columnNumber}
                          row={rowNumber}
                          column={columnNumber}
                          tableName={name}
                          label={
                            <img
                              src={state.data[rowNumber][1].value === "true" ? img_select : img_unselect}
                              alt="select"
                              onClick={() => selectRow(rowNumber, selectionMode)}
                              style={{ cursor: "pointer" }}
                            ></img>
                          }
                        />
                      ) : columnNumber > 1 && DataViewer ? (
                        inVisibleCols && inVisibleCols.indexOf(columnNumber) !== -1 ? null : (
                          <Cell
                            key={columnNumber}
                            row={rowNumber}
                            column={columnNumber}
                            newRow={state.data[rowNumber][1].value === "+" ? true : false}
                            tableName={name}
                            // @ts-ignore
                            DataViewer={DataViewer}
                            stylePrams={tbodyStylePrams[rowNumber]}
                            dialogPrams={dialogPrams}
                            buttonBoxPrams={buttonPrams}
                            advancedSelectionBoxPrams={advancedSelectionPrams}
                            htmlCols={htmlCols}
                            checkBoxPrams={checkBoxPrams}
                            columnStatus={state.columnStatus[columnNumber]} // XH 2022-07-04 column sort
                            scrollTimes={scrollTimes}
                            initialData={tableData}
                            tableHeight={scrollPrams.tableHeight}
                          />
                        )
                      ) : null
                    )}
                {pluginList &&
                  pluginList.map((plugin: any, index: number) =>
                    state.data[rowNumber][1].value !== "+" ? (
                      <plugin.IconCell
                        key={size.columns + pluginList.indexOf(plugin) + 1}
                        id={state.data[rowNumber][pluginParams[index]] ? state.data[rowNumber][pluginParams[index]].value : ""}
                        row={handleRowData(state.data[rowNumber], fields)}
                        position={rowNumber + "_" + (size.columns + index - 2) + " " + name}
                        pluginActiveRows={pluginActiveRows}
                      />
                    ) : (
                      <th
                        key={size.columns + pluginList.indexOf(plugin) + 1}
                        id={"cell_" + rowNumber + "_" + (size.columns + index - 2) + " " + name}
                        className="Spreadsheet__header"
                      ></th>
                    )
                  )}
              </Row>
            ) : null
          )}

          {/* FooterRow */}
          {JSON.stringify(footerPrams) !== "{}" ? (
            <FooterRow id={"row_" + state.data.length + " " + name}>
              {showRowNo ? <ColumnIndicator key={state.data.length} row={state.data.length} column={-1} tableName={name} label={null} /> : null}
              {type === TABLE
                ? range(size.columns).map((columnNumber) =>
                    columnNumber === 0 && (insertable || deletable) ? (
                      <ColumnIndicator tableName={name} key={columnNumber} row={state.data.length} column={columnNumber} label={""} />
                    ) : columnNumber === 1 && (editable || insertable || deletable) ? (
                      <ColumnIndicator tableName={name} key={columnNumber} row={state.data.length} column={columnNumber} label={""} />
                    ) : columnNumber > 1 ? (
                      inVisibleCols && inVisibleCols.indexOf(columnNumber) !== -1 ? null : (
                        <ColumnIndicator
                          tableName={name}
                          key={columnNumber}
                          row={state.data.length}
                          column={columnNumber}
                          stylePrams={tfootStylePrams[columnNumber - 2]}
                          label={getFooterData(footerPrams[columnNumber - 2], columnNumber, state.data, state.showRange)}
                        />
                      )
                    ) : null
                  )
                : range(size.columns).map((columnNumber) =>
                    columnNumber === 1 && selectionMode ? (
                      <RowIndicator tableName={name} key={columnNumber} row={state.data.length} column={columnNumber} label={""} />
                    ) : columnNumber > 1 ? (
                      inVisibleCols && inVisibleCols.indexOf(columnNumber) !== -1 ? null : (
                        <ColumnIndicator
                          tableName={name}
                          key={columnNumber}
                          row={state.data.length}
                          column={columnNumber}
                          stylePrams={tfootStylePrams[columnNumber - 2]}
                          label={getFooterData(footerPrams[columnNumber - 2], columnNumber, state.data, state.showRange)}
                        />
                      )
                    ) : null
                  )}
              {pluginList &&
                pluginList.map((plugin: any, index: number) => (
                  <th
                    id={"cell_" + state.data.length + "_" + (size.columns + index - 2) + " " + name}
                    key={size.columns + pluginList.indexOf(plugin) + 1}
                    className="Spreadsheet__header Spreadsheet__header__column"
                  />
                ))}
            </FooterRow>
          ) : null}
        </Table>
      )
    }
  }, [
    Table,
    scrollTimes,
    size.rows,
    size.columns,
    hideColumnIndicators,
    Row,
    HeaderRow,
    hideRowIndicators,
    pluginList,
    state.headerLabels,
    headerPrams.headerLines,
    ColumnIndicator,
    rowLabels,
    RowIndicator,
    Cell,
    DataViewer,
    editable,
    state.data,
    state.showRange,
    tbodyStylePrams,
  ])

  const activeCellNode = React.useMemo(
    () => (
      <ActiveCell
        DataEditor={DataEditor}
        comboPrams={comboPrams}
        dateBoxCols={dateBoxCols}
        initialData={tableData}
        textareaCols={textareaCols}
        disableCols={disableCols}
        formatPrams={formatPrams}
      />
    ),
    [DataEditor, comboPrams, dateBoxCols, textareaCols, disableCols] // LHH 2022-04-29
  )

  const pageNode = React.useMemo(() => {
    if (pageSize !== null && pageType !== null && pageSize > 0) {
      return (
        <div className="PageSelectDiv" style={{ display: "flex", alignItems: "flex-end", paddingLeft: "3px" }}>
          {pageNation === 1 || pageNation === 0 ? null : <img src={img_firstButton} alt="got to first page" onClick={getTheFirstPage}></img>}
          {pageNation === 1 || pageNation === 0 ? null : <img src={img_previousButton} alt="go to previous page" onClick={getPreviousPage}></img>}
          {pageNation === totalPageNm || pageNation === 0 || totalPageNm === 0 ? null : (
            <img src={img_nextButton} alt="Go to the next page" onClick={getNextPage}></img>
          )}
          {pageNation === totalPageNm || pageNation === 0 || totalPageNm === 0 ? null : (
            <img src={img_lastButton} alt="Go to the last page" onClick={getTheLastPage}></img>
          )}
          &nbsp;
          <select title="select" value={pageSelect} id="pageSelect" onChange={setPageNum} style={{ height: "21px" }}>
            {range(totalPageNm + 1).map((pn) => (
              <option title={String(pn)} key={pn} value={pn} onClick={() => setPageSelect(pn + 1)}>
                {pn === 0 ? "" : pn}
              </option>
            ))}
          </select>
          &nbsp;
          <img src={img_refreshButton} alt="go to the selection page" title="Select" onClick={refreshPage}></img>
          &nbsp;
          <img src={img_showAllButton} alt="show all" title="Show All (Up to 1000 Rows)" onClick={showAllData}></img>
        </div>
      )
    }
  }, [pageNation, pageSelect, pageSize, totalPageNm, messageFlag, state.data, state.showRange, filterRow])

  const topIconNode = React.useMemo(() => {
    let headerHeight = 0
    const head = document.getElementById("thead " + name)
    const filter = document.getElementById("row_-1 " + name)
    if (head) {
      headerHeight = filter ? head.getBoundingClientRect().height - 16.8 : head.getBoundingClientRect().height
    }
    return (
      <div className="topIcons">
        <div className="headerColumn" style={{ height: String(headerHeight) + "px" }}>
          {state.showRange.length !== 0 && showTopIcon ? (
            <img
              id={"top " + name}
              src={img_goToBottom}
              alt="go to bottom"
              onClick={goToBottom}
              title="Go to bottom"
              className="outOfTableIcon"
            ></img>
          ) : null}
          {showTopIcon ? (
            <>
              <img src={img_filter} alt="show filter row" onClick={showFilterRow} title="Filter" className="outOfTableIcon"></img>
              <img
                src={img_excel}
                alt="export"
                title="Export"
                className="outOfTableIcon"
                onClick={() => document.getElementById("table-xls-button").click()}
              ></img>
              <ReactHTMLTableToExcel
                id="table-xls-button"
                className="download-table-xls-button"
                table={"table " + name}
                filename={(caption ? caption.replace(/\ /g, "_") : name) + "-" + moment().format("YYYYMMDDHHmmss")}
                sheet="Sheet1"
              />
              {scrollPrams.tableHeight ? (
                <img src={img_cancel} alt="exit scrolling mode" onClick={exitScrollingMode} title="Exit Scroll Mode" className="outOfTableIcon"></img>
              ) : (
                <img
                  src={img_showAllButton}
                  alt="enter scrolling mode"
                  onClick={enterScrollingMode}
                  title="Enter Scroll Mode"
                  className="outOfTableIcon"
                ></img>
              )}
            </>
          ) : null}
        </div>
        <div className="filterRow">
          {filterRow ? <img src={img_cancel} alt="hide filter row" onClick={hideFilterRow} title="Hide" className="outOfTableIcon"></img> : null}
          {filterRow ? <img src={img_reset} alt="reset filter row" onClick={resetFilterRow} title="Reset" className="outOfTableIcon"></img> : null}
        </div>
      </div>
    )
  }, [filterRow, state.showRange, preShowRange, showTopIcon, scrollPrams])

  const bottomIconNode = React.useMemo(
    () => (
      <div className="bottomIcons">
        {state.showRange.length !== 0 && showBottomIcon ? (
          <div className="lastRow">
            <img id={"bottom " + name} src={img_goToTop} alt="go to top" onClick={goToTop} title="Go to top" className="outOfTableIcon"></img>
          </div>
        ) : null}
      </div>
    ),
    [state.showRange, showBottomIcon]
  )

  const rootNode = React.useMemo(
    () => (
      <form className="div_a" id={name} name={name}>
        <label className="fieldgroup_caption">{caption}</label>
        {(state.data && props.tableParams.pageSize < state.data.length) || pageType === pyiGlobal.SERVER_PAGING ? pageNode : null}{" "}
        {/* YL, 2023-05-29 */}
        <div
          ref={rootRef}
          className={classNames("Spreadsheet", className, {
            "Spreadsheet--dark-mode": darkMode,
          })}
          onKeyPress={onKeyPress}
          onKeyDown={handleKeyDown}
          onMouseMove={handleMouseMove}
          onBlur={handleBlur}
        >
          {tableNode}
          {type !== RESULT_TABLE ? activeCellNode : null}
          {topIconNode}
          {bottomIconNode}
          <Selected />
        </div>
      </form>
    ),
    [className, darkMode, onKeyPress, handleKeyDown, handleMouseMove, handleBlur, tableNode, activeCellNode, topIconNode, bottomIconNode, pageNode]
  )

  return <context.Provider value={reducerElements}>{rootNode}</context.Provider>
})
export default TableFg

// The function that creates the plugin
// XH 2022-04-24 start
export function createIconColumn(myCallback: any, pluginParams: any) {
  const caption = Array.isArray(pluginParams.caption) ? pluginParams.caption[0]?.text || "" : pluginParams.caption || ""
  const IconHeader = (props: any) => (
    <th id={"cell_" + props.position} className="Spreadsheet__header Spreadsheet__header__column" rowSpan={props.rowSpan}>
      <span>{caption}</span>
      {pluginParams.tooltip ? (
        <>
          <img
            src={img_tip}
            alt="tooltip img"
            style={pluginParams.caption ? { paddingLeft: "3px" } : {}}
            data-tooltip-id={"th-tooltip_" + props.position}
            data-tooltip-place="top"
            data-tooltip-content={pluginParams.tooltip}
          ></img>
          {ReactDOM.createPortal(<Tooltip id={"th-tooltip_" + props.position} style={{ zIndex: 2000 }} />, document.getElementById("root"))}
        </>
      ) : null}
    </th>
  )
  const IconCell = (props: any) => (
    <th id={"cell_" + props.position} className="Spreadsheet__header">
      {
        <img
          src={props.pluginActiveRows && props.pluginActiveRows.indexOf(Number(props.id)) !== -1 ? current_icon : expand_icon}
          alt="plugin icon"
          onClick={() => myCallback(props.id, props.row)}
          style={{ cursor: "pointer" }}
        />
      }
    </th>
  )
  return { IconHeader, IconCell }
}
// XH 2022-04-24

function getRowNo(rowNumber, pageSelect, pageType, pageSize) {
  if (pageType !== pyiGlobal.SERVER_PAGING || pageSelect === 0) {
    return rowNumber + 1
  } else {
    return (pageSelect - 1) * pageSize + rowNumber + 1
  }
}
