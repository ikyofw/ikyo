/*
 * @Description:
 * @version:
 * @Author: YL
 * @Date: 2022-04-06 08:55:14
 */
import { createAction } from "@reduxjs/toolkit"
import * as Matrix from "./matrix"
import * as Point from "./point"
import * as Types from "./types"

export const refreshTable = createAction<(refreshFlag: boolean) => { payload: { refreshFlag: boolean } }, "REFRESH_TABLE">(
  "REFRESH_TABLE",
  (refreshFlag) => ({ payload: { refreshFlag } })
)
export const setData = createAction<
  (
    data: Matrix.Matrix<Types.CellBase>,
    textareaCols: any[],
    comboPrams: {
      columns: number[]
      comboData: { [key: string]: any }[]
    },
    headerLabels: any[],
    formatPrams: any[]
  ) => {
    payload: {
      data: Matrix.Matrix<Types.CellBase>
      textareaCols: any[]
      comboPrams: {
        columns: number[]
        comboData: { [key: string]: any }[]
      }
      headerLabels: any[]
      formatPrams: any[]
    }
  },
  "SET_DATA"
>("SET_DATA", (data, textareaCols, comboPrams, headerLabels, formatPrams) => ({
  payload: { data, textareaCols, comboPrams, headerLabels, formatPrams },
}))
export const select = createAction<(point: Point.Point) => { payload: { point: Point.Point } }, "SELECT">("SELECT", (point) => ({
  payload: { point },
}))
export const selectEntireRow = createAction<(row: number, extend: boolean) => { payload: { row: number; extend: boolean } }, "SELECT_ENTIRE_ROW">(
  "SELECT_ENTIRE_ROW",
  (row, extend) => ({ payload: { row, extend } })
)
export const selectEntireColumn = createAction<
  (column: number, extend: boolean) => { payload: { column: number; extend: boolean } },
  "SELECT_ENTIRE_COLUMN"
>("SELECT_ENTIRE_COLUMN", (column, extend) => ({
  payload: { column, extend },
}))
// XH 2022-07-04 start
export const sortByThisColumn = createAction<
  (column: number, extend: boolean) => { payload: { column: number; extend: boolean } },
  "SORT_BY_THIS_COLUMN"
>("SORT_BY_THIS_COLUMN", (column, extend) => ({
  payload: { column, extend },
}))
// XH 2022-07-04 end
export const activate = createAction<(point: Point.Point) => { payload: { point: Point.Point } }, "ACTIVATE">("ACTIVATE", (point) => ({
  payload: { point },
}))
export const setCellData = createAction<
  (
    active: Point.Point,
    data: Types.CellBase,
    initialData?: any[],
    isMultiSelectBox?: boolean
    //getBindingsForCell: Types.GetBindingsForCell
  ) => {
    payload: {
      active: Point.Point
      data: Types.CellBase
      initialData?: any[]
      isMultiSelectBox?: boolean
      //getBindingsForCell: Types.GetBindingsForCell;
    }
  },
  "SET_CELL_DATA"
>("SET_CELL_DATA", (active, data, initialData, isMultiSelectBox?) => ({
  payload: { active, data, initialData, isMultiSelectBox },
}))
export const setCellDimensions = createAction<
  (
    point: Point.Point,
    dimensions: Types.Dimensions
  ) => {
    payload: { point: Point.Point; dimensions: Types.Dimensions }
  },
  "SET_CELL_DIMENSIONS"
>("SET_CELL_DIMENSIONS", (point, dimensions) => ({
  payload: { point, dimensions },
}))
// export const addRow = createAction("ADD_ROW")
export const addRow = createAction<
  (comboPrams: { columns: number[]; comboData: { [key: string]: any }[] }) => {
    payload: {
      comboPrams: {
        columns: number[]
        comboData: { [key: string]: any }[]
      }
    }
  },
  "ADD_ROW"
>("ADD_ROW", (comboPrams) => ({
  payload: { comboPrams },
}))
// export const delRow = createAction("DEL_ROW");
export const delRow = createAction<(point: Point.Point) => { payload: { point: Point.Point } }, "DEL_ROW">("DEL_ROW", (point) => ({
  payload: { point },
}))

export const selectAll = createAction("SELECT_ALL")
export const selectRow = createAction<
  (rowNumber: number, selectionMode: string) => { payload: { rowNumber: number; selectionMode: string } },
  "SELECT_ROW"
>("SELECT_ROW", (rowNumber, selectionMode) => ({ payload: { rowNumber, selectionMode } }))

export const copy = createAction("COPY")
export const cut = createAction("CUT")
export const paste = createAction<
  (
    data: string,
    comboPrams: {
      columns: number[]
      comboData: { [key: string]: any }[]
    },
    formatPrams: any[]
  ) => {
    payload: {
      data: string
      comboPrams: {
        columns: number[]
        comboData: { [key: string]: any }[]
      },
      formatPrams: any[]
    }
  },
  "PASTE"
>("PASTE", (data, comboPrams, formatPrams) => ({
  payload: { data, comboPrams, formatPrams },
}))
export const edit = createAction("EDIT")
export const view = createAction("VIEW")
export const clear = createAction("CLEAR")
export const blur = createAction("BLUR")
export const keyPress = createAction<(event: React.KeyboardEvent) => { payload: { event: React.KeyboardEvent } }, "KEY_PRESS">(
  "KEY_PRESS",
  (event) => ({ payload: { event } })
)
export const keyDown = createAction<(event: React.KeyboardEvent) => { payload: { event: React.KeyboardEvent } }, "KEY_DOWN">("KEY_DOWN", (event) => ({
  payload: { event },
}))
export const dragStart = createAction("DRAG_START")
export const dragEnd = createAction("DRAG_END")
export const commit = createAction<
  (changes: Types.CommitChanges) => {
    payload: { changes: Types.CommitChanges }
  },
  "COMMIT"
>("COMMIT", (changes) => ({ payload: { changes } }))
export const setShowRange = createAction<(showRange: number[]) => { payload: { showRange: number[] } }, "SET_SHOW_RANGE">(
  "SET_SHOW_RANGE",
  (showRange) => ({ payload: { showRange } })
)
export const setEditable = createAction<(editable: boolean) => { payload: { editable: boolean } }, "SET_EDITABLE">("SET_EDITABLE", (editable) => ({
  payload: { editable },
}))
