import { useEffect, useState } from "react"
import "../../public/static/css/Dialog-v2.css"
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
    await HttpGet("/api/auth")
      .then((response) => response.json())
      .then((result) => {
        if (Number(result.code) === 100001) {
          pyiLocalStorage.clearStore()
          window.location.href = "/login"
        } else if (Number(result.code) !== 1) {
          sysUtil.showMessage(result.messages)
        } else if (result.code === 1) {
          // checkHasNewSysMsg() // BAK
        }
      })
  }

  const checkHasNewSysMsg = async () => {
    await HttpGet("/api/ib000/getNewMsgSize")
      .then((response) => {
        if (response.ok) return response.json()
        throw response
      })
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
    window.location.href = window.location.origin + "/IB000"
  }
  return pyiLocalStorage.getCurrentUser() ? (
    <>
      <h2>Thanks for using WCI 2.0.</h2> <br />
      <CustomDialog open={dialogOpen} dialogPrams={dialogPrams} />
    </>
  ) : null
}
export default Home
