import * as React from "react"
import { Link, useLocation } from "react-router-dom"
import * as Types from "./types"
import { getComputedValue } from "./util"
import ButtonCell from "./ButtonCell"
import HtmlCell from "./HtmlCell"
import AdvancedSelectionCell from "./AdvancedSelectionCell"
import { CheckCell } from "./CheckCell" // LHH 2022-05-06

export const TRUE_TEXT = "TRUE"
export const FALSE_TEXT = "FALSE"

/** The default Spreadsheet DataViewer component */
const DataViewer = <Cell extends Types.CellBase<Value>, Value>(
  {
    row,
    column,
    newRow,
    cell,
    dialogPrams,
    buttonBoxPrams,
    advancedSelectionBoxPrams,
    initialData,
    htmlCols,
    linkCols,
    checkBoxPrams,
  }: Types.DataViewerProps<Cell> // LHH 2022-04-29
): React.ReactElement => {
  const location = useLocation()

  const value = getComputedValue<Cell, Value>({ cell })
  const dialogCols = dialogPrams.columns
  const dialogIndex = dialogCols.indexOf(column)

  const buttonCols = buttonBoxPrams.columns
  const advancedSelectionCols = advancedSelectionBoxPrams.columns
  const stateNumber = checkBoxPrams[column - 2].stateNumber
  const editable = checkBoxPrams[column - 2].editable

  if (typeof value === "boolean") {
    return <span className="Spreadsheet__data-viewer Spreadsheet__data-viewer--boolean">{convertBooleanToText(value)}</span>
  } else if (buttonCols.indexOf(column) !== -1 && !newRow) {
    const bttIndex = buttonCols.indexOf(column)
    return (
      <ButtonCell
        value={value}
        active={{ row: row, column: column }}
        dialogPrams={dialogPrams}
        buttonBoxPrams={buttonBoxPrams}
        bttIndex={bttIndex}
        dialogIndex={dialogIndex}
        initialData={initialData}
      ></ButtonCell>
    )
  } else if (advancedSelectionCols.indexOf(column) !== -1) {
    const selectIndex = advancedSelectionCols.indexOf(column)
    return (
      <AdvancedSelectionCell
        cell={cell}
        active={{ row: row, column: column }}
        dialogPrams={dialogPrams}
        advancedSelectionBoxPrams={advancedSelectionBoxPrams}
        selectIndex={selectIndex}
        dialogIndex={dialogIndex}
        initialData={initialData}
      ></AdvancedSelectionCell>
    )
  } else if (htmlCols.indexOf(column) !== -1) {
    return (
      <HtmlCell
        value={value}
        active={{ row: row, column: column }}
        dialogPrams={dialogPrams}
        dialogIndex={dialogIndex}
        initialData={initialData}
      ></HtmlCell>
    )
  } else if (linkCols.indexOf(column) !== -1) {
    const currentPath = location.pathname
    const basePath = currentPath.substring(0, currentPath.lastIndexOf("/"))
    const newPath = `${basePath}/${cell["value"]}`
    return <a href={newPath}>{cell["display"]}</a>
  } else if (stateNumber && stateNumber !== 0) {
    return (
      <CheckCell
        stateNumber={stateNumber}
        editable={editable}
        state={String(value)}
        active={{ row: row, column: column }}
        initialData={initialData}
      />
    )
  } else {
    return <span className="Spreadsheet__data-viewer">{String(value)}</span>
  }
}

export default DataViewer

export function convertBooleanToText(value: boolean): string {
  return value ? TRUE_TEXT : FALSE_TEXT
}
