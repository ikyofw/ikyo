import TableFg from "../TableFg";
import DataEditor from "./DataEditor";
import DataViewer from "./DataViewer";

export default TableFg;
export { TableFg as Spreadsheet, DataEditor, DataViewer };
export type { Props } from "../TableFg";
export { getComputedValue } from "./util";
export { createEmpty as createEmptyMatrix } from "./matrix";
export type { Matrix } from "./matrix";
export type { Point } from "./point";
export type {
  CellBase,
  CellDescriptor,
  Mode,
  Dimensions,
  CellChange,
  CellComponentProps,
  CellComponent,
  DataViewerProps,
  DataViewerComponent,
  DataEditorProps,
  DataEditorComponent,
} from "./types";
