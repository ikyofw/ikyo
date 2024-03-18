import { useEffect, useState } from "react"
import { Line } from "react-chartjs-2"

import { Chart as ChartJS, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, Filler } from "chart.js"

import zoomPlugin from "chartjs-plugin-zoom"
import pyiLogger from "../../utils/log"

ChartJS.register(LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, zoomPlugin, Filler)

export function SoilProfile(props) {
  const [soilDataSet, setSoilDataSet] = useState({
    labels: [],
    datasets: [],
  })

  const [turnningPoints, setTurnningPoints] = useState([])

  const [rockLevel, setRockLevel] = useState(-100)
  useEffect(() => {
    let GetSoildDatas = props.soilData

    let dataX = []
    if (GetSoildDatas.length > 0) {
      let turnningPts = props.ptArray
      let segmentNumbers = GetSoildDatas[0].length - 2
      let TotalDistance = segmentNumbers
      let turnningX = []
      if (turnningPts.length > 1) {
        TotalDistance = 0
        for (let ptIndex = 1; ptIndex < turnningPts.length; ptIndex++) {
          let lastPt = turnningPts[ptIndex - 1]
          let currPt = turnningPts[ptIndex]
          let tempDis = Math.round(Math.sqrt(Math.pow(lastPt[0] - currPt[0], 2) + Math.pow(lastPt[1] - currPt[1], 2)))
          TotalDistance += tempDis
          turnningX.push(TotalDistance)
        }
      }

      for (let index = 1; index < GetSoildDatas[0].length; index++) {
        let splitDistance = (TotalDistance / segmentNumbers) * (index - 1)
        dataX.push(splitDistance.toFixed())
      }

      let soilDataSets = []
      let rockDepth = 0
      for (let index = 0; index < GetSoildDatas.length; index++) {
        const soildata = GetSoildDatas[index]
        let depths = []
        for (let j = 1; j < soildata.length; j++) {
          const depth = soildata[j]
          depths.push(depth)
          if (depth < rockDepth) {
            rockDepth = depth
          }
        }
      }
      rockDepth = rockDepth - (rockDepth % 50) - 50

      for (let index = 0; index < GetSoildDatas.length; index++) {
        const soildata = GetSoildDatas[index]
        let depths = []
        for (let j = 1; j < soildata.length; j++) {
          const depth = soildata[j] - rockDepth
          depths.push(depth)
        }
        let colorLayer
        props.colorLayerSets.forEach((cl) => {
          if (cl.nm === soildata[0]) {
            colorLayer = cl
          }
        })

        let soildataset = {
          label: soildata[0],
          data: depths,
          fill: true,
          // backgroundColor: colorList[index % colorList.length].backgroundColor,
          backgroundColor: colorLayer.color,
          borderColor: "black",
          borderWidth: 1,
          tension: 0.1,
          pointRadius: 0.1,
        }
        soilDataSets.unshift(soildataset)
      }
      let myDataSets2 = {
        labels: dataX,
        datasets: soilDataSets,
      }

      setSoilDataSet(myDataSets2)
      setRockLevel(rockDepth)
      setTurnningPoints(turnningX)
    }
  }, [props.soilData, props.ptArray])

  let myOptions = {
    plugins: {
      userDrawLine: {
        pts: turnningPoints,
        soils: props.soilData,
      },
      legend: {
        boxWidth: 100,
        textAlign: "left",
        position: "top",
        display: false,
      },
      tooltip: {
        callbacks: {
          title(datasets) {
            if (Array.isArray(datasets)) {
              return datasets[0].label
            } else {
              return ""
            }
          },
          label(tooltipItem) {
            // TODO: 2022-12-13, sort the layers from top to bottom.
            const layerName = tooltipItem.dataset.label
            let adjustedDepth = tooltipItem.formattedValue
            try {
              adjustedDepth = (tooltipItem.raw + rockLevel).toFixed(3)
            } catch (e) {
              pyiLogger.error(e, true)
              adjustedDepth = "error"
            }
            return layerName + ": " + adjustedDepth
          },
        },
      },
    },
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 1,
    scales: {
      y: {
        bottom: 560,
        grid: {
          display: true,
          drawTicks: true,
        },
        ticks: {
          stepSize: 5,
          autoSkip: false,
          callback: function (value, index, ticks) {
            return (value + rockLevel).toFixed(0)
          },
        },
      },
      x: {
        left: 200,
        interval: 10,
        grid: {
          display: true,
          drawTicks: true,
        },
        ticks: {
          stepSize: 50,
          autoSkip: false,
          maxRotation: 0,
          minRotation: 0,
        },
      },
    },

    title: { display: true },

    animation: { duration: 0 },
  }

  const XGridLine = (chart, ptX) => {
    let originOnCanvas = new Array(chart.chartArea.left, chart.chartArea.bottom)
    let origin = new Array(chart.scales.x.min, chart.scales.y.min)

    let xScalse = (chart.scales.x.max - chart.scales.x.min) / (chart.chartArea.right - chart.chartArea.left)
    let yScalse = (chart.scales.y.max - chart.scales.y.min) / (chart.chartArea.top - chart.chartArea.bottom)

    let canvasX = Math.round((ptX - origin[0]) / xScalse + originOnCanvas[0])
    let minY = chart.chartArea.bottom
    let maxY = chart.chartArea.top
    return [
      [canvasX, minY],
      [canvasX, maxY],
    ]
  }

  let userDrawLine = {
    id: "userDrawLine",
    afterDraw(chart, args, options) {
      const { pts, soils } = options
      const { ctx } = chart
      let ctx1 = ctx

      if (pts.length > 0 && soils.length > 0) {
        ctx1.beginPath()
        for (let i = 0; i < pts.length - 1; i++) {
          const ptX = (pts[i] / pts[pts.length - 1]) * (soils[0].length - 2)
          const gridLine = XGridLine(chart, ptX)
          ctx1.moveTo(gridLine[0][0], gridLine[0][1])
          ctx1.lineTo(gridLine[1][0], gridLine[1][1])
        }
        ctx1.strokeStyle = "black"
        ctx1.stroke()
        ctx1.save()
      }
    },
  }

  useEffect(() => {
    if (!props.showSoilData) {
      setRockLevel(-100)
      setTurnningPoints([])
      setSoilDataSet({
        labels: [],
        datasets: [],
      })
    }
  }, [props.showSoilData])

  return <Line data={soilDataSet} options={myOptions} plugins={[userDrawLine]} />
}
