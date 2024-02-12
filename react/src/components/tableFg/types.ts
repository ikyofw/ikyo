import * as React from "react"
import { Matrix } from "./matrix"
import { Point } from "./point"
import { PointMap } from "./point-map"
import { Selection } from "./selection" // XH 2022-04-28

/** The base type of cell data in Spreadsheet */
export type CellBase<Value = any> = {
  /** Whether the cell should not be editable */
  readOnly?: boolean
  /** Class to be given for the cell element */
  className?: string
  /** The value of the cell */
  value: Value
  /** The selection key of the combo */
  comboKey?: string
  /** Custom component to render when the cell is edited, if not defined would default to the component defined for the Spreadsheet */
  DataEditor?: DataEditorComponent<CellBase<Value>>
  /** Custom component to render when the cell is viewed, if not defined would default to the component defined for the Spreadsheet */
  DataViewer?: DataViewerComponent<CellBase<Value>>
}

/**
 * A cell with it's coordinates
 * @deprecated the component does not use cell descriptors anymore. Instead it passes cell point and cell value explicitly.
 */
export type CellDescriptor<Cell> = {
  /** The cell's data */
  data: Cell | undefined
} & Point

/** The spreadsheet's write mode */
export type Mode = "view" | "edit"
//export type RowStatus = "" | "~" | "-" | "+";

/** Dimensions of an element */
export type Dimensions = {
  /** The element's width in pixels */
  width: number
  /** The element's height in pixels */
  height: number
  /** The distance of the element from it's container top border in pixels */
  top: number
  /** The distance of the element from it's container left border in pixels */
  left: number
}

export type StoreState<Cell extends CellBase = CellBase> = {
  data: Matrix<Cell>
  selected: Selection // XH 2022-04-28
  copied: PointMap<Cell>
  hasPasted: boolean
  cut: boolean
  active: Point | null
  mode: Mode
  rowDimensions: Record<number, Pick<Dimensions, "height" | "top"> | undefined>
  columnDimensions: Record<number, Pick<Dimensions, "width" | "left"> | undefined>
  dragging: boolean
  lastChanged: Point | null
  lastCommit: null | CellChange<Cell>[]
  hasModify: Array<boolean>
  editable: boolean
  disableCols: number[] // XH 2022-04-28
  inVisibleCols: number[] // XH 2022-05-09 invisible
  headerLabels: string[]
  headerLabelTips: string[] // YL, 2023-05-06 Add tooltip
  columnStatus: number[] // XH 2022-07-04 column sort
  sortNewRows: boolean
  showRange: number[]
  refreshFlag: boolean
}

export type CellChange<Cell extends CellBase = CellBase> = {
  prevCell: Cell | null
  nextCell: Cell | null
}

/** Type of Spreadsheet Cell component props */
export type CellComponentProps<Cell extends CellBase = CellBase> = {
  /** The row of the cell */
  row: number
  /** The column of the cell */
  column: number
  /** The name of table */
  tableName: string
  /** The DataViewer component to be used by the cell */
  DataViewer: DataViewerComponent<Cell>
  /** Whether the cell is selected */
  selected: boolean
  /** Whether the cell is active */
  active: boolean
  /** Whether the cell is copied */
  copied: boolean
  /** Whether the user is dragging */
  dragging: boolean
  /** Whether the cell is new row */
  newRow?: boolean
  /** The mode of the cell */
  mode: Mode
  /** Which cell is active */
  tableData: any
  /** The data of the cell */
  data: Cell | undefined
  /** The column status of the cell */
  stylePrams: any[]
  /** Save the initial css settings of the cell  */
  columnStatus?: number
  /** Saves the number of scrolls when mode is scrolling  */
  scrollTimes?: number
  /** Save the initial data of the table  */
  initialData?: any[]
  /** Select the cell at the given point */
  select: (point: Point) => void
  /** Activate the cell at the given point */
  activate: (point: Point) => void
  /** Set the dimensions of the cell at the given point with the given dimensions */
  setCellDimensions: (point: Point, dimensions: Dimensions) => void
  /** Define the parameters of the dialog */
  dialogPrams?: {
    columns: number[]
    dialog: { [key: string]: any }[]
    eventHandler: { [key: string]: any }[]
  }
  /** Define the parameters of the button */
  buttonBoxPrams?: {
    columns: number[]
    btnIcon: number[]
    type: string[]
  }
  /** Define the parameters of the advancedSelection */
  advancedSelectionBoxPrams?: {
    columns: number[]
    btnIcon: number[]
    comboData: { [key: string]: any }[]
  }
  /** The column number of the html */
  htmlCols?: number[]
  checkBoxPrams?: any[]
  tableHeight?: number
}

/** Type of the Spreadsheet Cell component */
export type CellComponent<Cell extends CellBase = CellBase> = React.ComponentType<CellComponentProps<Cell>>

type DataComponentProps<Cell extends CellBase> = {
  /** Whether the cell is new row */
  newRow?: boolean
  /** The rendered cell by the component */
  cell: Cell | undefined
  /** Define the parameters of the dialog */
  dialogPrams?: {
    columns: number[]
    dialog: { [key: string]: any }[]
    eventHandler: { [key: string]: any }[]
  }
  /** Define the parameters of the button */
  buttonBoxPrams?: {
    columns: number[]
    btnIcon: number[]
    type: string[]
  }
  /** Define the parameters of the advancedSelection */
  advancedSelectionBoxPrams?: {
    columns: number[]
    btnIcon: number[]
    comboData: { [key: string]: any }[]
  }
  /** Save the initial data of the table  */
  initialData?: any[]
  htmlCols?: number[]
  checkBoxPrams?: any[]
} & Point

/** Type of the Spreadsheet DataViewer component props */
export type DataViewerProps<Cell extends CellBase = CellBase> = DataComponentProps<Cell> & {}

/** Type of the Spreadsheet DataViewer component */
export type DataViewerComponent<Cell extends CellBase = CellBase> = React.ComponentType<DataViewerProps<Cell>>

/** Type of the Spreadsheet DataEditor component props */
export type DataEditorProps<Cell extends CellBase = CellBase> = DataComponentProps<Cell> & {
  /** Callback to be called when the cell's value is changed */
  onChange: (cell: Cell) => void
  /** Callback to be called when edit mode should be exited */
  exitEditMode: () => void
  // for comboBox cell
  /** The corresponding selections for each combo column */
  comboPrams?: {
    columns: number[]
    comboData: { [key: string]: any }[]
  }
  /** Define which column is a calendar */
  dateBoxCols?: Array<{ colIndex: number; formatFlag?: 1 | 2 | 3 }> // LHH 2022-05-09
  /** Define which column use textarea input value*/
  textareaCols?: number[]
  /** Define the style of textarea */
  style?: any
}

/** Type of the Spreadsheet DataEditor component */
export type DataEditorComponent<Cell extends CellBase = CellBase> = React.ComponentType<DataEditorProps<Cell>>

/** Type of the Spreadsheet Table component props */
export type TableProps = React.PropsWithChildren<{
  /** Number of columns the table should render */
  columns: number
  /** Whether column indicators are hidden */
  hideColumnIndicators?: boolean | null
  /** Name of the table */
  tableName: string
  /** Pramaters of scrolling */
  scrollPrams?: { [key: string]: any };
}>

/** Type of the Spreadsheet Table component */
export type TableComponent = React.ComponentType<TableProps>

/** Type of the Spreadsheet Row component props */
export type RowProps = React.PropsWithChildren<{
  /** The row index of the table */
  row: number
  /** The name of table */
  tableName?: string
}>

/** Type of the Row component */
export type RowComponent = React.ComponentType<RowProps>

/** Type of the Spreadsheet OtherRow component props */
export type OtherRowProps = React.PropsWithChildren<{ id: string }>

/** Type of the HeaderRow component */
export type HeaderRowComponent = React.ComponentType<OtherRowProps>

/** Type of the FooterRow component */
export type FooterRowComponent = React.ComponentType<OtherRowProps>

/** Type of the Spreadsheet RowIndicator component props */
export type RowIndicatorProps = {
  /** The row the indicator indicates */
  row: number
  /** The column the indicator indicates */
  column: number
  /** The name of table */
  tableName: string
  /** A custom label for the indicator as provided in rowLabels */
  label?: React.ReactNode | null
  /** Whether the entire row is selected */
  selected: boolean
  /** Callback to be called when the row is selected */
  onSelect: (row: number, extend: boolean) => void
}

/** Type of the RowIndicator component */
export type RowIndicatorComponent = React.ComponentType<RowIndicatorProps>

// XH 2022-07-04 start
/** Type of the Spreadsheet ColumnIndicator component props */
export type ColumnIndicatorProps<Cell extends CellBase = CellBase> = {
  /** Table name */
  tableName?: string
  /** The row the indicator indicates */
  row: number
  /** The column the indicator indicates */
  column: number
  /** The column style prams */
  stylePrams?: any
  /** A custom label for the indicator as provided in columnLabels */
  label?: React.ReactNode | null
  /** The column status of this column */
  columnStatus?: number
  /** The tips of this column */
  tip?: string // YL, 2023-05-06 Add tooltip
  data?: Matrix<Cell>
  addRow?: Function
  /** Whether the entire column in selected */
  selected: boolean
  /** Callback to be called when the column is selected */
  onSelect: (column: number, extend: boolean) => void
  onSorted: (column: number, extend: boolean) => void
}
// XH 2022-07-04 end

/** Type of the ColumnIndicator component */
export type ColumnIndicatorComponent = React.ComponentType<ColumnIndicatorProps>

/** Type of the Spreadsheet CornerIndicator component props */
export type CornerIndicatorProps = {
  /** Whether the entire table is selected */
  selected: boolean
  /** Callback to select the entire table */
  onSelect: () => void
}

/** Type of the CornerIndicator component */
export type CornerIndicatorComponent = React.ComponentType<CornerIndicatorProps>

export type CommitChanges<Cell extends CellBase = CellBase> = Array<{
  prevCell: Cell | null
  nextCell: Cell | null
}>
export function StoreState(StoreState: any) {
  throw new Error("Function not implemented.")
}
