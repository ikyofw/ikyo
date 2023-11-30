import { useEffect } from "react"
import pyiLocalStorage from "../utils/pyiLocalStorage"
const BeforeLogin = () => {
  useEffect(() => {
    if (pyiLocalStorage.getCurrentUser()) {
      window.location.href = "/home"
    }
  }, [])

  const goToLogin = () => {
    window.location.href = "/login"
  }
  return (
    <div className="div_center">
      <table style={{ margin: "0 auto" }}>
        <tbody>
          <tr>
            <td id="lr">
              <div>
                <h1 style={{ fontSize: "1.1em" }}>Welcome to YWL Portal - IUI</h1>
                <div
                  style={{
                    textAlign: "left",
                    marginTop: "5px",
                    paddingLeft: "198px",
                  }}
                >
                  <input
                    type="button"
                    id="showLoginPanel"
                    value="Login"
                    style={{
                      border: "0",
                      cursor: "pointer",
                      background: "red",
                      color: "#fff",
                      fontWeight: "bold",
                    }}
                    onClick={goToLogin}
                  />
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
export default BeforeLogin
