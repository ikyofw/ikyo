import { useEffect, useState } from "react"
import CustomDialog from "../components/Dialog"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as sysUtil from "../utils/sysUtil"

const Home = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)
  const [newMsgSize, setNewMsgSize] = useState(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogPrams, setDialogPrams] = useState({ onCancel: () => closeDialog() })

  useEffect(() => {
    checkLogin()
  }, [])

  const checkLogin = async () => {
    const response = (await HttpGet("/api/auth")) as Response
    if (!response || typeof response.json !== "function") {
      console.error("No valid response from server.")
      return
    }

    const result = await response.json()
    if (Number(result.code) === 100001) {
      pyiLocalStorage.clearStore()
      window.location.href = "/login"
    } else if (Number(result.code) !== 1) {
      sysUtil.showMessage(result.messages)
    } else if (result.code === 1) {
      checkHasNewSysMsg()
    }
  }

  const checkHasNewSysMsg = async () => {
    await HttpGet("/api/inbox/get_new_msg_count")
      .then((response) => response.json())
      .then((result) => {
        if (result.data && result.data > 0) {
          // dialog
          const dialogContent = "You have " + result.data + " unread message" + (result.data === 1 ? "" : "s") + " in your inbox."
          const params = {
            dialogContent: dialogContent,
            dialogType: pyiLocalStorage.globalParams.DIALOG_TYPE_HOME_INBOX,
            onCancel: () => closeDialog(),
            openInbox: () => openInbox(),
          }
          setNewMsgSize(result.data)
          setDialogOpen(true)
          setDialogPrams(params)
        }
      })
  }

  // Dialog
  const closeDialog = () => {
    setDialogOpen(false)
  }

  const openInbox = () => {
    window.location.href = window.location.origin + "/Inbox"
  }
  return pyiLocalStorage.getCurrentUser() ? (
    <>
      <h2>Thanks for using WCI 2.0.</h2> <br />
      <CustomDialog open={dialogOpen} dialogPrams={dialogPrams} />
    </>
  ) : null
}
export default Home
