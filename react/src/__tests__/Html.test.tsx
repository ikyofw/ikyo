/**
 * @jest-environment jsdom
 */
import "@testing-library/jest-dom"
import * as React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import Html from "../components/html/Html"

// ---------- Mocks ----------

// addStaticResource（来自 ../components/Screen）
const addStaticResource = jest.fn()
jest.mock("../components/Screen", () => ({
  __esModule: true,
  addStaticResource: (...args: any[]) => addStaticResource(...args),
}))

// useHttp（来自 ../utils/http）
const mockHttpJson = jest.fn()
jest.mock("../utils/http", () => ({
  __esModule: true,
  useHttp: () => {
    return (_method: string) =>
      Promise.resolve({
        ok: true,
        json: mockHttpJson, // 各用例自行设定返回
      })
  },
}))

// validateResponse（来自 ../utils/sysUtil）
jest.mock("../utils/sysUtil", () => ({
  __esModule: true,
  validateResponse: jest.fn(() => true),
}))

describe("Html component", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test("params.data（无脚本）：渲染文本并调用资源注入", async () => {
    render(
      <Html
        params={{ name: "html-no-script", data: `<div><b>Hello</b></div>` }}
        resources={[{ href: "/a.css" }]}
      />
    )

    const hello = await screen.findByText("Hello")
    expect(hello).toBeInTheDocument()

    expect(document.body).toContainHTML("<div><b>Hello</b></div>")

    // effect 可能跑多次，这里断言“至少有一次且参数正确”
    expect(addStaticResource).toHaveBeenCalled()
    const calledWithACss = addStaticResource.mock.calls.some(
      (args) => JSON.stringify(args[0]) === JSON.stringify({ href: "/a.css" })
    )
    expect(calledWithACss).toBe(true)
  })

  test("params.data 含内联 <script>：保留可见内容，并通过 HTML 断言脚本存在", async () => {
    const inlineJs = `window.__ran = (window.__ran||0) + 1;`
    render(
      <Html
        params={{
          name: "html-inline",
          data: `<div id="x">A</div><script>${inlineJs}</script>`,
        }}
        resources={[]}
      />
    )

    const aText = await screen.findByText("A")
    expect(aText).toBeInTheDocument()

    await waitFor(() => {
      expect(document.body).toContainHTML(
        `<script type="text/javascript">${inlineJs}</script>`
      )
    })
  })

  test("params.dataUrl：异步获取并渲染（外链 + 内联脚本），资源批量注入", async () => {
    const inlineJs = `window.__inline = 'ok';`
    const externalSrc = "https://cdn.example.com/a.js"

    // 模拟接口返回
    mockHttpJson.mockResolvedValueOnce({
      data: `<div>From URL</div>
             <script src="${externalSrc}"></script>
             <script>${inlineJs}</script>`,
    })

    render(
      <Html
        params={{ name: "html-url", dataUrl: "/fake-api/html" }}
        resources={[{ href: "/r1.css" }, { href: "/r2.css" }]}
      />
    )

    // HTML 已写入
    expect(await screen.findByText("From URL")).toBeInTheDocument()

    // 外链脚本节点出现（JSDOM 会补 type；可能呈现自闭合）
    await waitFor(() => {
      expect(document.body).toContainHTML(`<script src="${externalSrc}"`)
    })

    // 手动触发外链脚本的 load 事件，驱动组件把内联内容以新 <script> 方式追加
    /* eslint-disable testing-library/no-node-access */
    const extScript = document.querySelector(
      `script[src="${externalSrc}"]`
    ) as HTMLScriptElement | null
    extScript?.dispatchEvent(new Event("load"))
    /* eslint-enable testing-library/no-node-access */

    // 现在应能看到被追加的内联脚本（JSDOM 会自动加 type）
    await waitFor(() => {
      expect(document.body).toContainHTML(
        `<script type="text/javascript">${inlineJs}</script>`
      )
    })

    // 资源注入至少覆盖到两个资源
    expect(addStaticResource).toHaveBeenCalled()
    const payloads = addStaticResource.mock.calls.map((c) => JSON.stringify(c[0]))
    expect(payloads.filter((p) => p === JSON.stringify({ href: "/r1.css" })).length).toBeGreaterThanOrEqual(1)
    expect(payloads.filter((p) => p === JSON.stringify({ href: "/r2.css" })).length).toBeGreaterThanOrEqual(1)
  })
})
