# Set some columns to read only

## First, the column number that needs to be made read-only should be passed
to the component

Add a new props

    
    
    spreadsheet.tsx:
    export type Props<CellType extends Types.CellBase> = {
      xxx
      readOnlyColumns?:number[];  
      xxx  // other props
    ｝
    

Use this props:

    
    
    App.tsx:
    <Spreadsheet
       readOnlyColumns={[1,3]} 
       xxx // other props
    />
    

## Then save it to state

Set types:

    
    
    types.ts:
    export type StoreState<Cell extends CellBase = CellBase> = {
      readOnlyColumns: number[];
      xxx // other state
    }
    

Initial

    
    
    reducer.tsx:
    export const INITIAL_STATE: Types.StoreState = {
      readOnlyColumns: [],
      xxx // other initial state
    }
    

Save props in state:

    
    
    spreadsheet.tsx:
    const initialState = React.useMemo(() => {
      return {
        ...INITIAL_STATE,
        readOnlyColumns: props.readOnlyColumns,
        xxx // other props that save in state
      } as Types.StoreState<CellType>;
    }, [..., props.readOnlyColumns]);
    

## Use this state to make some columns read only

Change function edit：

    
    
    reducer.tsx:
    function edit(state: Types.StoreState): Types.StoreState | void {
      if (!state.active) {
        return;
      }
      if (
        isActiveReadOnly(state) ||
        !state.editable ||
        state.readOnlyColumns.indexOf(state.active.column) !== -1  // change in this line
      ) {
        return;
      }
      return { ...state, mode: "edit" };
    }
    

Add a new condition to the handleKeyPress event:

    
    
    spreadsheet.tsx:
    const handleKeyPress = React.useCallback(
      (event: React.KeyboardEvent) => {
        if (
          state.active &&
          state.readOnlyColumns.indexOf(state.active.column) === -1
        ) {
          onKeyPress(event);
          xxx // other code
        }
      },
      [..., state.readOnlyColumns])
    

# Set some columns to invisible

## First, the column number that needs to be made invisible should be
transferred to the component

Add a new props

    
    
    spreadsheet.tsx:
    export type Props<CellType extends Types.CellBase> = {
      xxx
      visibleColumns?: number[];  
      xxx  // other props
    ｝
    

Use this props:

    
    
    App.tsx:
    <Spreadsheet
       visibleColumns?={[0,1]} 
       xxx // other props
    />
    

## Then save it to state

Set types:

    
    
    types.ts:
    export type StoreState<Cell extends CellBase = CellBase> = {
      visibleColumns: number[];
      xxx // other state
    }
    

Initial

    
    
    reducer.tsx:
    export const INITIAL_STATE: Types.StoreState = {
      visibleColumns: [],
      xxx // other initial state
    }
    

Save props in state:

    
    
    spreadsheet.tsx:
    const initialState = React.useMemo(() => {
      return {
        ...INITIAL_STATE,
        visibleColumns: props.visibleColumns,
        xxx // other props that save in state
      } as Types.StoreState<CellType>;
    }, [..., props.visibleColumns]);
    

## Use this state to make some columns invisible

When rendering column headers and data, if columnNumber in the list of
invisible, render null.

    
    
    spreadsheet.tsx:
    props.inVisibleColumns &&
    props.inVisibleColumns.indexOf(columnNumber - 2) !==
      -1 ? null : (
      <ColumnIndicator
        key={columnNumber}
        column={columnNumber}
        label={
          columnNumber in state.columnLabels
             ? state.columnLabels[columnNumber]
             : null
          }
       />
    )
    
    
    
    props.inVisibleColumns &&
    props.inVisibleColumns.indexOf(columnNumber - 2) !==
      -1 ? null : (
      <Cell
        key={columnNumber}
        row={rowNumber}
        column={columnNumber}
        // @ts-ignore
        DataViewer={DataViewer}
      />
    )
    

Add a loop for the movement of the select rectangle so that the select
rectangle can skip columns that are invisible.

    
    
    reducer.tsx  select rectangle moved by arrows:
    let nextColumn = state.active.column + columnDelta;
    while (state.inVisibleColumns.indexOf(nextColumn - 2) !== -1){
      if (columnDelta > 0){
        nextColumn = nextColumn + 1
      } else {
        nextColumn = nextColumn - 1
      }
    }
    const nextActive = {
      row: state.active.row + rowDelta,
      column: nextColumn
    };
    
    
    
    reducer.tsx  select rectangle moved by tab, shift+tab and enter:
    let nextRow = nextActive.row;
    let nextColumn = nextActive.column;
    while (state.inVisibleColumns.indexOf(nextColumn - 2) !== -1) {
      if (columnDelta > 0) {
        nextRow =
          nextColumn + 1 === columnNumber
            ? nextRow + 1 === rowNumber
              ? 0
              : nextRow + 1
            : nextRow;
        nextColumn = nextColumn + 1 === columnNumber ? 2 : nextColumn + 1;
      } else if (columnDelta < 0) {
        nextRow =
          nextColumn - 1 === 1
            ? nextRow - 1 === -1
              ? rowNumber - 1
              : nextRow - 1
            : nextRow;
        nextColumn = nextColumn - 1 === 1 ? columnNumber - 1 : nextColumn - 1;
      } else if (rowDelta > 0) {
        nextColumn = nextColumn + 1 === columnNumber ? 2 : nextColumn + 1;
      }
    }
    nextActive.row = nextRow;
    nextActive.column = nextColumn;
    

# Click column header to select whole column

## Download the latest version of the spreadsheet component from Git and
update it to our project

Copy a file named "selection.ts" from the new version into "./src/react-
spreadsheet/";

updata our "ColumnIndicator.tsx", "CornerIndicator.tsx", "RowIndicator.tsx"
and "Selected.tsx" from new version;

## Update the configuration

types.ts: line 7,line 50,line 178-line 217

    
    
    import { Matrix } from "./matrix";
    
    
    
    selected: Selection
    
    
    
    export type RowIndicatorProps = {
      /** The row the indicator indicates */
      row: number;
      /** A custom label for the indicator as provided in rowLabels */
      label?: React.ReactNode | null;
      /** Whether the entire row is selected */
      selected: boolean;
      /** Callback to be called when the row is selected */
      onSelect: (row: number, extend: boolean) => void;
    };
    
    /** Type of the RowIndicator component */
    export type RowIndicatorComponent = React.ComponentType<RowIndicatorProps>;
    
    /** Type of the Spreadsheet ColumnIndicator component props */
    export type ColumnIndicatorProps = {
      /** The column the indicator indicates */
      column: number;
      /** A custom label for the indicator as provided in columnLabels */
      label?: React.ReactNode | null;
      /** Whether the entire column in selected */
      selected: boolean;
      /** Callback to be called when the column is selected */
      onSelect: (column: number, extend: boolean) => void;
    };
    
    /** Type of the ColumnIndicator component */
    export type ColumnIndicatorComponent =
      React.ComponentType<ColumnIndicatorProps>;
    
    /** Type of the Spreadsheet CornerIndicator component props */
    export type CornerIndicatorProps = {
      /** Whether the entire table is selected */
      selected: boolean;
      /** Callback to select the entire table */
      onSelect: () => void;
    };
    
    /** Type of the CornerIndicator component */
    export type CornerIndicatorComponent =
      React.ComponentType<CornerIndicatorProps>;
    

util.ts: line 9,line 129-line 139

    
    
    import * as Selection from "./selection";
    
    
    
    export function getSelectedDimensions(
      rowDimensions: Types.StoreState["rowDimensions"],
      columnDimensions: Types.StoreState["columnDimensions"],
      data: Matrix.Matrix<unknown>,
      selected: Selection.Selection
    ): Types.Dimensions | undefined {
      const range = Selection.toRange(selected, data);
      return range
        ? getRangeDimensions(rowDimensions, columnDimensions, range)
        : undefined;
    }
    

Cell.tsx: line 10, line 139-line 141

    
    
    import * as Selection from "./selection";
    
    
    
    const selected = useSelector((state) =>
      Selection.hasPoint(state.selected, state.data, { row, column }) 
    );
    

spreadsheet.tsx: line 306-line 309

    
    
    if (state.selected !== prevState.selected) {
        const points = Selection.getPoints(state.selected, state.data);
        onSelect(points);
      }
    

## Create new function

reducer.tsx: line7,line 48, line 396, if the line number has changed, search
for "nextSelected" and "selectedPoints" to find and update them.

    
    
    import * as Selection from "./selection";
    
    
    
    const nextSelected = Selection.normalize(state.selected, data);
    
    
    
    const selectedPoints = Selection.getPoints(state.selected, state.data);
    
    
    
    const selectedPoints = Selection.getPoints(state.selected, state.data);
    

Create a new function about selectEntireColumn in reducer.tsx:

    
    
    builder.addCase(Actions.selectEntireColumn, (state, action) => {
      const { column, extend } = action.payload;
      const { active } = state;
      return {
        ...state,
        selected:
          extend && active
            ? Selection.createEntireColumns(active.column, column)
            : Selection.createEntireColumns(column, column),
        active: extend && active ? active : { ...Point.ORIGIN, column },
        mode: "view",
        };
    });
    

Remove function "modifyEdge" in recucer.tsx

change "shiftKeyDownHandlers":

    
    
    const shiftKeyDownHandlers: KeyDownHandlers = {
      ArrowUp: (state) => ({
        ...state,
        selected: Selection.modifyEdge(
          state.selected,
          state.active,
          state.data,
          Selection.Direction.Top
        ),
      }),
      ArrowDown: (state) => ({
        ...state,
        selected: Selection.modifyEdge(
          state.selected,
          state.active,
          state.data,
          Selection.Direction.Bottom
        ),
      }),
      ArrowLeft: (state) => ({
        ...state,
        selected: Selection.modifyEdge(
          state.selected,
          state.active,
          state.data,
          Selection.Direction.Left
        ),
      }),
      ArrowRight: (state) => ({
        ...state,
        selected: Selection.modifyEdge(
          state.selected,
          state.active,
          state.data,
          Selection.Direction.Right
        ),
      }),
      Tab: go_(0, -1),
    };
    

Update function in spreadsheet.tsx: line 15-line 25,line 347- line 355,line
477-line 492

    
    
    import * as Selection from "./selection"; 
    import DefaultCornerIndicator, {
      enhance as enhanceCornerIndicator,
    } from "./CornerIndicator";
    import DefaultColumnIndicator, {
      enhance as enhanceColumnIndicator,
    } from "./ColumnIndicator";
    import DefaultRowIndicator, {
      enhance as enhanceRowIndicator,
    } from "./RowIndicator";
    import { Cell as DefaultCell, enhance as enhanceCell } from "./Cell";
    
    
    
    const clip = React.useCallback(
      (event: ClipboardEvent): void => {
        const { data, selected } = state;
        const selectedData = Selection.getSelectionFromMatrix(selected, data); // XH 2022-04-28
        const csv = getCSV(selectedData);
        writeTextToClipboard(event, csv);
      },
      [state]
    );
    
    
    
    const CornerIndicator = React.useMemo(
      () =>
        enhanceCornerIndicator(props.CornerIndicator || DefaultCornerIndicator),
      [props.CornerIndicator]
    );
    
    const RowIndicator = React.useMemo(
      () => enhanceRowIndicator(props.RowIndicator || DefaultRowIndicator),
      [props.RowIndicator]
    );
    
    const ColumnIndicator = React.useMemo(
      () =>
        enhanceColumnIndicator(props.ColumnIndicator || DefaultColumnIndicator),
      [props.ColumnIndicator]
    );
    

