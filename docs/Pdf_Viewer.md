## Usage

Reference link: <https://react-pdf-viewer.dev/docs/>

use the core@3.3.0 and default-layout plugins

### interface

[![Pdf-img.png](/images/thumb/c/c7/Pdf-img.png/500px-Pdf-
img.png)](File.md:Pdf-img.png)

### Install the package and modify

    
    
    npm install pdfjs-dist@2.13.216
    npm install @react-pdf-viewer/core@3.3.0
    npm i @react-pdf-viewer/default-layout
    

Modify:

...node_modules\@react-pdf-viewer\core\lib\cjs\core.js

line 746:

Origin:

    
    
    var maxHeight = document.body.clientHeight * 0.75;
    

Modify to:

    
    
    var maxHeight = document.documentElement.clientHeight * 0.75;
    

### PDFViewer.tsx

    
    
    import * as React from 'react';
    import { ProgressBar, ScrollMode, SpecialZoomLevel, Viewer,Worker } from '@react-pdf-viewer/core';
    import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
    
    import '@react-pdf-viewer/core/lib/styles/index.css';
    import '@react-pdf-viewer/default-layout/lib/styles/index.css';
    
    interface SwitchScrollModeInFullScreenModeExampleProps {
        fileUrl: string;
    
        //px
        disWidth?:Number;
        disHeight?:Number;
    }
    
    const SwitchScrollModeInFullScreenModeExample: React.FC<SwitchScrollModeInFullScreenModeExampleProps> = ({
        fileUrl,disWidth,disHeight
    }) => {
        const defaultLayoutPluginInstance = defaultLayoutPlugin({
            toolbarPlugin: {
                fullScreenPlugin: {
                    onEnterFullScreen: (zoom) => {
                        zoom(SpecialZoomLevel.PageFit);
                        defaultLayoutPluginInstance.toolbarPluginInstance.scrollModePluginInstance.switchScrollMode(
                            ScrollMode.Wrapped
                        );
                    },
                    onExitFullScreen: (zoom) => {
                        zoom(SpecialZoomLevel.PageWidth);
                        defaultLayoutPluginInstance.toolbarPluginInstance.scrollModePluginInstance.switchScrollMode(
                            ScrollMode.Vertical
                        );
                    },
                },
            },
        });
    
        let divWidth=disWidth?disWidth:700
        let divHeight=disHeight?disHeight:700
    
        const renderLoader = (percentages: number) => (
            <div style={{ width: '240px' }}>
                <ProgressBar progress={Math.round(percentages)} />
            </div>
        );
    
        return (
            <div style={{
                border: '1px solid rgba(0, 0, 0, 0.3)',
                display: 'flex',
                flexDirection: 'column',
                // height: '100%',
                height: String(divHeight).concat("px"),
                // width:'700px',
                width:String(divWidth).concat("px")
            }}>
                <Worker workerUrl="https://unpkg.com/pdfjs-dist@2.13.216/build/pdf.worker.min.js">
                    <Viewer fileUrl={fileUrl} plugins={[defaultLayoutPluginInstance]} />
                </Worker>
            </div>
                );
            
    };
    
    export default SwitchScrollModeInFullScreenModeExample;
    

### App.tsx

    
    
    import React from 'react';
    import './App.css';
    import PDFViewer from './components/PDFViewer'
    
    
    
    function App() {
      var fileUrl=require( './components/file/testPdf.pdf')
      return (
        <div className="App">
          {/* <CreateInfo /> */}
          <PDFViewer fileUrl={fileUrl} disHeight={700} disWidth={700}/>
        </div>
      );
    }
    
    export default App;
    

