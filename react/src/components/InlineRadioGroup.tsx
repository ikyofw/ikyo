import classnames from "classnames"
import React, { Ref, forwardRef, useEffect, useImperativeHandle, useState } from "react"
import "../../public/static/css/InlineRadioGroup.css"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import * as simpleFg from "./SimpleFg"
type RadioOption = {
  value: number
  display: string
  description?: string
  disabled?: boolean
}

interface InlineRadioGroupProps {
  ref: any
  inlineRadioGroupLabel: string
  value: any
  require: boolean
  name: string
  editable: boolean
  style?: any
  tip?: string
  widgetParameter?: any
}

const InlineRadioGroup: React.FC<InlineRadioGroupProps> = forwardRef((props, ref: Ref<any>) => {
  const HttpPost = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_POST)

  const [valueAndDisplay, setValueAndDisplay] = useState<RadioOption[]>([])
  const [selectedValues, setSelectedValues] = useState<any[]>([])
  const [columns, setColumns] = useState<number>(0)
  const [tooltip, setTooltip] = React.useState<string>("")

  const { data, dataUrl, multiple } = props.widgetParameter

  useImperativeHandle(ref, () => ({
    getSelected: () => {
      return selectedValues.join(",")
    },
  }))

  useEffect(() => {
    if (props.value !== null && props.value !== undefined) {
      let selectedValues: string[]
      if (Array.isArray(props.value)) {
        selectedValues = props.value.map((v) => String(v).trim())
      } else if (typeof props.value === "string") {
        selectedValues = props.value.split(",").map((s) => s.trim())
      } else {
        selectedValues = [String(props.value).trim()]
      }
      if (!multiple) {
        selectedValues = selectedValues.slice(0, 1)
      }

      setSelectedValues(selectedValues)
    } else if (!props.require) {
      setSelectedValues([])
    }

    const raw = props.widgetParameter?.columns
    const parsed = parseInt(raw, 10)
    if (!isNaN(parsed) && parsed > 0) {
      setColumns(parsed)
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
    } else {
      setTooltip("")
    }
  }, [props.value, props.tip, props.widgetParameter, multiple, props.require])

  useEffect(() => {
    if (data) {
      fetchDataFromData()
    } else {
      fetchDataFromUrl()
    }
  }, [props.widgetParameter, data])

  function fetchDataFromData() {
    let parseData = []
    let values = props.widgetParameter.values
    if (values) {
      values = JSON.parse(values)
    } else {
      values = { value: "value", display: "display" }
    }

    if (typeof data === "string") {
      parseData = JSON.parse(data)
    } else if (Array.isArray(data)) {
      if (typeof data[0] !== "object") {
        data.forEach((option) => {
          parseData.push({ value: String(option), display: String(option) })
        })
      } else {
        if ("value" in data[0] && "display" in data[0]) {
          data.map((option: any, index) => parseData.push({ value: option["value"], display: option["display"], description: option["description"] }))
        } else {
          data.forEach((option) => {
            parseData.push({ value: option[values.value], display: option[values.display], description: option["description"] })
          })
        }
      }
    }
    if (selectedValues.length === 0 && parseData.length > 0 && props.require) {
      setSelectedValues([String(parseData[0].value)])
    }
    setValueAndDisplay(parseData)
    if (columns === 0) {
      setColumns(parseData.length)
    }
  }
  async function fetchDataFromUrl() {
    try {
      if (!dataUrl) {
        console.warn("No dataUrl provided in widgetParameter")
        return
      }

      await HttpPost(dataUrl, JSON.stringify({ useDataUrl: true }))
        .then((response) => response.json())
        .then((result) => {
          if (result.data) {
            let values = props.widgetParameter.values
            if (values) {
              values = JSON.parse(values)
            } else {
              values = { value: "value", display: "display" }
            }

            let options = []
            result.data.forEach((option) => {
              options.push({ value: option[values.value], display: option[values.display], description: option["description"] })
            })
            if (selectedValues.length === 0 && options.length > 0 && props.require) {
              setSelectedValues([String(options[0].value)])
            }
            setValueAndDisplay(options)
            if (columns === 0) {
              setColumns(options.length)
            }
          }
        })
    } catch (err) {
      console.error("Failed to fetch:", err)
    }
  }

  const handleChange = (val: any) => {
    let newValues: String[]
    if (multiple) {
      newValues = selectedValues.includes(String(val)) ? selectedValues.filter((v) => v !== String(val)) : [...selectedValues, String(val)]
    } else {
      newValues = [String(val)]
    }
    setSelectedValues(newValues)
    // onChange?.(newValues)
  }

  const isSelected = (val: any) => selectedValues.includes(String(val))

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style)
  return (
    <>
      <th className="property_key">{props.inlineRadioGroupLabel}</th>
      <td className={classnames(cellClass, "tip_center")}>
        <table className="inline-radio-group__table">
          <tbody>
            {Array.from({ length: Math.ceil(valueAndDisplay.length / columns) }).map((_, rowIndex) => (
              <tr key={rowIndex}>
                {valueAndDisplay.slice(rowIndex * columns, rowIndex * columns + columns).map((opt) => {
                  const selected = isSelected(opt.value)
                  const disabled = !props.editable || opt.disabled || false

                  let classNames = "inline-radio-option"
                  if (selected) classNames += " inline-radio-option--selected"
                  if (disabled) classNames += " inline-radio-option--disabled"

                  return (
                    <td key={opt.value} className={classnames(classNames)}>
                      <label style={{ display: "inline-flex", alignItems: "center", cursor: disabled ? "not-allowed" : "pointer" }}>
                        <input
                          type={multiple ? "checkbox" : "radio"}
                          name={multiple ? undefined : props.name}
                          value={opt.value}
                          checked={selected}
                          disabled={disabled}
                          onChange={() => !disabled && handleChange(opt.value)}
                          style={{ marginRight: "8px" }}
                        />
                        <div className="inline-radio-option__label">{opt.display}</div>
                        {opt.description && <div className="inline-radio-option__description">({opt.description})</div>}
                      </label>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {tooltip ? <span className="tip">{tooltip}</span> : null}
      </td>
    </>
  )
})

export default InlineRadioGroup
