import moment from "moment"
import { useEffect, useState } from "react"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams

const TopTitle = () => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const helpImg = pyiGlobal.PUBLIC_URL + "images/help.gif"
  const newMsgsImg = pyiGlobal.PUBLIC_URL + "images/new_msg.png"
  const noMsgsImg = pyiGlobal.PUBLIC_URL + "images/no_msg.png"
  const [newMsgSize, setNewMsgSize] = useState(null)

  // check has new message
  useEffect(() => {
    if (pyiLocalStorage.getCurrentUser()) {
      // checkHasNewSysMsg() BAK
    }
  }, [])

  const checkHasNewSysMsg = async () => {
    await HttpGet("/api/ib000/getNewMsgSize")
      .then((response) => {
        if (response.ok) return response.json()
        throw response
      })
      .then((result) => {
        setNewMsgSize(result.data)
      })
  }

  function goToInbox() {
    window.location.href = window.location.origin + "/IB000"
  }

  return (
    <>
      {
        <table className="screen_title_layout">
          <tbody>
            <tr style={{ height: "25px" }}>
              <td className="screen_title_left" id="sysScreenTitle"></td>
              <td className="screen_title_center" id="sysMsgTitle"></td>
              <td className="screen_title_right">
                {(pyiLocalStorage.getCurrentUser() ? pyiLocalStorage.getCurrentUser() : "guest") + " " + moment().format("YYYY-MM-DD hh:mm:ss")}
                <a id={"sysHelp"} title="Help Document" target="_blank">
                  <img src={helpImg} alt="help img" style={{ verticalAlign: "middle", borderStyle: "none", paddingLeft: "3px" }}></img>
                </a>
                {newMsgSize != null ? (
                  <a id={"sysInbox"} title="Inbox">
                    <img
                      src={newMsgSize > 0 ? newMsgsImg : noMsgsImg}
                      alt="go to inbox"
                      title={newMsgSize > 0 ? newMsgSize + " Message(s)" : null}
                      onClick={goToInbox}
                      style={{ verticalAlign: "middle", borderStyle: "none", padding: "0 5px 0 3px" }}
                    ></img>
                  </a>
                ) : null}
              </td>
            </tr>
          </tbody>
        </table>
      }
    </>
  )
}
export default TopTitle
