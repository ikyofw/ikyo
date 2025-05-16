import ReactDOM from "react-dom";
import pyiLocalStorage from "../utils/pyiLocalStorage"

const pyiGlobal = pyiLocalStorage.globalParams
const loadingImgUrl = pyiGlobal.PUBLIC_URL + "images/loading2.gif"

const Loading = () => {
  return (
    <div className="loading-container">
      <img className="img" src={loadingImgUrl} title="loading" />
    </div>
  )
}
export default Loading
let loadingDiv = null

export function show() {
  if (!document.getElementById("loadingDiv")) {
    loadingDiv = document.createElement("div");
    loadingDiv.setAttribute("id", "loadingDiv");
    document.body.appendChild(loadingDiv);
    ReactDOM.render(<Loading />, loadingDiv); 
  }
}

export function remove() {
  if (loadingDiv) {
    ReactDOM.unmountComponentAtNode(loadingDiv) // Unmount the component from the container
    loadingDiv.parentNode?.removeChild(loadingDiv) // Remove the container from the DOM
    loadingDiv = null // Reset loadingDiv to null
  }
}