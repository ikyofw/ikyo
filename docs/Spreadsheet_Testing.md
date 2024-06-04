## Some important module tests

In this section, tests will be added for some of the less generic but
important modules.

### Sort

This is an automatic test for list sorting, The implementation of the
statement is complex and will not be listed.

    
    
    test("sort", () => {
      const EXAMPLE_DATA = createEmptyMatrix<Types.CellBase<string>>(
        ROWS,
        COLUMNS
      )
      EXAMPLE_DATA[0][2] = { value: "3" }
      EXAMPLE_DATA[1][2] = { value: "1" }
      EXAMPLE_DATA[2][2] = { value: "4" }
      EXAMPLE_DATA[3][2] = { value: "2" }
      let PROPS = EXAMPLE_PROPS_EDITABLE
      PROPS["tableParams"]["data"] = EXAMPLE_DATA
      render(<TableFg {...PROPS} />)   // change example data 
      // Get elements
      const element = getTableFgElement()
      const table = safeQuerySelector(element, "table.Spreadsheet__table")
      const addRow = safeQuerySelector(table, "tr th img")
      fireEvent.click(addRow)
      fireEvent.click(addRow)   // add row, test the effect of adding new rows on sorting 
      const newTable = safeQuerySelector(element, "table.Spreadsheet__table")
      const trs = newTable.querySelectorAll("tr")
      const value1 = safeQuerySelector(trs[1], "td span").innerHTML
      const value2 = safeQuerySelector(trs[2], "td span").innerHTML
      const value3 = safeQuerySelector(trs[3], "td span").innerHTML
      const value4 = safeQuerySelector(trs[4], "td span").innerHTML
      const value5 = safeQuerySelector(trs[5], "td span").innerHTML
      const value6 = safeQuerySelector(trs[6], "td span").innerHTML
      const status5 = trs[5].querySelectorAll("th")[1].innerHTML
      const status6 = trs[6].querySelectorAll("th")[1].innerHTML
      expect(trs).toHaveLength(ROWS + 3)
      expect(value1).toBe("3")
      expect(value2).toBe("1")
      expect(value3).toBe("4")
      expect(value4).toBe("2")
      expect(value5).toBe("")
      expect(value6).toBe("")
      expect(status5).toBe("+")
      expect(status6).toBe("+")
      const cell5 = safeQuerySelector(trs[5], "td")
      const cell6 = safeQuerySelector(trs[6], "td")   // checking the initial state
    
      fireEvent.mouseDown(cell5)
      const activeCell1 = safeQuerySelector(element, ".Spreadsheet__active-cell")
      fireEvent.keyDown(activeCell1, {
        key: "F2",
      })
      const input1 = safeQuerySelector(activeCell1, "input")
      fireEvent.change(input1, {
        target: {
          value: "0",
        },
      })
      fireEvent.mouseDown(cell6)
      const activeCell2 = safeQuerySelector(element, ".Spreadsheet__active-cell")
      fireEvent.keyDown(activeCell2, {
        key: "F2",
      })
      const input2 = safeQuerySelector(activeCell2, "input")
      fireEvent.change(input2, {
        target: {
          value: "5",
        },
      })
      expect(safeQuerySelector(trs[5], "td span").innerHTML).toBe("0")
      expect(safeQuerySelector(trs[6], "td span").innerHTML).toBe("5")  // checking the state about adding new rows
    
      const rowHeader = table.querySelectorAll("th")[2]
      fireEvent.click(rowHeader)
      fireEvent.doubleClick(rowHeader)
      fireEvent.click(rowHeader)
      fireEvent.doubleClick(rowHeader)
      expect(safeQuerySelector(trs[1], "td span").innerHTML).toBe("4")
      expect(safeQuerySelector(trs[2], "td span").innerHTML).toBe("3")
      expect(safeQuerySelector(trs[3], "td span").innerHTML).toBe("2")
      expect(safeQuerySelector(trs[4], "td span").innerHTML).toBe("1")
      expect(safeQuerySelector(trs[5], "td span").innerHTML).toBe("0")
      expect(safeQuerySelector(trs[6], "td span").innerHTML).toBe("5")  
    
      fireEvent.click(rowHeader)
      fireEvent.doubleClick(rowHeader)
      expect(safeQuerySelector(trs[1], "td span").innerHTML).toBe("1")
      expect(safeQuerySelector(trs[2], "td span").innerHTML).toBe("2")
      expect(safeQuerySelector(trs[3], "td span").innerHTML).toBe("3")
      expect(safeQuerySelector(trs[4], "td span").innerHTML).toBe("4")
      expect(safeQuerySelector(trs[5], "td span").innerHTML).toBe("0")
      expect(safeQuerySelector(trs[6], "td span").innerHTML).toBe("5")   // sort and then check the sort results
    })
    

### Pageable

This is an automatic test for pageable function.

    
    
    test("pageable", () => {
      let PROPS = EXAMPLE_PROPS_EDITABLE
      const EXAMPLE_DATA = createEmptyMatrix<Types.CellBase<string>>(
        8,
        COLUMNS
      )
      EXAMPLE_DATA[0][2] = { value: "1" }
      EXAMPLE_DATA[1][2] = { value: "2" }
      EXAMPLE_DATA[2][2] = { value: "3" }
      EXAMPLE_DATA[3][2] = { value: "4" }
      EXAMPLE_DATA[4][2] = { value: "5" }
      EXAMPLE_DATA[5][2] = { value: "6" }
      EXAMPLE_DATA[6][2] = { value: "7" }
      EXAMPLE_DATA[7][2] = { value: "8" }
      PROPS["tableParams"]["data"] = EXAMPLE_DATA
      PROPS["tableParams"]["pageType"] = "client"
      PROPS["tableParams"]["pageSize"] = "2"
      render(<TableFg {...PROPS} />)
      // Get elements
      const element = getTableFgElement()
      const table = safeQuerySelector(element, "table.Spreadsheet__table")
      // Check all sub elements are rendered correctly
      const trs = table.querySelectorAll("tr")
      expect(trs).toHaveLength(3)
      const pageSelect = safeQuerySelector(document, ".PageSelectDiv")
    
      const buttons_0 = pageSelect.querySelectorAll("img")
      expect(buttons_0).toHaveLength(4)
      fireEvent.click(buttons_0[0])
      const tds_0 = table.querySelectorAll("td span")
      expect(tds_0[0].innerHTML).toBe("3")    // test about getNextPage
    
      const buttons_1 = pageSelect.querySelectorAll("img")
      expect(buttons_1).toHaveLength(6)
      fireEvent.click(buttons_1[3])
      const tds_1 = table.querySelectorAll("td span")
      expect(tds_1[0].innerHTML).toBe("7")    // test about getTheLastPage
    
      const buttons_2 = pageSelect.querySelectorAll("img")
      expect(buttons_2).toHaveLength(4)
      fireEvent.click(buttons_2[1])
      const tds_2 = table.querySelectorAll("td span")
      expect(tds_2[0].innerHTML).toBe("5")    // test about getPreviousPage
    
      fireEvent.click(buttons_2[0])
      const tds_3 = table.querySelectorAll("td span")
      expect(tds_3[0].innerHTML).toBe("1")    // test about getTheFirstPage
    
      fireEvent.click(buttons_2[3])
      const tds_4 = table.querySelectorAll("td span")
      expect(tds_4).toHaveLength(16)
      expect(tds_4[0].innerHTML).toBe("1")    // test about showAllData
    })
    

### Selectable

This is an automatic test for selectable function.

    
    
    test(`3.7 selectable, () => {
      const tableParams = {
        ...EXAMPLE_PROPS.tableParams,
        selectable: true,
        type: "resultTable",
      }
      render(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} />)
      // Get elements
      const element = getTableFgElement()
      const table = safeQuerySelector(element, "table.Spreadsheet__table")
      const trs = table.querySelectorAll("tr")
    
      let select = safeQuerySelector(trs[1], "th img") as any
      let img = genImgName(trs[1])
      expect(img).toBe("checkbox_false.gif")
      fireEvent.click(select)
      img = genImgName(trs[1])
      expect(img).toBe("checkbox_true.gif")
    
      let selectAll = safeQuerySelector(trs[0], "th img") as any
      img = genImgName(trs[0])
      expect(img).toBe("checkbox_false.gif")
      fireEvent.click(selectAll)
      img = genImgName(trs[0])
      expect(img).toBe("checkbox_true.gif")
      img = genImgName(trs[2])
      expect(img).toBe("checkbox_true.gif")
      img = genImgName(trs[4])
      expect(img).toBe("checkbox_true.gif")
    
      fireEvent.click(selectAll)
      selectAll = safeQuerySelector(trs[0], "th img") as any
      img = genImgName(trs[0])
      expect(img).toBe("checkbox_false.gif")
      img = genImgName(trs[2])
      expect(img).toBe("checkbox_false.gif")
      img = genImgName(trs[4])
      expect(img).toBe("checkbox_false.gif")
    })
    

### Page Scrolling

This is an automatic test for page scrolling function.

    
    
    test(`4.3 page Scrolling`, () => {
      let scrollIntoViewMock = jest.fn()
      window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock
      render(<TableFg {...EXAMPLE_PROPS} />)
      // Get elements
      const element = getTableFgElement()
      const table = safeQuerySelector(element, "table.Spreadsheet__table")
    
      const tr_0 = table.querySelectorAll("tr")[0]
      fireEvent.mouseEnter(tr_0)
      const go_to_bottom = document.getElementsByClassName("outOfTableIcon")[0]
      fireEvent.click(go_to_bottom)
      expect(scrollIntoViewMock).toBeCalledTimes(1)
    
      const tr_4 = table.querySelectorAll("tr")[4]
      fireEvent.mouseEnter(tr_4)
      const go_to_top = document.getElementsByClassName("outOfTableIcon")[3]
      fireEvent.click(go_to_top)
      expect(scrollIntoViewMock).toBeCalledTimes(2)
    
      fireEvent.mouseLeave(tr_0)
      fireEvent.mouseLeave(tr_4)
      const callback = () => {
        const icons = document.getElementsByClassName("outOfTableIcon")
        expect(icons).toHaveLength(0)
      }
      timerGame(callback)
    })
    

## The mindmap of test cases

[![Test
mindmap.png](images/Test_mindmap.png)](images/Test_mindmap.png)

