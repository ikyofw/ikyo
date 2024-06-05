## Function

A new interface has been added that allows the user to create a function on
the backend to manipulate dom.

Here is a example:

    
    
    def getScreen(self, request):
        screen = getScreenDfnJson(request, getScreenName(self), 'beforeDisplayAdapterTest')
    
        func = "function xxx(tableDat, rowData, rowIndex, columnIndex, cell){\n"
        func += "if ((rowIndex === 2 && columnIndex === 3) || (rowIndex === 8 && columnIndex === 0)) {cell.innerHTML = ''}\n"
        func += "const value = cell.querySelector('span') ? cell.querySelector('span').innerHTML : ''\n"
        func += "if (value.indexOf('t2') !== -1) {cell.style.background = '#A0C32D'}"
        func += "};"
        screen['outputFg']['beforeDisplayAdapter'] = func
        
        return PyiSccJsonResponse(data=screen)
    

Just pass a js syntax function as a string to the beforeDisplayAdapter
property of the corresponding table to manipulate the dom of the table.

The five parameters in order are the data of the entire table, the data of the
current row, the row index, and column index of the cell, and the dom of the
cell.

Use the first four parameters to determine whether the current cell needs to
be modified and how to modify it.

## Implementation method

Get to the string form of the back-end written function, Create a string as a
function using new Function(prams1, prams2, ..., func).

Then just pass the parameters into this function in order to trigger the
function:

    
    
    React.useEffect(() => {
      if (!beforeDisplayAdapter) {
        return
      }
      try {
        const pramsIndexLeft = beforeDisplayAdapter.indexOf("(")
        const pramsIndexRight = beforeDisplayAdapter.indexOf(")")
        const funcIndexLeft = beforeDisplayAdapter.indexOf("{")
        const funcIndexRight = beforeDisplayAdapter.lastIndexOf("}")
        const prams = beforeDisplayAdapter.slice(pramsIndexLeft + 1, pramsIndexRight).split(',')
        const func = beforeDisplayAdapter.slice(funcIndexLeft + 1, funcIndexRight)
    
        // eslint-disable-next-line no-new-func
        const __beforeDisplayAdapter = new Function(
          prams[0].trim(),
          prams[1].trim(),
          prams[2].trim(),
          prams[3].trim(),
          prams[4].trim(),
          func
        )   
        let tableData = []
        state.showRange && state.showRange.map((row) => {
          tableData.push(state.data[row])
        })
        const pluginColNm = pluginList ? pluginList.length : 0
            
        state.showRange && state.showRange.map((rowIndex) => {
          const rowData = state.data[rowIndex] ? state.data[rowIndex] : []
          for (let columnIndex = 0; columnIndex < size.columns + pluginColNm; columnIndex++) {
            const cell = document.getElementById('cell_' + rowIndex + (columnIndex - 2) + ' ' + name)
            if (cell) {
              __beforeDisplayAdapter(tableData, rowData, rowIndex, columnIndex - 2, cell)
            }
          }
        })
      } catch (error) {
        showErrorMessage("Function error, please check: " + error)
      }
    }, [state.showRange])
    

