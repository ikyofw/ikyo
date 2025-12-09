import React from "react"

export const suuidContext = React.createContext(null)

export const DialogContext = React.createContext({
  screenID: "",
  closeDialog: () => {},
  openDialog: (params) => {},
  createEventData: (params) => {
    return {}
  },
  setShowPdfViewer: (params) => {},
})
