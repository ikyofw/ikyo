/**
 * @jest-environment jsdom
 */
import "@testing-library/jest-dom"
import * as React from "react"
import { act, render, screen, fireEvent } from '@testing-library/react'
import CustomDialog from "../components/Dialog"

// ---- Mocks ----

// 1) mock 全局常量
jest.mock("../utils/pyiLocalStorage", () => ({
  __esModule: true,
  default: {
    globalParams: {
      PUBLIC_URL: "/", // 用于 close 图标
      HTTP_TYPE_GET: "GET",
      DIALOG_TYPE_UPLOAD: "UPLOAD",
      DIALOG_TYPE_HOME_INBOX: "HOME_INBOX",
      SUB_SCREEN_KEY_NAME: "subScreen",
    },
  },
}))

// 2) mock 日志与工具
jest.mock("../utils/log", () => ({
  __esModule: true,
  default: { error: jest.fn(), info: jest.fn(), debug: jest.fn() },
}))

// 3) mock getResponseData：直接返回 result.data
jest.mock("../utils/sysUtil", () => ({
  __esModule: true,
  getResponseData: (resp: any) => resp?.data ?? resp,
  showInfoMessage: jest.fn(),
}))

// 4) mock useHttp：返回一个 Promise，模拟 initScreen 接口（含 fieldGroupNames）
jest.mock("../utils/http", () => ({
  __esModule: true,
  useHttp: () => {
    return (_method: string) =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            data: { fieldGroupNames: ["fg1"] },
          }),
      })
  },
}))

// 5) mock Screen：渲染占位，并把 ref.getData 返回固定数据
jest.mock("../components/Screen", () => {
  const Screen = React.forwardRef((_props: any, ref: any) => {
    React.useImperativeHandle(ref, () => ({
      getData: () => ({ foo: "bar" }),
    }))
    return <div data-testid="mock-screen">ScreenMock</div>
  })
  return { __esModule: true, default: Screen }
})

// 6) mock FileUpload：转发 ref，塞入一个可读取的 files 列表
jest.mock("../components/FileUpload", () => {
  const React = require("react") as typeof import("react")

  const FileUpload = React.forwardRef<any, any>((props, ref) => {
    const [files, setFiles] = React.useState<FileList | null>(null)

    React.useImperativeHandle(ref, () => ({
      get files() {
        return files
      },
    }))

    return (
      <td colSpan={2}>
        <input
          id="uploadField"
          data-testid="mock-file"
          type="file"
          multiple={!!props?.widgetParameter?.multiple}
          onChange={(e) => setFiles((e.target as HTMLInputElement).files)}
        />
      </td>
    )
  })

  return { __esModule: true, default: FileUpload }
})

// 7) mock ImageButton：直接渲染可点击的按钮
jest.mock("../components/ImageButton", () => {
  const ImageButton = ({ caption, clickEvent, name }: any) => (
    <button data-testid={`btn-${name || caption}`} onClick={clickEvent}>
      {caption}
    </button>
  )
  return { __esModule: true, default: ImageButton }
})

// ---- Tests ----

describe("CustomDialog", () => {
  const basePrams = {
    dialogName: "SubScreenA",
    dialogTitle: "My Title",
    dialogContent: "My Content",
    dialogWidth: 400,
    dialogHeight: 300,
    screenID: "PD001",
    cancelName: "Cancel",
    continueName: "Continue",
    onCancel: jest.fn(),
    onContinue: jest.fn(),
    openInbox: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // MUI Dialog 默认挂载到 body 即可；若你在项目里使用了自定义 Portal 容器，可在此处插入：
    // const portal = document.createElement("div"); portal.id = "iconAndText"; document.body.appendChild(portal);
  })

  test("非上传路径：渲染标题/内容，点击 Continue 传递数据并调用 onCancel", async () => {
    render(<CustomDialog open={true} dialogPrams={{ ...basePrams, dialogType: "FORM" }} />)

    // 1) 标题：MUI 的 <DialogTitle> 通常是 heading 语义
    expect(screen.getByText("My Title")).toBeInTheDocument()
    
    // 2) 内容
    expect(screen.getByText("My Content")).toBeInTheDocument()

    // 3) 等待内部 initScreen 完成并渲染 Screen（被 mock）
    expect(await screen.findByTestId("mock-screen")).toBeInTheDocument()

    // 4) 点击 Continue —— 这里我们是用 mock 的 ImageButton 渲染成 <button>
    fireEvent.click(screen.getByRole("button", { name: /continue/i }))
    // 如果你保留了 data-testid="btn-Continue"，也可以：
    // fireEvent.click(screen.getByTestId('btn-Continue'))

    expect(basePrams.onContinue).toHaveBeenCalledTimes(1)
    expect(basePrams.onContinue).toHaveBeenCalledWith({ foo: "bar" })
    expect(basePrams.onCancel).toHaveBeenCalledTimes(1)
  })

  test("上传路径：选择文件，点击 Continue 传递 FormData，并随后调用 onCancel", async () => {
    render(
      <CustomDialog
        open={true}
        dialogPrams={{
          ...basePrams,
          dialogType: "UPLOAD", // 触发上传分支
          multiple: false,
          uploadTip: "Select File",
        }}
      />
    )

    // 选择文件（通过我们 mock 的 <input type="file" />）
    const fileInput = screen.getByTestId("mock-file") as HTMLInputElement
    const file = new File(["hello"], "hello.txt", { type: "text/plain" })
    // 触发 change
    fireEvent.change(fileInput, { target: { files: [file] } })

    // 点击 Continue
    fireEvent.click(screen.getByTestId("btn-Continue"))

    // onContinue 应收到 FormData
    expect(basePrams.onContinue).toHaveBeenCalledTimes(1)
    const arg = basePrams.onContinue.mock.calls[0][0]
    expect(arg).toBeInstanceOf(FormData)

    // 验证 FormData 里有上传的文件键（uploadField_FILES_0）
    const entries = Array.from((arg as FormData).entries())
    const fileEntry = entries.find(([k]) => k === "uploadField_FILES_0")
    expect(fileEntry).toBeTruthy()
    const sentFile = (fileEntry as any)[1] as File
    expect(sentFile.name).toBe("hello.txt")

    // handleContinue 最后会调用 onCancel 一次
    expect(basePrams.onCancel).toHaveBeenCalledTimes(1)
  })

  test("点击 Cancel 直接调用 onCancel", () => {
    render(<CustomDialog open={true} dialogPrams={{ ...basePrams, dialogType: "FORM" }} />)
    fireEvent.click(screen.getByTestId("btn-Cancel"))
    expect(basePrams.onCancel).toHaveBeenCalledTimes(1)
    expect(basePrams.onContinue).not.toHaveBeenCalled()
  })
})
