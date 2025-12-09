import { createRoot, Root } from "react-dom/client"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const { PUBLIC_URL } = pyiLocalStorage.globalParams
const loadingImgUrl = PUBLIC_URL + "images/loading2.gif"

const Loading = () => (
  <div className="loading-container">
    <img className="img" src={loadingImgUrl} alt="loading" />
  </div>
)

export default Loading

// Keep singleton references
let loadingDiv: HTMLDivElement | null = null
let loadingRoot: Root | null = null

export function show() {
  // already mounted → do nothing
  if (loadingRoot) return

  // create container
  loadingDiv = document.createElement("div")
  loadingDiv.id = "loadingDiv"
  document.body.appendChild(loadingDiv)

  // create root once, then render
  loadingRoot = createRoot(loadingDiv)
  loadingRoot.render(<Loading />)
}

export function remove() {
  if (!loadingRoot) return

  // unmount the same root
  loadingRoot.unmount()
  loadingRoot = null

  // remove container
  if (loadingDiv?.parentNode) {
    loadingDiv.parentNode.removeChild(loadingDiv)
  }
  loadingDiv = null
}
