import ImgViewer from "./viewer/ImgViewer"

interface IContourViewer {
  fileUrl: any

  //px
  disWidth?: number
  disHeight?: number
}

const ContourViewer: React.FC<IContourViewer> = ({ fileUrl, disWidth, disHeight }) => {
  return (
    <div style={{ float: "left", width: "40%", height: "80%" }}>
      <ImgViewer
        fileUrl={fileUrl}
        disWidth={disWidth ? disWidth : window.innerWidth * 0.4}
        disHeight={disHeight ? disHeight : window.innerHeight * 0.8}
        onClose={function (): void {
          throw new Error("Function not implemented.")
        }}
      />
    </div>
  )
}

export default ContourViewer
