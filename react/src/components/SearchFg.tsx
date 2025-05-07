import React, { Ref, forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { validateResponse } from "../utils/sysUtil"
import CheckBox from "./CheckBox"
import ComboBox from "./ComboBox"
import ListBox from "./ListBox"
import DateBox from "./DateBox"
import * as simpleFg from "./SimpleFg"
import TextBox from "./TextBox"
import Label from "./Label"

const global = pyiLocalStorage.globalParams

interface ISearchFg {
  ref: any
  searchParams: any
  searchEvent: any
  onChangeEvent: any
  editable: boolean
}
const SearchFg: React.FC<ISearchFg> = forwardRef((props, ref: Ref<any>) => {
  const HttpGet = useHttp(global.HTTP_TYPE_GET)

  let refs: { [key: string]: React.MutableRefObject<any> } = {}
  const _useRef = useRef

  const { searchParams, editable: screenEditable } = props
  const caption = searchParams?.caption
  const name = searchParams.name
  const cols = searchParams.cols
  const fields = searchParams.fields
  const editable = screenEditable && searchParams.editable
  const searchBtn = global.PUBLIC_URL + "images/search_button.gif"
  const [updateFields, setUpdateFields] = useState<Boolean>(false)
  const [searchData, setSearchData] = useState(Object)

  fields.map((field, index) => (refs[field.name] = _useRef(null)))
  let column = cols ? cols : 1
  if (column < 0) {
    column = 1
  }
  if (column > fields.length) {
    column = fields.length
  }

  useImperativeHandle(ref, () => {
    return {
      refs,
      formDataToJson: () => {
        const formData = new FormData()
        fields.forEach((field) => {
          let value = null
          if (field.widget.trim().toLocaleLowerCase() === global.FIELD_TYPE_LIST_BOX) {
            value = Array.from(refs[field.name].current.options)
              .filter((option: any) => option.selected)
              .map((option: any) => option.value)
          } else {
            value = refs[field.name].current?.value
          }

          formData.append(field.name, value)
        })
        // convert to json format
        let jsonData: any = {}
        formData.forEach((value, key) => (jsonData[key] = value))
        setSearchData(jsonData)
        const jsonStr = JSON.stringify(jsonData)
        return jsonStr
      },
    }
  })

  useEffect(() => {
    init()
  }, [ref])

  const init = async () => {
    await initComboBox()
    setUpdateFields(true) // noted: can't delete, otherwise, will can't init combobox data
  }

  const initComboBox = async () => {
    // init fields comboBox data
    if (fields && fields.length > 0) {
      await fields.map(async (element, index) => {
        if (element.widget.trim().toLowerCase() === global.FIELD_TYPE_COMBO_BOX) {
          if (!element.widgetParameter.data || element.widgetParameter.data === null) {
            var comboBoxDataUrl = element.widgetParameter.dataUrl
            if (comboBoxDataUrl) {
              await HttpGet(comboBoxDataUrl)
                .then((response) => response.json())
                .then((result) => {
                  if (validateResponse(result, true)) {
                    element.widgetParameter.data = result.data
                  }
                })
            } else {
              pyiLogger.warn(element.name + " combobox is no data defined in screen excel, please check.")
            }
          }
        }
      })
    }
  }

  useEffect(() => {
    setSearchData(searchParams.data)
  }, [name, searchParams.data])

  return (
    <>
      <form
        name={name}
        id={name}
        onKeyDown={(e) => {
          if (e.key.toLowerCase() === "enter") {
            e.preventDefault()
          }
        }}
      >
        <label className="fieldgroup_caption">{caption}</label>
        <table className="search_layout">
          <tbody>
            <tr>
              <td valign="top" className="layout_default_td">
                <table className="property_field">
                  <tbody>
                    {simpleFg.SetRows(fields, column).map((row, rowNum) => (
                      <tr key={rowNum}>
                        {row.map((field: any, index: number) => (
                          <>
                            {field.groupTitle !== undefined ? (
                              field.groupTitle
                            ) : String(field.widget).trim().toLocaleLowerCase() === global.FIELD_TYPE_LABEL ? (
                              <Label
                                key={index}
                                ref={refs[field.name]}
                                labelLabel={field.caption}
                                labelValue={simpleFg.formatValue(searchData, field)}
                                name={field.name}
                                tip={field.tooltip}
                                style={field.style}
                                widgetParameter={field.widgetParameter}
                              />
                            ) : String(field.widget).trim().toLocaleLowerCase() === global.FIELD_TYPE_TEXT_BOX ? (
                              <TextBox
                                key={index}
                                ref={refs[field.name]}
                                textBoxLabel={field.caption}
                                textBoxValue={simpleFg.formatValue(searchData, field)}
                                name={field.name}
                                editable={editable && field.editable}
                                style={field.style}
                                widgetParameter={field.widgetParameter}
                              />
                            ) : String(field.widget).trim().toLocaleLowerCase() === global.FIELD_TYPE_COMBO_BOX ? (
                              <ComboBox
                                key={index}
                                ref={refs[field.name]}
                                comboBoxLabel={field.caption}
                                // data={searchData}
                                value={simpleFg.formatValue(searchData, field)}
                                require={field.required}
                                name={field.name}
                                onChangeEvent={props.onChangeEvent}
                                editable={editable && field.editable}
                                style={field.style}
                                widgetParameter={field.widgetParameter}
                              />
                            ) : String(field.widget).trim().toLocaleLowerCase() === global.FIELD_TYPE_LIST_BOX ? (
                              <ListBox
                                key={index}
                                ref={refs[field.name]}
                                listBoxLabel={field.caption}
                                value={simpleFg.formatValue(searchData, field)}
                                require={field.required}
                                name={field.name}
                                onChangeEvent={props.onChangeEvent}
                                editable={editable && field.editable}
                                style={field.style}
                                widgetParameter={field.widgetParameter}
                              />
                            ) : String(field.widget).trim().toLocaleLowerCase() === global.FIELD_TYPE_CHECK_BOX ? (
                              <CheckBox
                                key={index}
                                ref={refs[field.name]}
                                checkBoxLabel={field.caption}
                                value={simpleFg.formatValue(searchData, field)}
                                name={field.name}
                                editable={editable && field.editable}
                                style={field.style}
                                widgetParameter={field.widgetParameter}
                              />
                            ) : String(field.widget).trim().toLocaleLowerCase() === global.FIELD_TYPE_DATE_BOX ? (
                              <DateBox
                                key={index}
                                ref={refs[field.name]}
                                inputLabel={field.caption}
                                inputValue={simpleFg.formatValue(searchData, field)}
                                editable={editable && field.editable}
                                style={field.style}
                                widgetParameter={field.widgetParameter}
                              />
                            ) : null}
                          </>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </td>
              <td valign="top" className="layout_default_td">
                <img src={searchBtn} onClick={props.searchEvent} alt="search" />
              </td>
            </tr>
          </tbody>
        </table>
      </form>
    </>
  )
})

export default React.memo(SearchFg)
