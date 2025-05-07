import transform from "css-to-react-native"
import React, { useImperativeHandle, Ref, forwardRef, useEffect, useState } from "react"
import classnames from "classnames"
import * as simpleFg from "./SimpleFg"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { MultiSelect } from "react-multi-select-component"

interface IAdvancedComboBox {
  ref: any
  advancedComboBoxLabel: string
  value?: any
  require: boolean
  name: string
  editable: boolean
  style?: any
  tip?: string
  widgetParameter?: any
}
const AdvancedComboBox: React.FC<IAdvancedComboBox> = forwardRef((props, ref: Ref<any>) => {
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [selectValues, setSelectValues] = useState([])
  const [valueAndDisplay, setValueAndDisplay] = useState([])
  const [tooltip, setTooltip] = React.useState("")

  useImperativeHandle(ref, () => ({
    getSelected: () => {
      return selectValues.map((option) => option["value"]).join(",")
    },
  }))

  useEffect(() => {
    if (props.value) {
      const selectedValues = props.value.split(",").map((s) => s.trim())
      const selectedOptions = valueAndDisplay.filter((option) => selectedValues.includes(String(option.value)))
      setSelectValues(selectedOptions)
    } else {
      setSelectValues([])
    }

    // set tooltip
    if (props.tip) {
      if (props.tip.includes("\\r\\n")) {
        setTooltip(props.tip.replace(/\\r\\n/g, "\r\n"))
      } else if (props.tip.includes("\\n")) {
        setTooltip(props.tip.replace(/\\n/g, "\r\n"))
      } else if (props.tip.includes("\\r")) {
        setTooltip(props.tip.replace(/\\r/g, "\r\n"))
      } else {
        setTooltip(props.tip)
      }
    }
  }, [props])

  const data = props.widgetParameter.data
  useEffect(() => {
    let values = props.widgetParameter.values
    const dataUrl = props.widgetParameter.dataUrl
    if (values) {
      values = JSON.parse(values)
    } else {
      values = { value: "value", display: "display" }
    }
    if (data) {
      if (typeof data === "string") {
        setValueAndDisplay(JSON.parse(data))
      } else if (Array.isArray(data)) {
        if (typeof data[0] !== "object") {
          let options = []
          data.forEach((option) => {
            options.push({ value: String(option), label: String(option) })
          })
          setValueAndDisplay(options)
        } else {
          if ("value" in data[0] && "display" in data[0]) {
            let options = []
            data.map((item: any, index) => options.push({ value: item["value"], label: item["display"] }))
            setValueAndDisplay(options)
          } else {
            let options = []
            data.forEach((option) => {
              options.push({ value: option[values.value], label: option[values.display] })
            })
            setValueAndDisplay(options)
          }
        }
      }
    } else if (dataUrl) {
      HttpPost(dataUrl, JSON.stringify({ useDataUrl: true }))
        .then((response) => response.json())
        .then((result) => {
          if (result.data) {
            let options = []
            result.data.forEach((option) => {
              options.push({ value: option[values.value], label: option[values.display] })
            })
            setValueAndDisplay(options)
          }
        })
    }
  }, [props.widgetParameter, data])

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style)

  const IAdvancedComboBoxNode = React.useMemo(
    () => (
      <>
        <th className="property_key">{props.advancedComboBoxLabel}</th>
        <td className={classnames(cellClass, "tip_center")}>
          <MultiSelect
            options={valueAndDisplay}
            value={selectValues}
            onChange={setSelectValues}
            hasSelectAll={false}
            className="advanced_select"
            labelledBy="Select"
          />
        </td>
        <td>{tooltip ? <span className="tip">{tooltip}</span> : null}</td>
      </>
    ),
    [props.advancedComboBoxLabel, valueAndDisplay, selectValues, tooltip]
  )

  useEffect(() => {
    function adjustSvgSize(selector) {
      const svgElements = document.querySelectorAll(selector)
      svgElements.forEach((svgElement) => {
        svgElement.setAttribute("viewBox", "0 0 24 24")
        svgElement.setAttribute("width", "18")
        svgElement.setAttribute("height", "18")
      })
    }

    const selectors = [".dropdown-search-clear-icon", ".dropdown-heading-dropdown-arrow"]
    selectors.forEach((selector) => adjustSvgSize(selector))

    const dropdownContainers = document.querySelectorAll(".advanced_select .dropdown-container") as any
    dropdownContainers.forEach((dropdownContainer) => {
      cellStyle.forEach((style) => {
        let value = style[1]
        if (style[0].toLocaleLowerCase() === "width" && !value.endsWith("%")) {
          // If the property is "width" and the unit is not a percentage, it will be processed in the original: width + 3
          const currentValue = parseFloat(value)
          const unit = value.replace(String(currentValue), "").trim()
          value = currentValue + 4 + unit
        }
        dropdownContainer.style.setProperty(style[0], value)
      })
    })
  }, [IAdvancedComboBoxNode])

  return <>{IAdvancedComboBoxNode}</>
})
export default AdvancedComboBox
