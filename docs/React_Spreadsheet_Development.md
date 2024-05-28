# Run "react-spreadsheet" Project

2022-03-25 tested.

  1. Prepare react development environment.
  2. Download the last source code from <https://github.com/iddan/react-spreadsheet>.
  3. Unzip download file _react-spreadsheet-master.zip_ to a temp folder. E.g. __D:\Temp\react-spreadsheet-master__.
  4. Create react project: _**npx create-react-app myapp --template typescript**_. E.g. __D:\Projects\myapp__.
  5. Copy the react-spreadsheet sources to the project folder: 
    1. Create a folder named "**react-spreadsheet** " in _myapp/src_ folder. E.g. __D:\Projects\myapp\src\react-spreadsheet__.
    2. Copy react-spreadsheet sources to _myapp/src/react-spreadsheet_ folder. E.g. Copy __D:\Temp\react-spreadsheet-master/src/*__ _to _D:\Projects\myapp\src\react-spreadsheet\_._
    3. Modify _**myapp/package.json**_ : Add all _**dependencies**_ and _**devDependencies**_ from __react-spreadsheet-master\package.json__ to __myapp\package.json__. Remove duplicate item(s).
    4. Modify _**myapp/tsconfig.json**_ : Add __"downlevelIteration": true,__ after __"target": "es5",__.
        
                {
          "compilerOptions": {
            "target": "es5",
            "downlevelIteration": true,
            "lib": [
              "dom",
              ...
            ],
        ...
        ]
        

This is used to resolve the _matrix.entries()_ problem. Please reference to
_react-spreadsheet\matrix.ts_ file in line 115.

        
                export function map<T, T2>(
          func: (value: T | undefined, point: Point.Point) => T2,
          matrix: Matrix<T>
        ): Matrix<T2> {
          const newMatrix: Matrix<T2> = [];
          for (const [row, values] of matrix.entries()) {
            for (const [column, value] of values.entries()) {
              const point = { row, column };
              mutableSet(point, func(value, point), newMatrix);
            }
          }
          return newMatrix;
        }
        

  6. Open myapp using **Visual Studio Code**. E.g. 
    1. _cd_ __D:\Projects\myapp__
    2. _code ._
  7. Open Terminal in VS Code. And install the dependencies: **npm install --force**.
  8. Modify the _myapp/src/react-spreadsheet/index.ts_ file to resolve the compile error. See below:
    
        ...
    //export { Matrix, createEmpty as createEmptyMatrix } from "./matrix";
    export { createEmpty as createEmptyMatrix } from "./matrix";
    export type { Matrix } from "./matrix";
    ...
    

  9. Modity the myapp/src/App.tsx to add the an example. Please reference to <https://iddan.github.io/react-spreadsheet/docs/usage>
    
        import React from 'react';
    import {useState} from 'react'
    import logo from './logo.svg';
    import './App.css';
    import Spreadsheet from './react-spreadsheet';
    
    const App = () => {
      const [data, setData] = useState([
        [{ value: "Vanilla" }, { value: "Chocolate" }],
        [{ value: "Strawberry" }, { value: "Cookies" }],
      ]);
      return <Spreadsheet data={data} onChange={()=>setData} />;
    };
    
    export default App;
    

  10. Get updated values (_onChange_ event):

    
    
    ...
    const App = () => {
      const [data, setData] = useState([
        [{ value: "Vanilla" }, { value: "Chocolate" }],
        [{ value: "Strawberry" }, { value: "Cookies" }],
      ]);
      return <Spreadsheet data={data} onChange={(data)=>{
        console.log(JSON.stringify(data))
      }} />;
    };
    ...
    

  1. Run the react server: **npm start**
  2. [![](/images/thumb/8/8b/React-spreadsheet-example.png/300px-React-spreadsheet-example.png)](File.md:React-spreadsheet-example.png)

[](File.md:React-spreadsheet-example.png "Enlarge")

React spreadsheet demo

Check the output via browser: <http://localhost:3000>

  3. 

# Use "react-spreadsheet" in myapp

  * .Preparation stage： 
    * Download the source code of "react-spreadsheet" from this page：<https://github.com/iddan/react-spreadsheet>
    * Create reactjs project：npx create-react-app myapp
  * Delete the unneeded files (optional): 
    * Delete all the files in ./myapp/src except index.js
    * Delete all the test files in ./react-spreadsheet-master/src that with the "test" field.
  * Import the source code of "react-spreadsheet" into myapp: 
    * Copy all files from ./react-spreadsheet-master/src to ./myapp/src
    * Copy all files from ./react-spreadsheet-master/node_modules to ./myapp/node_modules
  * Verify success: 
    * Try the simple example in this page:[https://iddan.github.io/react-spreadsheet/](https://iddan.github.io/react-spreadsheet/docs/usage)

  

# Remove all the formula stuff

  * Remove the "class Parser" in "/myreact2/src/typings/hot-formula-parser.d.ts"
  * Remove statements that use "class Parser": 
    * ./myapp/src/types.ts:line 2,line62,line 67-line 70,line 86,line118-line121

    
    
     import { Parser as FormulaParser } from "hot-formula-parser";
    
    
    
     bindings: PointMap<PointSet>;
    
    
    
     
    export type GetBindingsForCell<Cell extends CellBase = CellBase> = (
      cell: Cell,
      data: Matrix<Cell>
    ) => Point[];
    
    
    
      formulaParser: FormulaParser;
    
    
    
     
    & {
    /** Instance of `FormulaParser` */
    formulaParser: FormulaParser;}
    

  *     * ./myapp/src/Cell.tsx:line 18,line 91, line 148-line 156

    
    
    formulaParser,
    
    
    
    formulaParser={formulaParser}
    
    
    
    useSelector((state) => {
      const point = { row, column };
      const cellBindings = PointMap.get(point, state.bindings);
      return cellBindings &&
        state.lastChanged &&
        PointSet.has(cellBindings, state.lastChanged)
        ? {}
        : null;
    });
    

  *     * ./myapp/src/Spreadsheet.tsx:line 9,line 28, line 30-line 32,line 52,line 105,line 142,line 176,line 355-line 357,line 376-line 402,line 445,line 467,line 198

    
    
    import { Parser as FormulaParser } from "hot-formula-parser";
    
    
    
    import { getBindingsForCell as defaultGetBindingsForCell } from "./bindings";
    
    
    
    transformCoordToPoint,
    getCellRangeValue,
    getCellValue,
    
    
    
    formulaParser?: FormulaParser;
    
    
    
    getBindingsForCell?: Types.GetBindingsForCell<CellType>;
    
    
    
    getBindingsForCell = defaultGetBindingsForCell,
    
    
    
    bindings: PointMap.from([]),
    
    
    
      
    const formulaParser = React.useMemo(() => {
    return props.formulaParser || new FormulaParser();
    }, [props.formulaParser]);
    
    
    
    React.useEffect(() => {
        formulaParser.on("callCellValue", (cellCoord, done) => {
          let value;
          try {
            const point = transformCoordToPoint(cellCoord);
            const data = state.data;
            value = getCellValue(formulaParser, data, point);
          } catch (error) {
            console.error(error);
          } finally {
            done(value);
          }
        });
        formulaParser.on("callRangeValue", (startCellCoord, endCellCoord, done) => {
          const startPoint = transformCoordToPoint(startCellCoord);
          const endPoint = transformCoordToPoint(endCellCoord);
          const data = state.data;
          let values;
          try {
            values = getCellRangeValue(formulaParser, data, startPoint, endPoint);
          } catch (error) {
            console.error(error);
          } finally {
            done(values);
          }
        });
      }, [formulaParser, state, handleCut, handleCopy, handlePaste]);
    
    
    
    formulaParser={formulaParser}
    
    
    
    formulaParser,
    
    
    
    getBindingsForCell={getBindingsForCell}
    

  *     * ./myapp/src/util.ts:line 145-line 155,line 256-line 265,line 271-line 283

    
    
    export function getFormulaComputedValue({
      cell,
      formulaParser,
    }: {
      cell: Types.CellBase<string>;
      formulaParser: hotFormulaParser.Parser;
    }): FormulaParseResult | FormulaParseError | null {
      const formula = Formula.extractFormula(cell.value);
      const { result, error } = formulaParser.parse(formula);
      return error || result;
    }
    
    
    
    export function getCellValue<CellType extends Types.CellBase>(
      formulaParser: hotFormulaParser.Parser,
      data: Matrix.Matrix<CellType>,
      point: Point.Point
    ): FormulaParseResult | CellType["value"] | null {
      return getComputedValue({
        cell: Matrix.get(point, data),
        formulaParser,
      });
    }
    
    
    
    export function getCellRangeValue<CellType extends Types.CellBase>(
      formulaParser: hotFormulaParser.Parser,
      data: Matrix.Matrix<CellType>,
      start: Point.Point,
      end: Point.Point
    ): Array<FormulaParseResult | CellType["value"] | null> {
      return Matrix.toArray(Matrix.slice(start, end, data), (cell) =>
        getComputedValue({
          cell,
          formulaParser,
        })
      );
    }
    

  *     * ./myapp/src/ActiveCell.ts:line 13

    
    
    getBindingsForCell: Types.GetBindingsForCell<Types.CellBase>;
    

  *     * ./myapp/src/bingdings.ts:delete whole file.

  *     * ./myapp/src/index.ts:line 16

    
    
    getBindingsForCell
    

  *     * ./myapp/src/reducer.ts:line 24,line 34-line 38,line 44

    
    
    bindings: PointMap.from([]),
    
    
    
    const nextBindings = PointMap.map(
      (bindings) =>
        PointSet.filter((point) => Matrix.has(point, data), bindings),
      PointMap.filter((_, point) => Matrix.has(point, data), state.bindings)
    );
    
    
    
    bindings: nextBindings,
    

  * Modify statements that use "class Parser": 
    * ./myapp/src/util.ts:line 128-line 142

    
    
    export function getComputedValue<Cell extends Types.CellBase<Value>, Value>({
      cell,
      //formulaParser,
    }: {
      cell: Cell | undefined;
      // formulaParser: hotFormulaParser.Parser;
    }): Value | FormulaParseResult | FormulaParseError | null {
      if (cell === undefined) {
        return null;
      }
      // if (isFormulaCell(cell)) {
      //   return getFormulaComputedValue({ cell, formulaParser });
      // }
      return cell.value;
    }
    

  *     * ./myapp/src/DataViewer.tsx:line 9-line 21

    
    
    const DataViewer = <Cell extends Types.CellBase<Value>, Value>({
      cell,
      //formulaParser,
    }: Types.DataViewerProps<Cell>): React.ReactElement => {
      const value = getComputedValue<Cell, Value>({ cell });
      return typeof value === "boolean" ? (
        <span className="Spreadsheet__data-viewer Spreadsheet__data-viewer--boolean">
          {convertBooleanToText(value)}
        </span>
      ) : (
        <span className="Spreadsheet__data-viewer">{value}</span>
      );
    };
    

# The key strokes are managed in the programs

The function “go” is the cornerstone,any keyboard input is converted to
go(x,y) Keyboard input is classified according to its different states

    
    
    if (state.mode === "edit") {
        if (event.shiftKey) {
          handlers = editShiftKeyDownHandlers;
        } else {
          handlers = editKeyDownHandlers;
        }
      } else if (event.shiftKey && event.metaKey) {
        handlers = shiftMetaKeyDownHandlers;
      } else if (event.shiftKey) {
        handlers = shiftKeyDownHandlers;
      } else if (event.metaKey) {
        handlers = metaKeyDownHandlers;
      } else {
        handlers = keyDownHandlers;
      }
    

Such as

    
    
    else {
          handlers = editKeyDownHandlers;
        }
    
    
    
    const editKeyDownHandlers: KeyDownHandlers = {
      Escape: view,
      Tab: keyDownHandlers.Tab,
      F2: keyDownHandlers.Arrowup,
    };
    

Means when mode is “edit” and have not press “shift”,”ESC” brings the mode
back to “view”，etc.

    
    
    else {
        handlers = keyDownHandlers;
      }
    
    
    
    const keyDownHandlers: KeyDownHandlers = {
      ArrowUp: go(-1, 0),
      ArrowDown: go(+1, 0),
      ArrowLeft: go(0, -1),
      ArrowRight: go(0, +1),
      Tab: go(0, +1),
      F2: edit,
      Backspace: clear,
      Escape: blur,
    };
    

Means when mode is “view” and have not press “shift” and ”windows”,Arrow keys
makes the selection box move in all four directions,”F2” brings the mode to
“edit”，etc.

