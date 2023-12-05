import { createReducer } from "@reduxjs/toolkit"
import * as Actions from "./actions"
import * as Matrix from "./matrix"
import * as Point from "./point"
import * as PointMap from "./point-map"
import * as PointRange from "./point-range"
import * as PointSet from "./point-set"
import * as Selection from "./selection" // XH 2022-04-28
import * as Types from "./types"
import { isActive, range } from "./util"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams

export const INITIAL_STATE: Types.StoreState = {
  active: null,
  mode: "view",
  rowDimensions: {},
  columnDimensions: {},
  lastChanged: null,
  hasPasted: false,
  cut: false,
  dragging: false,
  data: [],
  selected: null,
  copied: PointMap.from([]),
  lastCommit: null,
  hasModify: [],
  editable: false,
  disableCols: [],
  inVisibleCols: [], // XH 2022-05-09 visible
  headerLabels: [],
  headerLabelTips: [], // YL, 2023-05-06 Add tooltip
  columnStatus: [], // XH 2022-07-04 column sort
  sortNewRows: false,
  showRange: [],
  refreshFlag: false,
}

const reducer = createReducer(INITIAL_STATE, (builder) => {
  builder.addCase(Actions.refreshTable, (state, action) => {
    const refreshFlag = action.payload.refreshFlag
    return {
      ...state,
      refreshFlag: refreshFlag,
    }
  })
  builder.addCase(Actions.setData, (state, action) => {
    const { data, textareaCols, comboPrams, headerLabels, formatPrams } = action.payload
    const nextActive = state.active && Matrix.has(state.active, data) ? state.active : null
    const nextSelected = Selection.normalize(state.selected, data) // XH 2022-04-28
    const { rows, columns } = Matrix.getSize(data)
    const initialHasModify = Array(rows).fill(false)

    let initialData: any[] = []
    data.forEach((rows) => {
      let newRows = []
      rows.forEach((cell, index) => {
        let newCell = cell
        if (textareaCols.indexOf(index) !== -1 && cell.value) {
          newCell.value = cell.value.trim()
        }
        if (comboPrams['columns'].indexOf(index) !== -1 && cell.value) {
          const comboData = comboPrams['comboData'][comboPrams['columns'].indexOf(index)]
          if (comboData && comboData.data) {
            comboData.data.forEach((item) => {
              if (String(item.value) === String(cell.value)) {
                newCell.value = item.display
                newCell.comboKey = item.value
              }
            })
            if (newCell.comboKey === undefined) {
              newCell.value = ""
            }
          }
        }
        if (formatPrams[index] && newCell.value) {
          const format = formatPrams[index]
          if (!isNaN(newCell.value)) {
            // const index = format.indexOf(".")
            // let newValue = Number(newCell.value) as any
            // if (index !== -1) {
            //   const digits = format.slice(index + 1).length
            //   newValue = newValue.toFixed(Number(digits))
            //   newValue = newValue.replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",")
            // }
            newCell.comboKey = newCell.value
            newCell.value = formatNumber(newCell.value, format)
          } else {
            let newValue = newCell.value
            newValue = dateFormat(newValue, format)
            newCell.value = newValue
          }
        }
        newRows.push(newCell)
      })
      initialData.push(newRows)
    })

    return {
      ...state,
      data: initialData,
      columnStatus: Array(columns).fill(0),
      active: nextActive,
      selected: nextSelected,
      hasModify: initialHasModify,
      headerLabels: headerLabels,
    }
    // YL, 2022-04-20 bug fix - end
  })
  builder.addCase(Actions.setEditable, (state, action) => {
    const editable = action.payload.editable
    return {
      ...state,
      editable: editable,
    }
  })
  builder.addCase(Actions.addRow, (state, action) => {
    const { comboPrams } = action.payload

    const columns = state.headerLabels.length
    let column = Array.from({ length: columns }, () => ({ value: "" }));

    column.forEach((cell, index) => {
      if (comboPrams['columns'].indexOf(index) !== -1) {
        const comboDataIndex = comboPrams['columns'].indexOf(index);
        const comboData = comboPrams['comboData'][comboDataIndex];
        if (comboData && comboData.data) {
          comboData.data.forEach((item) => {
            if (item.isDefault) {
              cell['value'] = item.display;
              cell['comboKey'] = item.value;
            }
          });
        }
      }
    });

    column[1] = { value: "+" }
    return {
      ...state,
      data: [...state.data, column],
      hasModify: [...state.hasModify, true],
      active: null,
      selected: null,
    }
  })
  builder.addCase(Actions.delRow, (state, action) => {
    const { row } = action.payload.point // XH 2022-04-24
    const statusPoint = { row: row, column: 1 } // XH 2022-05-09 隐藏列
    const status = Matrix.get(statusPoint, state.data)?.value
    let preData = state.data

    // if row status is "+", delete this line and modify row status
    // if this line have modified, click delete will make row status change in "" and "~";
    // if this line have not modified, click delete will make row status change in "" and "-";
    let newData = []
    if (status === "+") {
      newData = [...preData.slice(0, row), ...preData.slice(row + 1, preData.length)]
    } else if (status === "" && state.hasModify[row] === false) {
      newData = Matrix.set(statusPoint, { value: "-" }, preData)
    } else if (status === "-" && state.hasModify[row] === false) {
      newData = Matrix.set(statusPoint, { value: "" }, preData)
    } else if (status === "-" && state.hasModify[row] === true) {
      newData = Matrix.set(statusPoint, { value: "~" }, preData)
    } else if (status === "~" && state.hasModify[row] === true) {
      newData = Matrix.set(statusPoint, { value: "-" }, preData)
    }

    return {
      ...state,
      data: newData,
      active: null,
      selected: null,
    }
  })

  // YL, 2022-05-30 NEW add select for result table - start
  builder.addCase(Actions.selectAll, (state) => {
    let flag = state.headerLabels[1] === "true" ? "" : "true"
    let preData = state.data
    let newData = []
    preData.forEach((data) => {
      newData.push([...data.slice(0, 1), { value: flag }, ...data.slice(2, data.length)])
    })

    return {
      ...state,
      data: newData,
      headerLabels: [...state.headerLabels.slice(0, 1), flag, ...state.headerLabels.slice(2, state.headerLabels.length)],
      hasModify: [...state.hasModify, false],
    }
  })
  builder.addCase(Actions.selectRow, (state, action) => {
    const { rowNumber, selectionMode } = action.payload
    const statusPoint = { row: rowNumber, column: 1 }
    const newSelected = Matrix.get(statusPoint, state.data)?.value === "true" ? "" : "true"

    let preData = state.data
    if (selectionMode === pyiGlobal.SELECTION_MODE_SINGLE) {
      preData = preData.map((row) => {
        if (row[1].value === "true") {
          return [...row.slice(0, 1), { ...row[1], value: "" }, ...row.slice(2)]
        }
        return row
      })
    }
    const newData = Matrix.set(statusPoint, { value: newSelected }, preData)

    // Check if all rows are selected
    const allRowsSelected = newData.every((row) => row[1].value === "true")
    const headerSelectedValue = allRowsSelected ? "true" : ""

    return {
      ...state,
      headerLabels: [...state.headerLabels.slice(0, 1), headerSelectedValue, ...state.headerLabels.slice(2, state.headerLabels.length)],
      data: newData,
    }
  })
  // YL, 2022-05-30 - end
  builder.addCase(Actions.select, (state, action) => {
    const { point } = action.payload
    if (state.active && !isActive(state.active, point)) {
      return {
        ...state,
        selected: PointRange.create(point, state.active),
        mode: "view",
      }
    }
  })
  builder.addCase(Actions.selectEntireColumn, (state, action) => {
    const { column, extend } = action.payload
    const showRange = state.showRange

    if (!showRange) {
      return
    }

    const start = showRange.slice(-1)[0]
    const end = showRange[0]

    const point0 = { row: start, column: column }
    const point1 = { row: end, column: column }
    const { active } = state

    let newColumnStatus: number[] = Array(state.columnStatus.length).fill(0)
    if (state.columnStatus[column] === 0) {
      newColumnStatus[column] = 1
    } else {
      newColumnStatus[column] = state.columnStatus[column]
    }

    return {
      ...state,
      columnStatus: newColumnStatus,
      selected: showRange.length !== 0 ? PointRange.create(point0, point1) : null,
      active: showRange.length !== 0 ? (extend && active ? active : { ...Point.ORIGIN, column }) : null,
      mode: "view",
    }
  })
  builder.addCase(Actions.sortByThisColumn, (state, action) => {
    const { column, extend } = action.payload
    const pageRange = state.showRange

    if (!pageRange || column < 2) {
      return
    }

    const start = pageRange[0]
    const end = pageRange.slice(-1)[0]
    const point0 = { row: start, column: column }
    const point1 = { row: end, column: column }
    const { active } = state

    let preData = []
    pageRange.forEach((rowNumber) => {
      preData.push(state.data[rowNumber])
    })

    let preColumnStatus = state.columnStatus
    let newData: Matrix.Matrix<Types.CellBase> = []
    let addData: Matrix.Matrix<Types.CellBase> = []
    let newColumnStatus: number[] = Array(preColumnStatus.length).fill(0)

    preData.forEach((row: any) => {
      if (row[1].value !== "+") {
        newData.push([...row])
      } else {
        addData.push([...row])
      }
    })

    const sortNewData = () => {
      newData.sort(function (a, b) {
        const c = a[column]?.value
        const d = b[column]?.value
        return c.localeCompare(d, "en", { numeric: true })
      })
      if (state.sortNewRows) {
        addData.sort(function (e, f) {
          const g = e[column]?.value
          const h = f[column]?.value
          return g.localeCompare(h, "en", { numeric: true })
        })
      }
    }

    if (preColumnStatus[column] === 1) {
      newColumnStatus[column] = 2
      sortNewData()
    } else if (preColumnStatus[column] === 2) {
      newColumnStatus[column] = 3
      sortNewData()
      newData.reverse()
      if (state.sortNewRows) {
        addData.reverse()
      }
    } else if (preColumnStatus[column] === 3) {
      newColumnStatus[column] = 2
      sortNewData()
    }
    for (var i = 0; i < addData.length; i++) {
      newData.push(addData[i])
    }

    let newHasModify: boolean[] = []
    newData.forEach((newRow) => {
      state.data.forEach((preRow, index) => {
        if (preRow[0].value === newRow[0].value) {
          newHasModify.push(state.hasModify[index])
        }
      })
    })

    let data = []
    let hasModify = []
    let showRowNm = 0
    range(state.data.length).forEach((rowNm) => {
      if (pageRange.indexOf(rowNm) !== -1) {
        data.push(newData[showRowNm])
        hasModify.push(newHasModify[showRowNm])
        showRowNm += 1
      } else {
        data.push(state.data[rowNm])
        hasModify.push(state.hasModify[rowNm])
      }
    })

    return {
      ...state,
      data: data,
      columnStatus: newColumnStatus,
      hasModify: hasModify,
      selected: pageRange.length !== 0 ? PointRange.create(point0, point1) : null,
      active: pageRange.length !== 0 ? (extend && active ? active : { ...Point.ORIGIN, column }) : null,
      mode: "view",
    }
  })
  builder.addCase(Actions.setShowRange, (state, action) => {
    const { showRange } = action.payload
    return {
      ...state,
      showRange: showRange,
    }
  })
  // XH 2022-07-05 end
  builder.addCase(Actions.activate, (state, action) => {
    const { point } = action.payload
    return {
      ...state,
      selected: PointRange.create(point, point),
      active: point,
      mode: "view",
    }
  })
  builder.addCase(Actions.setCellData, (state, action) => {
    if (!state.editable || isActiveReadOnly(state)) {
      return
    }

    const { active, data: cellData, initialData, isMultiSelectBox } = action.payload
    const statusPoint = { row: active.row, column: 1 } // XH 2022-05-09 invisible column
    const status = Matrix.get(statusPoint, state.data)?.value
    let preData = Matrix.set(active, cellData, state.data)

    let changedFlag = false // if it's false, it means the line being modified is the same as the initial data
    const id = Matrix.get({ row: active.row, column: 0 }, state.data)?.value
    initialData &&
      initialData.forEach((row) => {
        if (row[0].value === id) {
          for (var i = 2; i < row.length; i++) {
            if (isMultiSelectBox) {
              if (!areMultiSelectValuesEqual(row[i].value, preData[active.row][i].value)) {
                changedFlag = true
                break
              }
            } else if (row[i].value !== preData[active.row][i].value) {
              changedFlag = true
              break
            }
          }
        }
      })

    // if row status is  "+", modify in this line only change the hasModify to "true"
    return {
      ...state,
      mode: "edit",
      data:
        status === "+" ? preData : changedFlag ? Matrix.set(statusPoint, { value: "~" }, preData) : Matrix.set(statusPoint, { value: "" }, preData),
      lastChanged: active,
      hasModify: [...state.hasModify.slice(0, active.row), changedFlag ? true : false, ...state.hasModify.slice(active.row + 1, preData.length)],
    }
  })
  builder.addCase(Actions.setCellDimensions, (state, action) => {
    const { point, dimensions } = action.payload
    const prevRowDimensions = state.rowDimensions[point.row]

    const prevColumnDimensions = state.columnDimensions[point.column]
    if (
      prevRowDimensions &&
      prevColumnDimensions &&
      prevRowDimensions.top === dimensions.top &&
      prevRowDimensions.height === dimensions.height &&
      prevColumnDimensions.left === dimensions.left &&
      prevColumnDimensions.width === dimensions.width
    ) {
      return
    }
    return {
      ...state,
      rowDimensions: {
        ...state.rowDimensions,
        [point.row]: { top: dimensions.top, height: dimensions.height },
      },
      columnDimensions: {
        ...state.columnDimensions,
        [point.column]: { left: dimensions.left, width: dimensions.width },
      },
    }
  })
  // XH 2022-05-11 start  paste in disableCols
  builder.addCase(Actions.paste, (state, action) => {
    const { data: text , comboPrams } = action.payload
    const { active } = state
    const hasModify: boolean[] = []
    state.hasModify.forEach((i) => {
      hasModify.push(i)
    })

    if (!active || text.trim().length === 0) {
      return
    }

    let copiedMatrix = Matrix.split(text, (value) => ({ value }))
    // data copied from Excel
    const copiedMatrixLength = copiedMatrix.length
    const copiedLastCell = copiedMatrix[copiedMatrixLength - 1][0]
    if (copiedLastCell) {
      if (copiedLastCell.value === "") {
        copiedMatrix = [...copiedMatrix.slice(0, copiedMatrixLength - 1)]
      }
    }

    const copied = PointMap.fromMatrix<any>(copiedMatrix)
    const minPoint = PointSet.min(copied)

    type Accumulator = {
      data: Types.StoreState["data"]
      commit: Types.StoreState["lastCommit"]
    }

    const copiedSize = Matrix.getSize(copiedMatrix)
    const requiredRows = active.row + copiedSize.rows
    let paddedData = Matrix.padRows(state.data, requiredRows)
    let newData: Matrix.Matrix<any> = paddedData

    const dataLength = newData.length - state.data.length
    const nextHasModify = Array(dataLength).fill(false)
    let hasPastedFlag = Array(newData.length).fill(false) // XH 2022-05-25

    let { data, commit } = PointMap.reduce<Accumulator, Types.CellBase>(
      (acc, value, point) => {
        let commit = acc.commit || []
        const nextPoint: Point.Point = {
          row: point.row - minPoint.row + active.row,
          column: point.column - minPoint.column + active.column,
        }

        const nextData = state.cut ? Matrix.unset(point, acc.data) : acc.data
        if (state.cut) {
          commit = [...commit, { prevCell: value, nextCell: null }]
        }
        if (!Matrix.has(nextPoint, newData)) {
          return { data: nextData, commit }
        }

        const currentValue = Matrix.get(nextPoint, nextData) || null

        if (state.disableCols && state.disableCols.indexOf(nextPoint.column) !== -1) {
          commit = [
            ...commit,
            {
              prevCell: currentValue,
              nextCell: currentValue,
            },
          ]
        } else {
          commit = [
            ...commit,
            {
              prevCell: currentValue,
              nextCell: value,
            },
          ]
        }

        if (state.disableCols && state.disableCols.indexOf(nextPoint.column) !== -1) {
          return {
            data: nextData,
            commit,
          }
        } else {
          hasPastedFlag[nextPoint.row] = true // XH 2022-05-25
          return {
            data: Matrix.set(nextPoint, value, nextData),
            commit,
          }
        }
      },
      copied,
      { data: newData, commit: [] }
    )

    // XH 2022-05-25 start   paste in disableCols
    const { rows } = Matrix.getSize(state.data)
    if (state.editable) {
      for (var i = active.row; i < requiredRows; i++) {
        const rowStatus = Matrix.get({ row: i, column: 1 }, data)
        if (rowStatus && rowStatus.value !== "+" && hasPastedFlag[i] === true) {
          data = Matrix.set({ row: i, column: 1 }, { value: "~" }, data)
          hasModify[i] = true
        }
      }
      for (var j = rows; j < requiredRows; j++) {
        data[j][1] = { value: "+" }
      }
    }
    // XH 2022-05-25 end   paste in disableCols

    // If the pasted column contains a comboBox column, try to find the pasted content in the display content of all selectable options of the combobox;
    // if found, use this option as the content of the pasted cell, otherwise set the cell content to empty.
    let initData = []
    data.forEach((rows) => {
      let newRows = []
      if (rows[1].value !== "") {
        rows.forEach((cell, index) => {
          let newCell = cell
          if (comboPrams['columns'].indexOf(index) !== -1 && cell && cell.value) {
            const comboData = comboPrams['comboData'][comboPrams['columns'].indexOf(index)]
            if (comboData && comboData.data) {
              comboData.data.forEach((item) => {
                if (String(item.display) === String(cell.value)) {
                  newCell.value = item.display
                  newCell.comboKey = item.value
                }
              })
              if (newCell.comboKey === undefined) {
                newCell.value = ""
              }
            }
          }
          newRows.push(newCell)
        })
      } else {
        newRows = rows
      }
      initData.push(newRows)
    })

    return {
      ...state,
      data: initData,
      selected: PointRange.create(active, {
        row: active.row + copiedSize.rows - 1,
        column: active.column + copiedSize.columns - 1,
      }),
      cut: false,
      hasPasted: true,
      mode: "view",
      lastCommit: commit,
      hasModify: [...hasModify, ...nextHasModify],
    }
    // XH 2022-05-11 end  paste in disableCols
  })
  builder.addCase(Actions.edit, edit)
  builder.addCase(Actions.view, view)
  builder.addCase(Actions.clear, clear)
  builder.addCase(Actions.blur, blur)
  builder.addCase(Actions.keyPress, (state, action) => {
    const { event } = action.payload
    if (isActiveReadOnly(state) || event.metaKey || !state.editable || !state.active || state.disableCols?.indexOf(state.active.column) !== -1) {
      return
    }

    if (state.mode === "view" && state.active) {
      return {
        ...state,
        data: Matrix.set(state.active, { value: "" }, state.data),
        mode: "edit",
      }
    }
    return
  })
  builder.addCase(Actions.keyDown, (state, action) => {
    const { event } = action.payload
    const handler = getKeyDownHandler(state, event)
    if (handler) {
      return { ...state, ...handler(state, event) }
    }
    return
  })
  builder.addCase(Actions.dragStart, (state, action) => {
    return { ...state, dragging: true }
  })
  builder.addCase(Actions.dragEnd, (state, action) => {
    return { ...state, dragging: false }
  })
  builder.addCase(Actions.commit, (state, action) => {
    const { changes } = action.payload
    return { ...state, ...commit(changes) }
  })
  builder.addMatcher(
    (action) => action.type === Actions.copy.type || action.type === Actions.cut.type,
    (state, action) => {
      const selectedPoints = Selection.getPoints(state.selected, state.data) // XH 2022-04-28
      return {
        ...state,
        copied: selectedPoints.reduce((acc, point) => {
          const cell = Matrix.get(point, state.data)
          return cell === undefined ? acc : PointMap.set(point, cell, acc)
        }, PointMap.from<Types.CellBase>([])),
        cut: action.type === Actions.cut.type,
        hasPasted: false,
      }
    }
  )
})

export default reducer

// Shared reducers
function edit(state: Types.StoreState): Types.StoreState | void {
  if (state.active.row === -1) {
    return { ...state, mode: "edit" }
  }
  if (!state.active || isActiveReadOnly(state) || !state.editable || state.disableCols?.indexOf(state.active.column) !== -1) {
    return
  }
  return { ...state, mode: "edit" }
}

function clear(state: Types.StoreState): Types.StoreState | void {
  if (!state.active || state.active.row === -1) {
    return
  }
  const selectedPoints = Selection.getPoints(state.selected, state.data) // XH 2022-04-28
  const changes = selectedPoints.map((point) => {
    const cell = Matrix.get(point, state.data)
    return {
      ...state,
      prevCell: cell || null,
      nextCell: null,
    }
  })
  return {
    ...state,
    data: selectedPoints.reduce((acc, point) => {
      let acc1 = acc
      const statusPoint = { row: point.row, column: 1 }
      if (Matrix.get(point, acc)?.value !== "") {
        acc1 = Matrix.set(statusPoint, { value: "~" }, acc)
      }
      return Matrix.set(point, { value: "" }, acc1)
    }, state.data),
    ...commit(changes),
  }
}

function blur(state: Types.StoreState): Types.StoreState {
  return { ...state, active: null, selected: null }
}

function view(state: Types.StoreState): Types.StoreState {
  return { ...state, mode: "view" }
}

function commit(changes: Types.CommitChanges): Partial<Types.StoreState> {
  return { lastCommit: changes }
}

// Utility
export const getNextRow = (state: Types.StoreState, preRow: number, rowDelta: number) => {
  let nextRow = preRow + rowDelta
  const maxRow = state.showRange.slice(-1)[0]
  const minRow = state.showRange[0]
  while (state.showRange.indexOf(nextRow) === -1 && nextRow < maxRow && nextRow > minRow) {
    if (rowDelta > 0) {
      nextRow += 1
    } else if (rowDelta < 0) {
      nextRow -= 1
    }
  }
  return nextRow
}

export const getNextColumn = (state: Types.StoreState, preColumn: number, columnDelta: number) => {
  let nextColumn = preColumn + columnDelta
  while (state.inVisibleCols.indexOf(nextColumn) !== -1) {
    if (columnDelta > 0) {
      nextColumn += 1
    } else if (columnDelta < 0) {
      nextColumn -= 1
    }
  }
  return nextColumn
}

export const go =
  (rowDelta: number, columnDelta: number): KeyDownHandler =>
  (state) => {
    if (!state.active) {
      return
    }
    const maxRow = state.showRange.slice(-1)[0]
    const minRow = state.showRange[0]
    const nextActive = {
      row: getNextRow(state, state.active.row, rowDelta),
      column: getNextColumn(state, state.active.column, columnDelta),
    }
    if (!Matrix.has(nextActive, state.data) || nextActive.column === 1 || nextActive.row > maxRow || nextActive.row < minRow) {
      return { ...state, mode: "view" }
    }
    return {
      ...state,
      active: nextActive,
      selected: PointRange.create(nextActive, nextActive),
      mode: "view",
    }
  }
export const go_ =
  (rowDelta: number, columnDelta: number): KeyDownHandler =>
  (state) => {
    if (!state.active) {
      return
    }
    const maxRow = state.showRange.slice(-1)[0]
    const minRow = state.showRange[0]
    const columnRange = range(state.data[0].length).filter(function (val) {
      return state.inVisibleCols.indexOf(val) === -1
    })

    if (state.active.row === -1) {
      if (rowDelta > 0) {
        return
      }
      let nextActive = {
        row: -1,
        column: getNextColumn(state, state.active.column, columnDelta),
      }
      if (nextActive.column < 2) {
        nextActive = {
          row: -1,
          column: state.data[0].length - 1,
        }
      } else if (nextActive.column === columnRange.slice(-1)[0] + 1) {
        nextActive = {
          row: -1,
          column: 2,
        }
      }
      return {
        ...state,
        active: nextActive,
        selected: PointRange.create(nextActive, nextActive),
        mode: "edit",
      }
    }

    let nextActive = {
      row: getNextRow(state, state.active.row, rowDelta),
      column: getNextColumn(state, state.active.column, columnDelta),
    }

    if (nextActive.row === maxRow + 1) {
      if (nextActive.column === columnRange.slice(-1)[0]) {
        nextActive = {
          row: minRow,
          column: 2,
        }
      } else {
        nextActive = {
          row: minRow,
          column: getNextColumn(state, state.active.column, +1),
        }
      }
    }
    if (nextActive.column === columnRange.slice(-1)[0] + 1) {
      if (nextActive.row === maxRow) {
        nextActive = {
          row: minRow,
          column: 2,
        }
      } else {
        nextActive = {
          row: getNextRow(state, state.active.row, +1),
          column: 2,
        }
      }
    }
    if (nextActive.column === 1) {
      if (nextActive.row === minRow) {
        nextActive = {
          row: maxRow,
          column: columnRange.slice(-1)[0],
        }
      } else {
        nextActive = {
          row: getNextRow(state, state.active.row, -1),
          column: columnRange.slice(-1)[0],
        }
      }
    }
    if (!Matrix.has(nextActive, state.data)) {
      return { ...state, mode: "view" }
    }
    return {
      ...state,
      active: nextActive,
      selected: PointRange.create(nextActive, nextActive),
      mode: "view",
    }
  }

// Key Bindings

export type KeyDownHandler = (state: Types.StoreState, event: React.KeyboardEvent) => Types.StoreState | void

type KeyDownHandlers = {
  [K in string]: KeyDownHandler
}

const keyDownHandlers: KeyDownHandlers = {
  ArrowUp: go(-1, 0),
  ArrowDown: go(+1, 0),
  ArrowLeft: go(0, -1),
  ArrowRight: go(0, +1),
  Tab: go_(0, +1),
  Enter: go_(+1, 0),
  F2: edit,
  Delete: clear,
  Escape: blur,
}

const editKeyDownHandlers: KeyDownHandlers = {
  Escape: view,
  Tab: keyDownHandlers.Tab,
  Enter: go_(+1, 0),
}

const editShiftKeyDownHandlers: KeyDownHandlers = {
  Tab: go_(0, -1),
}

const editAltKeyDownHandlers: KeyDownHandlers = {}
const shiftKeyDownHandlers: KeyDownHandlers = {
  ArrowUp: (state) => ({
    ...state,
    selected: Selection.modifyEdge(state, Selection.Direction.Top),
  }),
  ArrowDown: (state) => ({
    ...state,
    selected: Selection.modifyEdge(state, Selection.Direction.Bottom),
  }),
  ArrowLeft: (state) => ({
    ...state,
    selected: Selection.modifyEdge(state, Selection.Direction.Left),
  }),
  ArrowRight: (state) => ({
    ...state,
    selected: Selection.modifyEdge(state, Selection.Direction.Right),
  }),
  Tab: go_(0, -1),
}
// XH 2022-04-28 end

const shiftMetaKeyDownHandlers: KeyDownHandlers = {}
const metaKeyDownHandlers: KeyDownHandlers = {}

export function getKeyDownHandler(state: Types.StoreState, event: React.KeyboardEvent): KeyDownHandler | undefined {
  const { key } = event
  let handlers
  // Order matters
  if (state.mode === "edit") {
    if (event.shiftKey) {
      handlers = editShiftKeyDownHandlers
    } else if (event.altKey) {
      handlers = editAltKeyDownHandlers
    } else {
      handlers = editKeyDownHandlers
    }
  } else if (event.shiftKey && event.metaKey) {
    handlers = shiftMetaKeyDownHandlers
  } else if (event.shiftKey) {
    handlers = shiftKeyDownHandlers
  } else if (event.metaKey) {
    handlers = metaKeyDownHandlers
  } else {
    handlers = keyDownHandlers
  }

  return handlers[key]
}

/** Returns whether the reducer has a handler for the given keydown event */
export function hasKeyDownHandler(state: Types.StoreState, event: React.KeyboardEvent): boolean {
  return getKeyDownHandler(state, event) !== undefined
}

/** Returns whether the active cell is read only */
export function isActiveReadOnly(state: Types.StoreState): boolean {
  const activeCell = getActive(state)
  return Boolean(activeCell?.readOnly)
}

/** Gets active cell from given state */
export function getActive<Cell extends Types.CellBase>(state: Types.StoreState<Cell>): Cell | null {
  const activeCell = state.active && Matrix.get(state.active, state.data)
  return activeCell || null
}

function dateFormat(dateString: string, targetFormat: string) {
  const format = targetFormat.trim().toLocaleLowerCase()
  if (format !== "yyyy-mm-dd hh:mm:ss" && format !== "yyyy-mm-dd" && format !== "hh:mm:ss") {
    return dateString
  }

  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  const seconds = String(date.getSeconds()).padStart(2, "0")

  switch (format) {
    case "yyyy-mm-dd hh:mm:ss":
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    case "yyyy-mm-dd":
      return `${year}-${month}-${day}`
    case "hh:mm:ss":
      return `${hours}:${minutes}:${seconds}`
    default:
      return dateString
  }
}

function areMultiSelectValuesEqual(value1, value2) {
  // Split the strings into arrays, trim whitespace, and filter out any empty strings
  const array1 = value1
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item !== "")
  const array2 = value2
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item !== "")

  // Sort the arrays
  const sortedArray1 = array1.sort()
  const sortedArray2 = array2.sort()

  // Check if the sorted arrays are equal
  return JSON.stringify(sortedArray1) === JSON.stringify(sortedArray2)
}


export function formatNumber(number, format) {
  const decimalPlaces = format.includes('.') ? format.split('.')[1].length : 0;
  // Rounding to the specified number of decimal places
  number = Number(number).toFixed(decimalPlaces);

  let [integerPart, decimalPart] = number.split('.');
  // Handling the formatting of integer parts
  const integerFormat = format.split('.')[0];
  const thousandSeparator = integerFormat.includes(',') ? ',' : '';
  const shouldPadZero = integerFormat.includes('0');

  if (shouldPadZero) {
    // Calculate the number of zeros to be filled
    const neededPadding = integerFormat.replace(/,/g, '').length - integerPart.length;
    if (neededPadding > 0) {
      integerPart = '0'.repeat(neededPadding) + integerPart;
    }
  }
  if (decimalPart && !shouldPadZero) {
    decimalPart = decimalPart.replace(/0+$/, '');
  }

  integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, thousandSeparator);
  return integerPart + (decimalPart ? '.' + decimalPart : '');
}