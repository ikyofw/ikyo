import * as React from "react"
import classnames from "classnames"
import * as PointMap from "./point-map"
import * as Matrix from "./matrix"
import * as Types from "./types"
import * as Point from "./point"
import * as Actions from "./actions"
import { isActive, getOffsetRect } from "./util"
import useDispatch from "./use-dispatch"
import useSelector from "./use-selector"
import * as Selection from "./selection" // XH 2022-04-28
import transform, {StyleTuple} from 'css-to-react-native';

export const Cell: React.FC<Types.CellComponentProps> = ({
  row,
  column,
  tableName,
  DataViewer,
  selected,
  active,
  tableData,
  dragging,
  newRow,
  mode,
  data,
  stylePrams,
  columnStatus,
  scrollTimes,
  initialData,
  select,
  activate,
  setCellDimensions,
  dialogPrams,
  buttonBoxPrams,
  advancedSelectionBoxPrams,
  htmlCols,
  checkBoxPrams,
  tableHeight,
}): React.ReactElement => {
  const rootRef = React.useRef<HTMLTableCellElement | null>(null)
  const point = React.useMemo(
    (): Point.Point => ({
      row,
      column,
    }),
    [row, column]
  )

  const handleMouseDown = React.useCallback(
    (event: React.MouseEvent<HTMLTableCellElement>) => {
      if (mode === "view") {
        setCellDimensions(point, getOffsetRect(event.currentTarget, tableName, tableHeight))
        if (event.shiftKey) {
          select(point)
        } else {
          activate(point)
        }
      }
    },
    [mode, setCellDimensions, point, tableName, select, activate] // LHH.ikyo 2022-05-05
  )

  const handleMouseOver = React.useCallback(
    (event: React.MouseEvent<HTMLTableCellElement>) => {
      if (dragging) {
        setCellDimensions(point, getOffsetRect(event.currentTarget, tableName, tableHeight))
        select(point)
      }
    },
    [dragging, setCellDimensions, point, tableName, select]
  )

  React.useEffect(() => {
    const root = rootRef.current
    if (selected && root) {
      setCellDimensions(point, getOffsetRect(root, tableName, tableHeight))
    }
    if (root && active && mode === "view") {
      root.focus()
    }
  }, [setCellDimensions, selected, active, mode, point, columnStatus, tableData, tableName, scrollTimes]) // XH, edit input size change

  if (data && data.DataViewer) {
    // @ts-ignore
    DataViewer = data.DataViewer
  }

  let cellStyle: StyleTuple[] = []
  let cellClass = []
  if (stylePrams && stylePrams[column - 2]) {
    const properties = Object.keys(stylePrams[column - 2])
    properties.forEach((property) => {
      if (property.toLocaleLowerCase() === "class") {
        cellClass = stylePrams[column - 2][property].split(",").map((str) => str.trim())
      } else {
        cellStyle.push([property, stylePrams[column - 2][property]])
      }
    })
  }

  return (
    <td
      id={"cell_" + row + "_" + (column - 2) + " " + tableName}
      ref={rootRef}
      className={classnames(cellClass, "Spreadsheet__cell", data?.className, {
        "Spreadsheet__cell--readonly": data?.readOnly,
      })}
      style={cellStyle.length > 0 ? transform(cellStyle) : null}
      onMouseOver={handleMouseOver}
      onMouseDown={handleMouseDown}
      tabIndex={0}
    >
      <DataViewer
        row={row}
        column={column}
        newRow={newRow}
        cell={data}
        dialogPrams={dialogPrams}
        buttonBoxPrams={buttonBoxPrams}
        advancedSelectionBoxPrams={advancedSelectionBoxPrams}
        initialData={initialData}
        htmlCols={htmlCols}
        checkBoxPrams={checkBoxPrams} // LHH.ikyo 2022-04-29
      />
    </td>
  )
}

export const enhance = (
  CellComponent: React.FC<Types.CellComponentProps>
): React.FC<
  Omit<
    Types.CellComponentProps,
    "selected" | "active" | "tableData" | "copied" | "dragging" | "mode" | "data" | "select" | "activate" | "setCellDimensions"
  >
> => {
  return function CellWrapper(props) {
    const { row, column } = props
    const dispatch = useDispatch()
    const select = React.useCallback((point: Point.Point) => dispatch(Actions.select(point)), [dispatch])
    const activate = React.useCallback((point: Point.Point) => dispatch(Actions.activate(point)), [dispatch])
    const setCellDimensions = React.useCallback(
      (point: Point.Point, dimensions: Types.Dimensions) => dispatch(Actions.setCellDimensions(point, dimensions)),
      [dispatch]
    )
    const active = useSelector((state) =>
      isActive(state.active, {
        row,
        column,
      })
    )
    const mode = useSelector((state) => (active ? state.mode : "view"))
    const data = useSelector((state) => Matrix.get({ row, column }, state.data))
    const tableData = useSelector((state) => state.data)
    // XH 2022-04-28 start
    const selected = useSelector((state) => Selection.hasPoint(state.selected, state.data, { row, column }))
    // XH 2022-04-28 end
    const dragging = useSelector((state) => state.dragging)
    const copied = useSelector((state) => PointMap.has({ row, column }, state.copied))

    return (
      <CellComponent
        {...props}
        selected={selected}
        active={active}
        tableData={tableData}
        copied={copied}
        dragging={dragging}
        mode={mode}
        data={data}
        select={select}
        activate={activate}
        setCellDimensions={setCellDimensions}
      />
    )
  }
}
