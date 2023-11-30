import React from "react"
import ThreeDViewer from "./ThreeDViewer"
import { getUrl } from "../../utils/http"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

interface ThreeDProps {
  params: any
}

const ThreeD: React.FC<ThreeDProps> = (props) => {
  const name = props.params.name
  const caption = props.params.caption
  
  const [showFlag, setShowFlag] = React.useState(false)

  React.useEffect(() => {
    setShowFlag(false)
    setTimeout(() => {
      setShowFlag(true)
    }, 1)
  }, [props.params]) // page refresh

  const modelUrl =
    getUrl("/api/pd001q/getModel") + "?token=" + pyiLocalStorage.getToken()

  return (
    <form className="div_a" id={name} name={name}>
      <label className="fieldgroup_caption">{caption}</label>
      <div style={{ border: "1px solid black", width: "800px", height: "800px" }}>
        {showFlag ? (
          <ThreeDViewer
            modelUrl={modelUrl}
            scale={{ x: 0.5, y: 0.5, z: 0.5 }}
            disWidth="800"
            disHeight="800"
          />
        ) : null}
      </div>
    </form>
  )
}
export default ThreeD
