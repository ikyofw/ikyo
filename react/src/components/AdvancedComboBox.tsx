import transform from "css-to-react-native"
import React, { useImperativeHandle, Ref, forwardRef, useEffect, useState } from "react"
import classnames from "classnames"
import * as simpleFg from "./SimpleFg"
import { useHttp } from "../utils/http"
import pyiLocalStorage from "../utils/pyiLocalStorage"

import "../../public/static/css/AdvancedCombobox.css"

interface Option {
  value: string
  display: string
  description?: string
}
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

  const [selectedValues, setSelectedValues] = useState<Set<string>>(new Set())
  const [valueAndDisplay, setValueAndDisplay] = useState([])
  const [tooltip, setTooltip] = React.useState("")

  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false)
  const [error, setError] = useState<string>("")
  const containerRef = React.useRef<HTMLDivElement>(null)

  const server_filter = (() => {
    const raw = props.widgetParameter?.server_filter
    if (typeof raw === "boolean") return raw
    if (typeof raw === "string") return raw.toLowerCase() === "true"
    return false
  })()
  const page_size = (() => {
    const raw = props.widgetParameter?.page_size
    const parsed = parseInt(raw, 10)
    return !isNaN(parsed) && parsed > 0 ? parsed : 0
  })()
  const disabled = !props.editable

  const pagedOptions = React.useMemo(() => {
    const start = (page - 1) * page_size
    return valueAndDisplay.slice(start, start + page_size)
  }, [page, page_size, valueAndDisplay])
  const optionsToRender = page_size && page_size !== 0 ? pagedOptions : valueAndDisplay

  useImperativeHandle(
    ref,
    () => ({
      getSelected: () => Array.from(selectedValues).join(","),
    }),
    [selectedValues]
  )

  useEffect(() => {
    if (props.value) {
      let selected: string[]
      if (Array.isArray(props.value)) {
        selected = props.value.map((v) => String(v).trim())
      } else if (typeof props.value === "string") {
        selected = props.value.split(",").map((s) => s.trim())
      } else {
        selected = [String(props.value).trim()]
      }

      setSelectedValues(new Set(selected))
    } else {
      setSelectedValues(new Set())
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
  }, [props.value, props.tip])

  const data = props.widgetParameter.data
  useEffect(() => {
    if (data) {
      fetchDataFromData()
    } else {
      fetchDataFromUrl()
    }
  }, [props.widgetParameter, data])

  const valueMap = React.useMemo(() => {
    const raw = props.widgetParameter?.values
    try {
      return raw ? JSON.parse(raw) : { value: "value", display: "display" }
    } catch {
      return { value: "value", display: "display" }
    }
  }, [props.widgetParameter?.values])

  function fetchDataFromData(search: string = "") { 
    let parseData = []
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
            parseData.push({ value: option[valueMap.value], display: option[valueMap.display], description: option["description"] })
          })
        }
      }
    }
    if (search.trim() !== "") {
      parseData = parseData.filter((item) => item.display.toLowerCase().includes(search.toLowerCase()))
    }
    setValueAndDisplay(parseData)
  }
  async function fetchDataFromUrl(search: string = "") {
    try {
      const dataUrl = props.widgetParameter.dataUrl
      if (!dataUrl) {
        console.warn("No dataUrl provided in widgetParameter")
        return
      }
      setLoading(true)
      setError("")

      await HttpPost(dataUrl, JSON.stringify({ useDataUrl: true, search: search.trim() }))
        .then((response) => response.json())
        .then((result) => {
          if (result.data) {
            let options = []
            result.data.forEach((option) => {
              options.push({ value: option[valueMap.value], display: option[valueMap.display], description: option["description"] })
            })
            setValueAndDisplay(options)
          }
        })
    } catch (err) {
      console.error("Failed to fetch:", err)
      setError(err instanceof Error ? err.message : "Failed to fetch data")
      // setRawData([])
    } finally {
      setLoading(false)
    }
  }

  const { cellStyle, cellClass } = simpleFg.formatCss(props.style)

  const handleClickOutside = (event: MouseEvent) => {
    if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
      setOpen(false)
    }
  }
  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleComboboxClick = () => {
    if (!open && !hasInitiallyLoaded) {
      setHasInitiallyLoaded(true)
    }
    setOpen(!open)
  }
  const handleClearSelected = () => {
    setSelectedValues(new Set())
  }

  const toggleSelection = React.useCallback(
    (opt: Option) => {
      if (disabled) return
      setSelectedValues((prev) => {
        const next = new Set(prev)
        const val = String(opt.value)
        next.has(val) ? next.delete(val) : next.add(val)
        return next
      })
    },
    [disabled]
  )
  const selectedDisplays = React.useMemo(() => {
    return valueAndDisplay.filter((opt) => selectedValues.has(String(opt.value))).map((opt) => opt.display)
  }, [selectedValues, valueAndDisplay])

  const debounceRef = React.useRef<number | undefined>(undefined)

  useEffect(() => {
    window.clearTimeout(debounceRef.current)

    debounceRef.current = window.setTimeout(() => {
      if (server_filter) {
        fetchDataFromUrl(search)
      } else {
        fetchDataFromData(search)
      }
    }, 300)

    return () => window.clearTimeout(debounceRef.current)
  }, [search, server_filter])

  const IAdvancedComboBoxNode = React.useMemo(
    () => (
      <>
        <th className="property_key">{props.advancedComboBoxLabel}</th>
        <td className={classnames(cellClass, "tip_center")}>
          <div ref={containerRef} className="flex_centered">
            <div id={"advanced_select_" + props.name} className="advanced_select">
              <div
                id="advanced_select_container"
                className={`dropdown-container ${disabled ? "disabled" : selectedValues.size > 0 ? "selected" : ""}`}
                onClick={disabled ? undefined : handleComboboxClick}
              >
                {selectedValues.size > 0 ? selectedDisplays.join(", ") : disabled ? "Disabled - Cannot select options" : "Select options..."}

                {/* Clear X button */}
                {selectedValues.size > 0 && !disabled && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleClearSelected()
                    }}
                    className="close-button"
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = "#c82333"
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = "#dc3545"
                    }}
                  >
                    &times;
                  </button>
                )}
              </div>
            </div>

            {open && (
              <div className="dropdown-panel">
                <input
                  type="text"
                  placeholder={disabled ? "Search disabled" : "Search..."}
                  value={search}
                  onChange={(e) => !disabled && setSearch(e.target.value)}
                  disabled={disabled}
                  className={`input-box ${disabled ? "disabled" : ""}`}
                />

                {loading ? (
                  <div style={{ textAlign: "center", padding: 20 }}>Loading...</div>
                ) : error ? (
                  <div style={{ textAlign: "center", padding: 20, color: "red" }}>Error: {error}</div>
                ) : optionsToRender.length > 0 ? (
                  optionsToRender.map((opt) => {
                    return (
                      <label key={opt.value} className={`option-item ${disabled ? "disabled" : ""}`}>
                        <input
                          type="checkbox"
                          checked={selectedValues.has(String(opt.value))}
                          onChange={() => !disabled && toggleSelection(opt)}
                          disabled={disabled}
                        />
                        <span style={{ marginLeft: 6, color: disabled ? "#999" : "inherit" }}>
                          <strong>{opt.display}</strong>
                          {disabled && <span style={{ fontSize: 12, marginLeft: 6 }}>(disabled)</span>}
                          {opt.description && (
                            <span style={{ fontSize: 12, color: disabled ? "#bbb" : "#777", marginLeft: 6 }}>({opt.description})</span>
                          )}
                        </span>
                      </label>
                    )
                  })
                ) : search.trim() !== "" ? (
                  <div style={{ textAlign: "center", padding: 20, color: "#666" }}>No results found for "{search}"</div>
                ) : !hasInitiallyLoaded ? (
                  <div style={{ textAlign: "center", padding: 20, color: "#666" }}>Click to load options...</div>
                ) : (
                  <div style={{ textAlign: "center", padding: 20, color: "#666" }}>No options available</div>
                )}

                {!loading && !error && page_size !== 0 && optionsToRender.length > 0 && (
                  <div className="action-bar">
                    <button
                      type="button"
                      onClick={() => setPage((p) => Math.max(p - 1, 1))}
                      disabled={page === 1}
                      className={`page-button ${page === 1 ? "disabled" : ""}`}
                    >
                      Prev
                    </button>
                    <span style={{ fontSize: "12px", color: "#666" }}>
                      Page {page} of {Math.ceil(valueAndDisplay.length / page_size)}
                    </span>
                    <button
                      type="button"
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page * page_size >= valueAndDisplay.length}
                      className={`page-button ${page * page_size >= valueAndDisplay.length ? "disabled" : ""}`}
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          {tooltip ? <span className="tip">{tooltip}</span> : null}
        </td>
      </>
    ),
    [props.advancedComboBoxLabel, valueAndDisplay, optionsToRender, selectedValues, search, tooltip, open, loading, page]
  )

  useEffect(() => {
    const container = document.getElementById(`advanced_select_${props.name}`)
    cellStyle.forEach((style) => {
      let value = style[1]
      if (style[0].toLocaleLowerCase() === "width" && !value.endsWith("%")) {
        // If the property is "width" and the unit is not a percentage, it will be processed in the original: width + 3
        const currentValue = parseFloat(value)
        const unit = value.replace(String(currentValue), "").trim()
        value = currentValue + 2 + unit
      }
      container.style.setProperty(style[0], value)
    })
  }, [IAdvancedComboBoxNode])

  return <>{IAdvancedComboBoxNode}</>
})
export default AdvancedComboBox
