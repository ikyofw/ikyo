/* eslint-disable no-array-constructor */
import { useRef, useEffect, useState } from "react";
import { Scatter, Line } from "react-chartjs-2";
import { GetSoilDataComponent } from "./GetSoilDataComponent";
import * as Loading from "../../components/Loading"
import * as sysUtil from "../../utils/sysUtil"
import { useHttp } from "../../utils/http"
import ImageButton from "../../components/ImageButton"
import pyiLogger from "../../utils/log"
import pyiLocalStorage from "../../utils/pyiLocalStorage"

import {
  Chart as ChartJS,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
} from "chart.js";

import zoomPlugin from "chartjs-plugin-zoom";
ChartJS.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  zoomPlugin
);

const colorList = [
  { backgroundColor: "rgb(255, 0, 0)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(255, 192, 0)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(255, 255, 0)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(146, 208, 80)",borderColor: "rgb(75, 192, 192)",},
  { backgroundColor: "rgb(0, 255, 0)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(0, 176, 80)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(55, 86, 35)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(0, 176, 240)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(0, 112, 192)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(0, 32, 96)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(112, 48, 160)",borderColor: "rgb(75, 192, 192)",},
  { backgroundColor: "rgb(131, 60, 12)", borderColor: "rgb(75, 192, 192)" },
  { backgroundColor: "rgb(128,128,128)", borderColor: "rgb(75, 192, 192)" },
];

export function SitePlan(props) {
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)
  const HttpDownload = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_DOWNLOAD)

  const [showSoilDataComponent,setShowSoilDataComponent] = useState(false)
  const [showSoilData, setShowSoilData] = useState(false)
  const [showContourDiv,setShowContourDiv] = useState(false)
  const [contourFileUrl,setContourFileUrl] = useState()
  const [selectLayerName,setSelectLayerName] = useState('')
  const [contourGap,setContourGap] = useState(1)
  
  const [myDataSets, setMyDataSets] = useState({
    datasets: [
      {
        label: "borehole",
        data: [],
        backgroundColor: "rgb(150,150,150)",
        borderColor: "rgb(0,0,0)",
        borderCapStyle: "butt",
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: "miter",
        pointBorderColor: "rgb(0,0,0)",
        pointBackgroundColor: "#000",
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "rgb(255,255,255)",
        pointHoverBorderColor: "rgb(0,0,0)",
        pointHoverBorderWidth: 2,
        pointRadius: 3,
        pointHitRadius: 10,
      },

      {
        label: "pilecap",
        data: [],
        backgroundColor: "rgb(255,255,255)",
        borderColor: "rgb(255,0,0)",
        borderCapStyle: "butt",
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: "miter",
        pointBorderColor: "rgb(255,0,0)",
        pointBackgroundColor: "#f00",
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "rgb(255,255,255)",
        pointHoverBorderColor: "rgb(255,0,0)",
        pointHoverBorderWidth: 2,
        pointRadius: 5,
        pointHitRadius: 10,
      },
    ],
  });

  const [area, setArea] = useState({
    minX: props.scatterData.minX,
    maxX: props.scatterData.maxX,
    minY: props.scatterData.minY,
    maxY: props.scatterData.maxY,
  });
  const chartReference = useRef(null);

  const [myLayerColorSets,setMyLayerColorSets]=useState([{nm:'',color:''}]);

  useEffect(() => {
    let dataSets = {
      datasets: [
        {
          label: "borehole",
          data: props.scatterData.GetHoleData,
          backgroundColor: "rgb(150,150,150)",
          borderColor: "rgb(0,0,0)",
          borderCapStyle: "butt",
          borderDash: [],
          borderDashOffset: 0.0,
          borderJoinStyle: "miter",
          pointBorderColor: "rgb(0,0,0)",
          pointBackgroundColor: "#000",
          pointBorderWidth: 1,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: "rgb(255,255,255)",
          pointHoverBorderColor: "rgb(0,0,0)",
          pointHoverBorderWidth: 2,
          pointRadius: 3,
          pointHitRadius: 10,
        },

        {
          label: "pilecap",
          data: props.scatterData.GetPierData,
          backgroundColor: "rgb(255,255,255)",
          borderColor: "rgb(255,0,0)",
          borderCapStyle: "butt",
          borderDash: [],
          borderDashOffset: 0.0,
          borderJoinStyle: "miter",
          pointBorderColor: "rgb(255,0,0)",
          pointBackgroundColor: "#f00",
          pointBorderWidth: 1,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: "rgb(255,255,255)",
          pointHoverBorderColor: "rgb(255,0,0)",
          pointHoverBorderWidth: 2,
          pointRadius: 5,
          pointHitRadius: 10,
        },
      ],
    };
    if (props.screenID === 'pd001s') {
      dataSets.datasets.pop()
    }
    setMyDataSets(dataSets);

    let layerColorSets=[]
    if(props.scatterData.GetLayerNames) {
      {props.scatterData.GetLayerNames.map((lynm,lyindex)=>{
        let ls={nm:lynm,color:colorList[lyindex%colorList.length]}
        layerColorSets.push(ls)
      })}
    }
    setMyLayerColorSets(layerColorSets)

  }, [props.scatterData]);

  const [lineArray, setLineArray] = useState([]);
  const [movept, setMovept] = useState([]);
  const [ptArray, setPtArray] = useState([]);
  const [escState, setEscState] = useState(false)
  const [panclickRunning, setPanclickRunning] = useState(false);
  const [drawState, setDrawState] = useState(false);

  const [contourPathArray,setContourPathArray]=useState([]);
  const [contourLabelArray,setContourLabelArray]=useState([]);
  const [currentLynm,setCurrentLynm]=useState();

  useEffect(() => {}, [lineArray]);

  const scaleOpts = {
    reverse: true,
    ticks: {
      callback: (val, index, ticks) =>
        index === 0 || index === ticks.length - 1 ? null : val,
    },
    grid: {
      color: "rgba( 0, 0, 0, 0.1)",
    },
    title: {
      display: true,
      text: (ctx) => ctx.scale.axis + " axis",
    },
  };

  const scales = {
    x: {
      position: "top",
    },
    y: {
      position: "right",
    },
  };
  Object.keys(scales).forEach((scale) =>
    Object.assign(scales[scale], scaleOpts)
  );

  const CoordinateConvert = (chart, pt) => {
    let originOnCanvas = new Array(
      chart.chartArea.left,
      chart.chartArea.bottom
    );
    let origin = new Array(chart.scales.x.min, chart.scales.y.min);

    let xScalse =
      (chart.scales.x.max - chart.scales.x.min) /
      (chart.chartArea.right - chart.chartArea.left);
    let yScalse =
      (chart.scales.y.max - chart.scales.y.min) /
      (chart.chartArea.top - chart.chartArea.bottom);

    let x = (pt[0] - originOnCanvas[0]) * xScalse + origin[0]
    let y = (pt[1] - originOnCanvas[1]) * yScalse + origin[1]

    return new Array(
      Math.round(x * 1000000) /1000000,
      Math.round(y * 1000000) /1000000
    );
  };

  const CoordinateReverse = (chart, pt) => {
    let originOnCanvas = new Array(
      chart.chartArea.left,
      chart.chartArea.bottom
    );
    let origin = new Array(chart.scales.x.min, chart.scales.y.min);

    let xScalse =
      (chart.scales.x.max - chart.scales.x.min) /
      (chart.chartArea.right - chart.chartArea.left);
    let yScalse =
      (chart.scales.y.max - chart.scales.y.min) /
      (chart.chartArea.top - chart.chartArea.bottom);

    let x = (pt[0] - origin[0]) / xScalse + originOnCanvas[0]
    let y = (pt[1] - origin[1]) / yScalse + originOnCanvas[1]

    return new Array(
      Math.round(x * 1000000) /1000000,
      Math.round(y * 1000000) /1000000
    );
  };

  const zoomOptions = {
    limits: {},
    pan: {
      enabled: true,
      mode: "xy",
      onPanStart(chart, event, point) {
        myOptions.plugins.pan.isRunning = true;
      },
      onPanComplete(chart) {
        let tempminX =
          chart.chart.scales.x.min - (chart.chart.scales.x.min % 100);
        let tempminY =
          chart.chart.scales.y.min - (chart.chart.scales.y.min % 100);
        setArea({
          minX: tempminX,
          maxX: chart.chart.scales.x.max,
          minY: tempminY,
          maxY: chart.chart.scales.y.max,
        });
        setPanclickRunning(true);
      },
    },
    zoom: {
      wheel: {
        enabled: true,
      },
      pinch: {
        enabled: true,
      },
      mode: "xy",

      onZoomStart(chart, event, point) {
        myOptions.plugins.zoom.isRunning = true;
      },

      onZoomComplete(chart) {
        myOptions.plugins.zoom.isRunning = false;
        // let tempminX =
        //   chart.chart.scales.x.min - (chart.chart.scales.x.min % 100);
        // let tempminY =
        //   chart.chart.scales.y.min - (chart.chart.scales.y.min % 100);
        setArea({
          minX: chart.chart.scales.x.min,
          maxX: chart.chart.scales.x.max,
          minY: chart.chart.scales.y.min,
          maxY: chart.chart.scales.y.max,
        });
        // setPtArray([]);
        // setMovept([]);
      },
    },
  };

  const userDrawLine = {
    id: "userDrawLine",
    afterDraw(chart, args, options) {
      const { pts, mp, dState } = options;
      const { ctx } = chart;
      // console.log(chart)
      let ctx1 = ctx;
      let ctx2 = ctx;
      //const { ctx2 } = chart;
      //ctx.save();
      // console.log(pts)
      if (pts.length > 0) {
        ctx1.beginPath();
        for (let i = 0; i < pts.length; i++) {
          const pt = pts[i];
          const canvasPt = CoordinateReverse(chart, pt);

          if (i === 0) {
            ctx1.moveTo(canvasPt[0], canvasPt[1]);
          } else {
            ctx1.lineTo(canvasPt[0], canvasPt[1]);
          }
        }
        ctx1.strokeStyle = "black";
        ctx1.lineWidth = 0.5;
        ctx1.stroke();
        ctx1.save();

        if (dState) {
          ctx2.beginPath();
          const lastPt = pts[pts.length - 1];
          const canvaLastPt = CoordinateReverse(chart, lastPt);
          const canvasMv = CoordinateReverse(chart, mp);
          ctx2.moveTo(canvaLastPt[0], canvaLastPt[1]);
          ctx2.lineTo(canvasMv[0], canvasMv[1]);
          ctx2.strokeStyle = "gray";
          ctx2.stroke(); // Stroke the current path.
        } else if (!dState && pts.length > 1) {
          const lastPt1 = pts[pts.length - 2];
          const lastPt2 = pts[pts.length - 1];
          const canvaLastPt1 = CoordinateReverse(chart, lastPt1);
          const canvaLastPt2 = CoordinateReverse(chart, lastPt2);
          const linelength = Math.sqrt(
            Math.pow(canvaLastPt2[0] - canvaLastPt1[0], 2) +
              Math.pow(canvaLastPt2[1] - canvaLastPt1[1], 2)
          );
          const lineDir = [
            (canvaLastPt2[0] - canvaLastPt1[0]) / linelength,
            (canvaLastPt2[1] - canvaLastPt1[1]) / linelength,
          ];

          let arrowlength = 20;
          let arrowwidth = 10;
          const arrowS = [
            canvaLastPt2[0] - lineDir[0] * arrowlength,
            canvaLastPt2[1] - lineDir[1] * arrowlength,
          ];

          const arrowLeft = [
            arrowS[0] + (lineDir[1] * arrowwidth) / 2,
            arrowS[1] - (lineDir[0] * arrowwidth) / 2,
          ];
          const arrowRight = [
            arrowS[0] - (lineDir[1] * arrowwidth) / 2,
            arrowS[1] + (lineDir[0] * arrowwidth) / 2,
          ];

          ctx2.beginPath();
          ctx2.moveTo(arrowLeft[0], arrowLeft[1]);
          ctx2.lineTo(canvaLastPt2[0], canvaLastPt2[1]);
          ctx2.lineTo(arrowRight[0], arrowRight[1]);
          ctx2.strokeStyle = "black";
          ctx2.stroke(); // Stroke the current path.
        }
      }
    },
  };

  const getoffSet = (e) => {
    let nodeElm = e.target;
    let offsetTop = 0;
    let offsetLeft = 0;
    let offsetWidth = nodeElm.offsetWidth
    let offsetHeight = nodeElm.offsetHeight
    while (true) {
      if (nodeElm.nodeName === "BODY") {
        break;
      }
      offsetTop += nodeElm.offsetTop;
      offsetLeft += nodeElm.offsetLeft;
      nodeElm = nodeElm.offsetParent;
    }
    return { left: offsetLeft, top: offsetTop, width: offsetWidth, height: offsetHeight };
  };

  const onMouseMove = (event) => {
    if (myOptions.plugins.pan.isRunning || myOptions.plugins.zoom.isRunning) {
      return;
    }

    let chartArea =  chartReference.current.chartArea
    
    let offset = getoffSet(event);
    let scrollTop = document.documentElement.scrollTop
    let x = event.clientX - offset.left;
    let y = event.clientY - offset.top + scrollTop;
    if (x < chartArea.left || y < chartArea.top || x > chartArea.right || y > chartArea.bottom) {
      return
    }
  
    if (ptArray.length > 0 || escState) {
      const mvPt = CoordinateConvert(chartReference.current, [x, y]);
      setMovept(mvPt);
    }
  };

  const onClick = (event) => {
    if (myOptions.plugins.pan.isRunning || myOptions.plugins.zoom.isRunning) {
      return;
    }
    
   let chartArea =  chartReference.current.chartArea
    
    let offset = getoffSet(event);
    let scrollTop = document.documentElement.scrollTop
    let x = event.clientX - offset.left;
    let y = event.clientY - offset.top + scrollTop;
    if (x < chartArea.left || y < chartArea.top || x > chartArea.right || y > chartArea.bottom) {
      return
    }

    if (panclickRunning) {
      setPanclickRunning(false);
      return;
    }

    if (escState) {
      setEscState(false)
    }
    if (!showSoilData) {
      setShowSoilData(true)
    }

    let tempArray = [...ptArray];
    if (!drawState) {
      setDrawState(true);
      tempArray = [];
    }
    
    let pt = CoordinateConvert(chartReference.current, [x, y]);
    let lastTemp = tempArray[tempArray.length - 1]
    if (lastTemp && lastTemp[0] === pt[0] && lastTemp[1] === pt[1]) {
      return
    }

    tempArray.push(pt);
    setPtArray(tempArray);

    // if (tempArray.length > 1) {
    //   setLineArray(tempArray);
    // }
  };

  const zoomReset = () => {
    setPtArray([]);
    setArea({
      minX: props.scatterData.minX,
      maxX: props.scatterData.maxX,
      minY: props.scatterData.minY,
      maxY: props.scatterData.maxY,
    });
    //chartReference.resetZoom();
  };

  const hideContour=()=>{
    setContourPathArray([])
    setContourLabelArray([])
  }

  const keyUp = (event) => {
    if (event.keyCode === 13) {
      setDrawState(false);
      if (ptArray.length > 1) {
        setLineArray(ptArray);
        setShowSoilDataComponent(true)
        setShowContourDiv(false)
        setShowSoilData(false)
      }
    } else if (event.keyCode === 27) {
      setEscState(true);
      setPtArray([])
    }
  };

  const onDoubleClick = () => {
    setDrawState(false);
    if (ptArray.length > 1) {
      setLineArray(ptArray);
      setShowSoilDataComponent(true)
      setShowContourDiv(false)
      setShowSoilData(false)
    }
  }

  /*
  const genContourImg=(lynm)=>{
    // console.log(lynm.nm)
    setShowContourDiv(true)
    setShowSoilDataComponent(false)
    Loading.show()
    try {
      HttpPost("/api/pd001n/getLayerData", "layerNm=" + lynm.nm)
        .then((response) => response.blob())
        .then((blob) => {
          let imgurl=URL.createObjectURL(blob)
          setContourFileUrl(imgurl)
          setSelectLayerName(lynm.nm)

        })
    } catch (error) {
      console.log("get layer data failed: " + error)
    } finally {
      Loading.remove()
    }
  }
  */

  const getContourPathPoints=(lynm)=>{
    Loading.show()
    setCurrentLynm(lynm)
    try {
      HttpPost("/api/" + props.screenID + "/getLayerPathData", "layerNm=" + lynm.nm+"&contourGap="+contourGap)
        .then((response) => response.json())
        .then((result) => {
          try {
            if (result.code !== 1) {
              sysUtil.showMessage(result.messages)
            } else {
              let responseData = result.data
              // console.log(responseData)
              setContourPathArray(responseData['pathLineList'])  
              setContourLabelArray(responseData['ctLabelList'])
            }
          } finally {
            Loading.remove()
          }
        })
    } catch (error) {
      pyiLogger.error("get layer data failed: " + error, true)
      Loading.remove()
    }
  }

  const downLoadLayerDxfFile=(lynm)=>{
    Loading.show()
    try{
      let data1={"layerNm":lynm.nm,"contourGap":contourGap}
      let eventHandler="/api/" + props.screenID + "/downLoadLayerDxf"
      HttpDownload(eventHandler,data1)
        .then((response) => {
          // console.log(response)
          try {
            let respType = response.headers?.["content-type"]
            if (respType.trim().toLocaleLowerCase() === "application/json") {
              var reader = new FileReader()
              reader.onload = (e) => {
                let data = JSON.parse(e.target.result)
              }
              reader.readAsText(response.data)
            } else {
              const blob = new Blob([response.data])
              // const blob=response.blob();
              // console.log(blob)
              // URL.createObjectURL(blob);
              // let imgurl=URL.createObjectURL(blob)
              let fileName = response?.headers?.["content-disposition"]?.split("filename=")[1]
              // let fileName = lynm+'.dxf'
              domDownload(fileName, blob, eventHandler)
            }
          } finally {
            Loading.remove()
          }
        })

    } catch (error) {
      pyiLogger.error("get dxf file failed: " + error, true)
      Loading.remove()
    }
  }

  const domDownload = (fileName, blob, eventHandler) => {
    if (fileName) {
      fileName = fileName.replaceAll("%20", " ")
      const linkNode = document.createElement("a")
      linkNode.download = fileName // Specify the name of the download file in the 'download' attribute of the 'a' tag.
      linkNode.style.display = "none"
      linkNode.href = URL.createObjectURL(blob) // Create Blob URL
      document.body.appendChild(linkNode)
      linkNode.click() // Simulate a mouse click on the button.
      URL.revokeObjectURL(linkNode.href) // Revoke URL
      document.body.removeChild(linkNode)
      // showInfoMessage("download success.")
    } else {
      pyiLogger.warn("Download - " + eventHandler + " no filename, please ask administrator to check.")
    }
  }


  const showContourLine = {
    id: "showContourLine",
    beforeDatasetsDraw(chart, args, options) {
      const { pts,labels,selectedLayer } = options;
      // const { pts, mp, dState } = options;
      const { ctx } = chart;
      let ctx1 = ctx;
      // ctx1.lineWidth = 0.1;
      //Draw contour lines 
      if (pts.length > 0) {
        ctx1.beginPath();
        for (let i = 0; i < pts.length; i++) {
          const pt = pts[i];
          
          if(pt[0]>chart.scales.x.min&&pt[0]<chart.scales.x.max
            &&pt[2]>chart.scales.x.min&&pt[2]<chart.scales.x.max
            &&pt[1]>chart.scales.y.min&&pt[1]<chart.scales.y.max
            &&pt[3]>chart.scales.y.min&&pt[3]<chart.scales.y.max)
            {
              let pt1=new Array(pt[0],pt[1]);
              let pt2=new Array(pt[2],pt[3]);
              

              let canvasPt1 = CoordinateReverse(chart, pt1);
              let canvasPt2 = CoordinateReverse(chart, pt2);
              ctx1.moveTo(canvasPt1[0], canvasPt1[1]);
              ctx1.lineTo(canvasPt2[0], canvasPt2[1]);

            }

          
        }
        // ctx1.strokeStyle = "red";
        ctx1.strokeStyle = "#D1D0CE";
        ctx1.lineWidth = 0.5;
        // ctx1.index=-1;
        ctx1.stroke();
        ctx1.save();       
      }

      //Draw contour labels
      // const { ctx_m } = chart;
      let ctx2 = ctx;
      // let origin = new Array(chart.scales.x.min, chart.scales.y.min);
      // console.log(origin)
      if(labels.length>0){
        for (let i = 0; i < labels.length; i++) {
          let label1=labels[i];
          let pt=new Array(label1['x'],label1['y']);
          if(pt[0]>chart.scales.x.min&&pt[0]<chart.scales.x.max
            &&pt[1]>chart.scales.y.min&&pt[1]<chart.scales.y.max){
              const canvasPt = CoordinateReverse(chart, pt);
              ctx2.textAlign = 'center';
              ctx2.textBaseline = 'middle';
              // ctx2.strokeStyle = "red";
              // ctx2.strokeStyle = "#D1D0CE";

              ctx2.strokeText(label1['text'],canvasPt[0],canvasPt[1]);
              // ctx2.strokeText(label1['text'],0,0);
              ctx2.stroke();
              ctx2.save(); 

          }
           

        }
        
      }

      
    },

  };

  

  const focusLayer=(event)=>{
    event.target.style.border="3px solid black"
  }

  const leaveLayer=(event)=>{
    event.target.style.border="1px solid black"
  }

  const changeContourGap=(event)=>{
    setContourGap(event.target.value)
    // alert(contourGap)
    // alert(currentLynm)
  }

  const spacing = 100;
  const myOptions = {
    plugins: {
      userDrawLine: {
        pts: ptArray,
        mp: movept,
        dState: drawState,
      },
      showContourLine:{
        pts: contourPathArray,
        labels:contourLabelArray,
        selectedLayer:currentLynm
      },
      legend: {
        boxWidth: 100,
        textAlign: "left",
        position: "top",
        display: true,
      },
      pan: {
        isRunning: false,
        clickRunning: false,
        enabled: true,
        modifierKey: "ctrl",
        mode: "xy",
      },
      zoom: zoomOptions,

      tooltip: {
        callbacks: {
          label: function (context) {
            return context.raw["borehole no"] || context.raw["pilecap no"];
          },
        },
      },
    },

    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 1,
    scales: {
      //distribution: "linear",
      y: {
        min: area.minY,
        max: area.maxY,
        grid: {
          display: true,
          drawTicks: true,
        },
        ticks: {
          stepSize: spacing,
          autoSkip: true,
          maxTicksLimit: spacing,
          callback: function (value, index, ticks) {
            return value.toFixed(0);
          },
        },
      },
      x: {
        min: area.minX,
        max: area.maxX,
        grid: {
          display: true,
          drawTicks: true,
        },
        ticks: {
          stepSize: spacing,
          autoSkip: true,
          maxTicksLimit: spacing,

          callback: function (value, index, ticks) {
            return value.toFixed(0);
          },
        },
      },
    },

    title: { display: false },

    animation: { duration: 0 },
  };

  return (
    <div>
      <div style={{ float: "left", width: "40%", height: "80%" }}>
        {currentLynm?
          <div style={{paddingTop: "3px"}}>
            <ImageButton caption="Generate Dxf"
              name="Generate Dxf"
              clickEvent={()=>downLoadLayerDxfFile(currentLynm)}
              widgetParameter={{"icon":"images/download_button.gif"}}
              editable={true}/>
              <div style={{paddingTop: "3px"}}>{"Show Contour Line Layer: "+ (currentLynm.nm ? currentLynm.nm : "N/A")}</div>
          </div>
        :null}
        <div style={{ paddingTop: "3px" }}>
          Contour Gap&nbsp;
          <input
            style={{ width: "40px" , textAlign:"center"}}
            defaultValue={contourGap}
            onChange={changeContourGap}
          />
          &nbsp;m
        </div>
        <Scatter
          tabIndex="0"
          data={myDataSets}
          options={myOptions}
          onClick={props.screenID !== 'pd001s' ? onClick : null}
          onMouseMove={props.screenID !== 'pd001s' ? onMouseMove : null}
          onKeyUp={keyUp}
          onDoubleClick={onDoubleClick}
          plugins={[userDrawLine,showContourLine]}
          ref={chartReference}
          style={{ outline: "none" }}
        />
        
        {/* {<><button onClick={zoomReset}>reset zoom</button>&nbsp;&nbsp;<button onClick={hideContour}>clear contour</button></>} */}
        
        {/* {<button >DownLoad Dxf</button>} */}
        

        
      </div>
      <div style={{ float: "left", width: "10%", height: "80%" }}>
        <table style={{borderSpacing:"0px",paddingTop:"40px"}}>
          <tbody>
          {myLayerColorSets.map((lynm)=>(
            <tr style={{height:"25px",paddingTop:"0px"}} key={lynm.nm}>
              <td style={{width:"60px",border:"1px solid black",background:lynm.color.backgroundColor,cursor: "pointer"}} title="click to show this layer contour line" onClick={()=>getContourPathPoints(lynm)} onMouseEnter={focusLayer} onMouseLeave={leaveLayer}></td>
              <td style={{paddingLeft:"5px"}}>
                {lynm.nm}
              </td>            
            </tr>
            )
          )}
          </tbody>
        </table>
        <div style={{paddingTop:"20px"}}>
          <button style={{width: "80px", textAlign:"center"}} onClick={zoomReset}>Reset Zoom</button>
        </div>
        <div style={{paddingTop:"6px"}}>
          <button style={{width: "80px", textAlign:"center"}} onClick={hideContour}>Clear Contour</button>
        </div>
      </div>
      

      <div hidden={!showSoilDataComponent || props.screenID === 'pd001s'}>
        <GetSoilDataComponent ptArray={lineArray} colorLayerSets={myLayerColorSets} showSoilData={showSoilData}/>
      </div>
      {/* <div hidden={!showContourDiv}>
        <ContourViewer fileUrl={contourFileUrl}/>
      </div> */}
    </div>
  );
}
