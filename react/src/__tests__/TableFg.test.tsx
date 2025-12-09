/**
 * @jest-environment jsdom
 *
 * General test of TableFg (modernized).
 * - Prefer user-event over fireEvent for interactions
 * - Avoid manual act; rely on RTL auto-act + waitFor where needed
 * - Keep minimal direct DOM access only when TableFg’s custom IDs are necessary
 */
/* eslint-disable testing-library/no-node-access */
import React from "react"
import { render, waitFor ,fireEvent } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import TableFg, { createIconColumn, Props } from "../components/TableFg"
import * as Types from "../components/tableFg/types"
import { MemoryRouter } from "react-router-dom"

beforeEach(() => {
  jest.clearAllMocks()
})

afterEach(() => {
  jest.useRealTimers()
})

function renderWithRouter(ui: React.ReactElement, initialEntries: string[] = ["/"]) {
  return render(<MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>)
}

const EXAMPLE_DATA = [
  { a: "12345", b: "" },
  { a: "", b: "" },
  { a: "", b: "" },
  { a: "", b: "" },
]

const makeProps = (overrides: Partial<Props<Types.CellBase<string>>> = {}): Props<Types.CellBase<string>> => ({
  tableParams: {
    name: "EXAMPLE_TABLE",
    data: EXAMPLE_DATA,
    editable: true,
    insertable: true,
    deletable: true,
    type: "table",
    fields: [{ dataField: "a", visible: true }, { dataField: "b", visible: true }],
  },
  pluginList: [],
  refresh: jest.fn(),
  ref: undefined,
  editable: true,
  ...overrides,
})

const EXAMPLE_PROPS_01 = makeProps()
const EXAMPLE_PROPS_02 = makeProps({ tableParams: { ...EXAMPLE_PROPS_01.tableParams, editable: false } })
const EXAMPLE_PROPS_03 = makeProps({ tableParams: { ...EXAMPLE_PROPS_01.tableParams, insertable: false } })
const EXAMPLE_PROPS_04 = makeProps({ tableParams: { ...EXAMPLE_PROPS_01.tableParams, deletable: false } })
const EXAMPLE_PROPS_05 = makeProps({
  tableParams: { ...EXAMPLE_PROPS_01.tableParams, insertable: false, deletable: false },
})
const EXAMPLE_PROPS_06 = makeProps({
  tableParams: { ...EXAMPLE_PROPS_01.tableParams, editable: false, deletable: false },
})
const EXAMPLE_PROPS_07 = makeProps({
  tableParams: { ...EXAMPLE_PROPS_01.tableParams, editable: false, insertable: false },
})
const EXAMPLE_PROPS_08 = makeProps({
  tableParams: { ...EXAMPLE_PROPS_01.tableParams, editable: false, insertable: false, deletable: false },
})

const cases = [
  [EXAMPLE_PROPS_01],
  [EXAMPLE_PROPS_02],
  [EXAMPLE_PROPS_03],
  [EXAMPLE_PROPS_04],
  [EXAMPLE_PROPS_05],
  [EXAMPLE_PROPS_06],
  [EXAMPLE_PROPS_07],
  [EXAMPLE_PROPS_08],
]

describe.each(cases)("General test", (EXAMPLE_PROPS) => {
  test(`1.3 send data to parent component, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, () => {
    const testRef = { current: { data: "" as any } }
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} ref={testRef} />)
    const data = testRef.current.data["data"]
    expect(data[0][0]).toBe("")
    expect(data[0][1]).toBe(null)
    expect(data[0][2]).toBe("12345")
    expect(data[0][3]).toBe(null)
  })

  test(`3.1 click column header, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const onSelect = jest.fn()
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} onSelect={onSelect} />)

    const cellA = document.getElementById("cell_0_0 EXAMPLE_TABLE")
    await user.click(cellA!)
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenLastCalledWith([
      { row: 0, column: 2 }
    ])

    const headerB = document.getElementById("cell_-2_1 EXAMPLE_TABLE")
    fireEvent.click(headerB);
    expect(onSelect).toHaveBeenCalledTimes(2)
    expect(onSelect).toHaveBeenLastCalledWith([
      { row: 0, column: 3 },
      { row: 1, column: 3 },
      { row: 2, column: 3 },
      { row: 3, column: 3 },
    ])
  })

  test(`3.2 drag (mouse select range), editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const onSelect = jest.fn()
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} onSelect={onSelect} />)

    const tableEl = getTableFgElement()
    const tds = tableEl.querySelectorAll("table tr td.Spreadsheet__cell")
    // simulate drag from first td to fourth td
    await user.pointer([{ target: tds[0], keys: "[MouseLeft>]" }, { target: tds[3], keys: "[/MouseLeft]" }])
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  test(`3.3 shift-click range, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const onSelect = jest.fn()
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} onSelect={onSelect} />)

    const firstCell = document.getElementById("cell_0_0 EXAMPLE_TABLE")
    const thirdCell = document.getElementById("cell_1_1 EXAMPLE_TABLE")
    // Activate a cell
    fireEvent.mouseDown(firstCell)
    // Clear onSelect previous calls
    onSelect.mockClear()
    // Select range of cells
    fireEvent.mouseDown(thirdCell, {
      shiftKey: true,
    })
    // Check onSelect is called with the range of cells on selection
    expect(onSelect).toBeCalledTimes(1)
    expect(onSelect).toBeCalledWith([
      { row: 0, column: 2 },
      { row: 0, column: 3 },
      { row: 1, column: 2 },
      { row: 1, column: 3 },
    ])
  })

  test(`3.4 shift-arrow selects a range of cells, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const onSelect = jest.fn()
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} onSelect={onSelect} />)

    const thirdCell = document.getElementById("cell_1_1 EXAMPLE_TABLE")!
    await user.pointer([{ target: thirdCell, keys: "[MouseLeft]" }])
    onSelect.mockClear()

    await user.keyboard("{Shift>}{ArrowUp}{/Shift}")
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenLastCalledWith([
      { row: 0, column: 3 },
      { row: 1, column: 3 },
    ])

    await user.keyboard("{Shift>}{ArrowLeft}{/Shift}")
    expect(onSelect).toHaveBeenCalledTimes(2)
    expect(onSelect).toHaveBeenLastCalledWith([
      { row: 0, column: 2 },
      { row: 0, column: 3 },
      { row: 1, column: 2 },
      { row: 1, column: 3 },
    ])

    await user.keyboard("{Shift>}{ArrowDown}{/Shift}")
    expect(onSelect).toHaveBeenCalledTimes(3)
    expect(onSelect).toHaveBeenLastCalledWith([
      { row: 1, column: 2 },
      { row: 1, column: 3 },
    ])

    await user.keyboard("{Shift>}{ArrowRight}{/Shift}")
    expect(onSelect).toHaveBeenCalledTimes(4)
    expect(onSelect).toHaveBeenLastCalledWith([{ row: 1, column: 3 }])
  })

  test(`3.6 filter, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const img_expand = "./public/static/images/search_button.gif"
    const EXAMPLT_CALLBACK = jest.fn()
    const EXAMPLE_PLUGIN = createIconColumn(img_expand, EXAMPLT_CALLBACK)
    const DATA = [
      { a: "xyz", b: "1" },
      { a: "y", b: "123" },
      { a: "x", b: "2" },
      { a: "", b: "" },
    ]
    const tableParams = {
      ...EXAMPLE_PROPS.tableParams,
      data: DATA,
      pageType: "client" as const,
      pageSize: "2",
    }
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} pluginList={[EXAMPLE_PLUGIN]} />)

    // Get elements
    const table = getTableFgElement().querySelector("table.Spreadsheet__table")!
    const tr = table.querySelectorAll("tr")[0]
    fireEvent.mouseEnter(tr)
    const filter_icon = document.getElementsByClassName("outOfTableIcon")[3]
    fireEvent.click(filter_icon)
    let inputs = table.getElementsByClassName("filter_input")
    expect(inputs).toHaveLength(2)

    await user.click(inputs[0])
    await user.type(inputs[0], "x")
    let trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(3)
    let td_1 = trs[2].querySelectorAll("td span")[0].innerHTML
    expect(td_1).toBe("xyz")

    await user.click(inputs[1])
    await user.type(inputs[1], "2")
    trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(2)

    const pageSelect = document.querySelector(".PageSelectDiv")!
    let paging = pageSelect.querySelectorAll("img")
    expect(paging).toHaveLength(4)
    await user.click(paging[0])
    trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(3)
    td_1 = trs[2].querySelectorAll("td span")[0].innerHTML
    let td_2 = trs[2].querySelectorAll("td span")[1].innerHTML
    expect(td_1).toBe("x")
    expect(td_2).toBe("2")

    const reset_icon = document.getElementsByClassName("outOfTableIcon")[6] as HTMLElement
    await user.click(reset_icon)
    trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(4)
    td_1 = trs[2].querySelectorAll("td span")[0].innerHTML
    expect(td_1).toBe("x")

    paging = pageSelect.querySelectorAll("img")
    expect(paging).toHaveLength(4)
    await user.click(paging[2])
    await user.click(paging[3])
    trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(6)
    td_1 = trs[2].querySelectorAll("td span")[0].innerHTML
    expect(td_1).toBe("xyz")

    const cancel_icon = document.getElementsByClassName("outOfTableIcon")[5] as HTMLElement
    await user.click(cancel_icon)
    trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(5)
    td_1 = trs[1].querySelectorAll("td span")[0].innerHTML
    expect(td_1).toBe("xyz")
  })

  test(`3.7 pageable, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const DATA = Array.from({ length: 8 }, (_, i) => ({ a: String(i + 1), b: "" }))
    const tableParams = {
      ...EXAMPLE_PROPS.tableParams,
      data: DATA,
      pageType: "client" as const,
      pageSize: "2",
      type: "table" as const,
    }
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} />)

    const element = getTableFgElement()
    const table = element.querySelector("table.Spreadsheet__table")!
    let trs = table.querySelectorAll("tr")
    expect(trs).toHaveLength(3)

    const pageSelect = document.querySelector(".PageSelectDiv")!
    let buttons = pageSelect.querySelectorAll("img")
    expect(buttons).toHaveLength(4)
    await user.click(buttons[0])
    let tds = table.querySelectorAll("td span")
    expect(tds[0].innerHTML).toBe("3")

    buttons = pageSelect.querySelectorAll("img")
    expect(buttons).toHaveLength(6)
    await user.click(buttons[3])
    tds = table.querySelectorAll("td span")
    expect(tds[0].innerHTML).toBe("7")

    buttons = pageSelect.querySelectorAll("img")
    expect(buttons).toHaveLength(4)
    await user.click(buttons[1])
    tds = table.querySelectorAll("td span")
    expect(tds[0].innerHTML).toBe("5")

    await user.click(buttons[0])
    tds = table.querySelectorAll("td span")
    expect(tds[0].innerHTML).toBe("1")

    await user.click(buttons[3])
    tds = table.querySelectorAll("td span")
    expect(tds).toHaveLength(16)
    expect(tds[0].innerHTML).toBe("1")

    const select = pageSelect.querySelector("select") as HTMLSelectElement
    expect(select.options).toHaveLength(5)
    select.options[1].selected = true
    await user.click(select.options[1])

    buttons = pageSelect.querySelectorAll("img")
    // expect(buttons[0]).toBe("")
    await user.click(buttons[0])
    tds = table.querySelectorAll("td span")
    expect(tds).toHaveLength(4)
    expect(tds[0].innerHTML).toBe("3")
  })

  test(`3.8 selection mode single, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const tableParams = { ...EXAMPLE_PROPS.tableParams, selectionMode: 'single', type: "resultTable" as const }
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} />)

    const table = getTableFgElement().querySelector("table.Spreadsheet__table")!
    const trs = table.querySelectorAll("tr")

    let selectOne1 = trs[1].querySelector("th img") as HTMLImageElement
    expect(genImgName(trs[1])).toBe("checkbox_false.gif")
    await user.click(selectOne1)
    expect(genImgName(trs[1])).toBe("checkbox_true.gif")

    let selectOne2 = trs[2].querySelector("th img") as HTMLImageElement
    expect(genImgName(trs[2])).toBe("checkbox_false.gif")
    await user.click(selectOne2)
    expect(genImgName(trs[1])).toBe("checkbox_false.gif")
    expect(genImgName(trs[2])).toBe("checkbox_true.gif")

    let selectAll = trs[0].querySelector("th img") as HTMLImageElement
    expect(selectAll).toBeNull()
  })

  test(`3.9 selection mode multiple, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const tableParams = { ...EXAMPLE_PROPS.tableParams, selectionMode: 'multiple', type: "resultTable" as const }
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} />)

    const table = getTableFgElement().querySelector("table.Spreadsheet__table")!
    const trs = table.querySelectorAll("tr")

    let selectOne1 = trs[1].querySelector("th img") as HTMLImageElement
    expect(genImgName(trs[1])).toBe("checkbox_false.gif")
    await user.click(selectOne1)
    expect(genImgName(trs[1])).toBe("checkbox_true.gif")

    let selectOne2 = trs[2].querySelector("th img") as HTMLImageElement
    expect(genImgName(trs[2])).toBe("checkbox_false.gif")
    await user.click(selectOne2)
    expect(genImgName(trs[1])).toBe("checkbox_true.gif")
    expect(genImgName(trs[2])).toBe("checkbox_true.gif")

    let selectAll = trs[0].querySelector("th img") as HTMLImageElement
    expect(genImgName(trs[0])).toBe("checkbox_false.gif")
    await user.click(selectAll)
    expect(genImgName(trs[0])).toBe("checkbox_true.gif")
    expect(genImgName(trs[2])).toBe("checkbox_true.gif")
    expect(genImgName(trs[4])).toBe("checkbox_true.gif")

    await user.click(selectAll)
    selectAll = trs[0].querySelector("th img") as HTMLImageElement
    expect(genImgName(trs[0])).toBe("checkbox_false.gif")
    expect(genImgName(trs[2])).toBe("checkbox_false.gif")
    expect(genImgName(trs[4])).toBe("checkbox_false.gif")
  })

  test(`4.1 beforeDisplayAdapter, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, () => {
    const tableParams = {
      ...EXAMPLE_PROPS.tableParams,
      beforeDisplayAdapter:
        "function xxx(tableDat, rowData, rowIndex, columnIndex, cell){if (rowIndex === 1 && columnIndex === 0) {cell.innerHTML = 'EXAMPLE_VALUE'}}",
    }
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} />)
    const table = getTableFgElement().querySelector("table.Spreadsheet__table")!
    const trs = table.querySelectorAll("tr")
    const td = trs[2].querySelectorAll("td")[0]
    expect(td.innerHTML).toBe("EXAMPLE_VALUE")
  })

  test(`4.2 click in plugin icon, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const img_expand = "./public/static/images/search_button.gif"
    const EXAMPLE_CALLBACK = jest.fn()
    const EXAMPLE_PLUGIN = createIconColumn(EXAMPLE_CALLBACK, img_expand)
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} pluginList={[EXAMPLE_PLUGIN]} />)
    const plugin_th = document.getElementById("cell_0_2 EXAMPLE_TABLE")
    const plugin_icon = plugin_th!.querySelector("img")!
    await user.click(plugin_icon)
    expect(EXAMPLE_CALLBACK).toHaveBeenCalledTimes(1)
  })

  test(`4.3 page Scrolling, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const scrollIntoViewMock = jest.fn()
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} />)

    const table = getTableFgElement().querySelector("table.Spreadsheet__table")!
    const tr0 = table.querySelectorAll("tr")[0]
    await user.hover(tr0)
    const go_to_bottom = document.getElementsByClassName("outOfTableIcon")[0]
    await user.click(go_to_bottom as HTMLElement)
    expect(scrollIntoViewMock).toHaveBeenCalledTimes(1)

    const tr4 = table.querySelectorAll("tr")[4]
    await user.hover(tr4)
    const go_to_top = document.getElementsByClassName("outOfTableIcon")[5]
    await user.click(go_to_top as HTMLElement)
    expect(scrollIntoViewMock).toHaveBeenCalledTimes(2)
  })

  test(`4.4 table Scrolling, editable:${EXAMPLE_PROPS.tableParams.editable} insertable:${EXAMPLE_PROPS.tableParams.insertable} deletable:${EXAMPLE_PROPS.tableParams.deletable}`, async () => {
    const DATA = Array.from({ length: 30 }, (_, i) => ({ a: String(i + 1), b: "" }))
    const tableParams = { ...EXAMPLE_PROPS.tableParams, data: DATA }
    const user = userEvent.setup()
    renderWithRouter(<TableFg {...EXAMPLE_PROPS} tableParams={tableParams} />)

    const table = getTableFgElement().querySelector("table.Spreadsheet__table")!
    const tr0 = table.querySelectorAll("tr")[0]
    await user.hover(tr0)

    const spyRect = jest
    .spyOn(HTMLElement.prototype, "getBoundingClientRect")
    .mockImplementation(function (this: HTMLElement): DOMRect {
      if (this.id === "tbody EXAMPLE_TABLE") {
        // 返回一个 height=500 的 DOMRect
        return {
          x: 0, y: 0, top: 0, left: 0,
          width: 800, height: 500,
          right: 800, bottom: 500,
          toJSON() { return {} as any },
        } as DOMRect
      }
      // 其他元素保持 0（jsdom 默认）
      return {
        x: 0, y: 0, top: 0, left: 0,
        width: 0, height: 0,
        right: 0, bottom: 0,
        toJSON() { return {} as any },
      } as DOMRect
    })

    let enterScrollMode = document.getElementsByClassName("outOfTableIcon")[4] as HTMLImageElement
    expect(enterScrollMode.title).toBe("Enter Scroll Mode")
    await user.click(enterScrollMode)

    const exitScrollMode = document.getElementsByClassName("outOfTableIcon")[4] as HTMLImageElement
    expect(exitScrollMode.title).toBe("Exit Scroll Mode")
    fireEvent.click(exitScrollMode)

    enterScrollMode = document.getElementsByClassName("outOfTableIcon")[4] as HTMLImageElement
    expect(enterScrollMode.title).toBe("Enter Scroll Mode")
    spyRect.mockRestore()
  })
})

/* ---------- helpers ---------- */
function getTableFgElement(): Element {
  const el = document.querySelector(".Spreadsheet")
  if (!el) throw new Error("Spreadsheet root not found")
  return el
}

function genImgName(tr: Element) {
  const img = tr.querySelector("th img") as HTMLImageElement
  const tail = img.src.split("/").pop()!
  return tail
}
