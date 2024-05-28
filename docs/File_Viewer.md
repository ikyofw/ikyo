## Usage

### Add PDF Viewer and Image Viewer

[PDF Viewer](PDF_Viewer.md "PDF Viewer")

[Image Viewer](Image_Viewer.md "Image Viewer")

### FileViewer.tsx

    
    
    interface IFileViewer {
      params: any
      screenID?: string
    }
    
    function isImgFile(pathImg: string) {
      if (pathImg.startsWith("data:image")) {
        return true
      } else if (/\.(jpg|jpeg|png|GIF|JPG|PNG)$/.test(pathImg)) {
        return true
      } else {
        return false
      }
    }
    
    function isPdfFile(pathPdf: string) {
      if (pathPdf.startsWith("data:application/pdf")) {
        return true
      } else if (/\.(pdf|PDF)$/.test(pathPdf)) {
        return true
      } else {
        return false
      }
    }
    
    function is3DFile(path3D: string) {
      if (path3D.indexOf("pd001q") > -1) {
        return true
      } else {
        return false
      }
    }
    
    const FileViewer: React.FC<IFileViewer> = (props) => {
      const HttpDownload = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD)
    
      const name = props.params.name
      const caption = props.params.caption
      const dataUrl = props.params.dataUrl
      const disWidth = props.params.disWidth
      const disHeight = props.params.disHeight
    
      const [fileUrl, setFileUrl] = React.useState(dataUrl)
      if (props.screenID && props.screenID.trim().toLowerCase() === "pd001q") {
        setFileUrl(getUrl("/api/pd001q/getModel") + "?token=" + pyiLocalStorage.getToken())
      }
    
      const [showFlag, setShowFlag] = React.useState(false)
    
      React.useEffect(() => {
        if (fileUrl && is3DFile(fileUrl)) {
          setShowFlag(false)
          setTimeout(() => {
            setShowFlag(true)
          }, 1)
        }
      }, [fileUrl, props.params]) // page refresh
    
      React.useEffect(() => {
        if (dataUrl && !isPdfFile(dataUrl) && !isImgFile(dataUrl)) {
          HttpDownload(dataUrl).then((response) => {
            let respType = response.headers?.["content-type"]
            var reader = new FileReader()
            if (respType.trim().toLocaleLowerCase() === "application/json") {
              reader.onload = (e) => {
                let data = JSON.parse(e.target.result as string)
                validateResponse(data, true)
              }
              reader.readAsText(response.data)
            } else {
              const blob = new Blob([response.data])
              reader.readAsDataURL(blob)
              reader.onload = (e) => {
                let base64: string = e.target.result.toString() // data:application/octet-stream;base64, XXX
                base64 = base64.split(",")[1]
                let fileType = respType.split("/")[1]
                let newPdfBlob = "data:" + (fileType === "pdf" ? "application" : "image") + "/" + fileType + ";base64," + base64
                setFileUrl(newPdfBlob)
              }
            }
          })
        }
      }, [dataUrl])
    
      if (fileUrl) {
        if (isPdfFile(fileUrl)) {
          return <PDFViewer fileUrl={fileUrl} disWidth={disWidth ? disWidth : null} disHeight={disHeight ? disHeight : null} />
        } else if (isImgFile(fileUrl)) {
          return <ImgViewer fileUrl={fileUrl} disWidth={disWidth ? disWidth : null} disHeight={disHeight ? disHeight : null} />
        } else if (is3DFile(fileUrl)) {
          return (
            <form className="div_a" id={name} name={name}>
              <label className="fieldgroup_caption">{caption}</label>
              <div style={{ border: "1px solid black", width: "800px", height: "800px" }}>
                {showFlag ? <ThreeDViewer modelUrl={fileUrl} scale={{ x: 0.5, y: 0.5, z: 0.5 }} disWidth="800" disHeight="800" /> : null}
              </div>
            </form>
          )
        }
      }
      return null
    }
    
    export default FileViewer
    

### TestViewer.tsx

Demo1, show the file directly.

    
    
    var fileUrl=require( '../components/file/testPdf.pdf')
    <FileViewer fileUrl={fileUrl} disHeight={700} disWidth={700}/>
    

Demo2. allow user select a file and display

    
    
    import "../../public/static/css/style-v1.css"
    import PDFViewer from '../components/PDFViewer'
    import ImgViewer from '../components/ImgViewer';
    import FileViewer from '../components/FileViewer';
    import { useRef, useState } from 'react';
    
    
    
    
    const  App = () => {
    
        const[iUrl1,setIUrl1]=useState('')
    
    
    
        function chooseFile(event:any){
            let f=event.target.files[0]
            let fReader = new FileReader();
            fReader.readAsDataURL(f);
            
            fReader.onloadend = function(e){
                setIUrl1(String(e.target?.result))
            }
    
    
        }
    
    
        return <>
                    <input type="file" id="file1"  accept="image/*,application/pdf" onChange{chooseImgFile}/>
                    <FileViewer fileUrl={iUrl1} disHeight={700} disWidth={700}/>
                </>
    
    
    
    }
    
    export default App
    

