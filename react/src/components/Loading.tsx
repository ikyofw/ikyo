import ReactDOM from "react-dom"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams
const loadingImgUrl = pyiGlobal.PUBLIC_URL + "images/loading.gif"

const Loading = () => {
  return (
    <div className="loading-container">
      <img className="img" src={loadingImgUrl} alt="loading" />
    </div>
  )
}
export default Loading
let loadingDiv = null
export function show() {
  if (!document.getElementById("loadingDiv")) {
    loadingDiv = document.createElement("div")
    loadingDiv.setAttribute("id", "loadingDiv")
    document.body.appendChild(loadingDiv)
    ReactDOM.render(<Loading />, loadingDiv)
  }
}

export function remove() {
  loadingDiv && ReactDOM.unmountComponentAtNode(loadingDiv) // Remove the mounted Loading component from the div
  loadingDiv && loadingDiv.parentNode?.removeChild(loadingDiv) // Removing a Mounted Container
}
