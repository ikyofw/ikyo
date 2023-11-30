// XH 2022-04-28 start
import * as React from "react"
import classNames from "classnames"
import * as Actions from "./actions"
import * as Types from "./types"
import * as Selection from "./selection"
import useDispatch from "./use-dispatch"
import useSelector from "./use-selector"

const RowIndicator: Types.RowIndicatorComponent = ({
  row,
  column,
  tableName,
  label,
  selected,
  onSelect,
}) => {
  const handleClick = React.useCallback(
    (event: React.MouseEvent) => {
      onSelect(row, event.shiftKey)
    },
    [onSelect, row]
  )

  return (
    <th
      id={'cell_' + row + "_" +  (column - 2) + ' ' + tableName}
      className={classNames("Spreadsheet__header", {
        "Spreadsheet__header--selected": selected,
        "Spreadsheet__header__row": column >= 0,
        "Spreadsheet__header__index": column < 0,
      })}
      onClick={handleClick}
      tabIndex={0}
    >
      {label !== undefined ? label : row + 1}
    </th>
  )
}

export default RowIndicator

export const enhance = (
  RowIndicatorComponent: Types.RowIndicatorComponent
): React.FC<Omit<Types.RowIndicatorProps, "selected" | "onSelect">> => {
  return function RowIndicatorWrapper(props) {
    const dispatch = useDispatch()
    const selected = useSelector(
      (state) =>
        Selection.hasEntireRow(state.selected, props.row) ||
        Selection.isEntireTable(state.selected)
    )
    const selectEntireRow = React.useCallback(
      (row: number, extend: boolean) =>
        dispatch(Actions.selectEntireRow(row, extend)),
      [dispatch]
    )
    return (
      <RowIndicatorComponent
        {...props}
        selected={selected}
        onSelect={selectEntireRow}
      />
    )
  }
}
// XH 2022-04-28 end
