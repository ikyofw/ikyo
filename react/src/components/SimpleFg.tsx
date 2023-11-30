import React, { Ref, forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react"
import { useHttp } from "../utils/http"
import pyiLogger from "../utils/log"
import pyiLocalStorage from "../utils/pyiLocalStorage"
import { showInfoMessage, validateResponse } from "../utils/sysUtil"
import AdvancedComboBox from "./AdvancedComboBox"
import AdvancedSelection from "./AdvancedSelection"
import CheckBox from "./CheckBox"
import ComboBox from "./ComboBox"
import DateBox from "./DateBox"
import FileUpload from "./FileUpload"
import ImageButton from "./ImageButton"
import Label from "./Label"
import ListBox from "./ListBox"
import PasswordBox from "./PasswordBox"
import TextArea from "./TextArea"
import TextBox from "./TextBox"

interface ISimpleFg {
  ref: any
  simpleParams: any
  onChangeEvent: any
  btnClickEvent?: any
  editable: boolean
}
const SimpleFg: React.FC<ISimpleFg> = forwardRef((props, ref: Ref<any>) => {
  const HttpGet = useHttp(pyiLocalStorage.globalParams.HTTP_TYPE_GET)

  const { simpleParams, editable: screenEditable } = props
  let refs: { [key: string]: React.MutableRefObject<any> } = {}
  const _useRef = useRef
  const [data, setData] = useState({})
  const caption = simpleParams?.caption
  const name = simpleParams?.name
  const editable = screenEditable && simpleParams?.editable
  const fields = simpleParams?.fields
  const cols = simpleParams?.cols
  const [updateFields, setUpdateFields] = useState<Boolean>(false)
  const maxFieldsNum = simpleParams?.maxFieldsNum

  let column
  if (fields) {
    fields.map((field, index) => (refs[field.name] = _useRef(null)))

    column = cols ? cols : 1
    if (column < 0) {
      column = 1
    }
    if (column > fields.length) {
      column = fields.length
    }
  }
  if (maxFieldsNum && Number(maxFieldsNum) > fields.length) {
    const invisibleFieldLen = Number(maxFieldsNum) - fields.length
    for (let i = 0; i < invisibleFieldLen; i++) {
      refs["invisibleField" + String(i)] = _useRef(null)
    }
  }

  useImperativeHandle(ref, () => {
    // ref can return something
    return {
      refs,
      // get form data to parent component
      formDataToJson: () => {
        // get no used but need column sql data(these data will be handle in django)
        const formData = new FormData()
        formData.append("id", data && data["id"] ? data["id"] : "")

        // get all form field data
        fields.forEach((field) => {
          let value = null
          if (field.widget.trim().toLocaleLowerCase() === "listbox") {
            value = Array.from(refs[field.name].current.options)
              .filter((option: any) => option.selected)
              .map((option: any) => option.value)
          } else if (field.widget.trim().toLocaleLowerCase() === "advancedcombobox") {
            value = refs[field.name].current.getSelected()
          } else if (field.widget.trim().toLocaleLowerCase() !== "button") {
            value = refs[field.name].current?.value
          }

          if (field.dataField) {
            formData.append(field.dataField, value)
          } else if (field.name) {
            formData.append(field.name, value)
          }
        })

        // convert to json format
        let jsonData: any = {}
        formData.forEach((value, key) => (jsonData[key] = value))
        setData(jsonData)
        const jsonStr = JSON.stringify(jsonData)
        return jsonStr
      },
      formData: () => {
        const formData = new FormData()
        formData.append("id", data && data["id"] ? data["id"] : "")
        fields.forEach((field) => {
          if (field.widget.trim().toLowerCase() === "file") {
            // TODO: pass a array to server (2022-11-03, Li)
            const files = refs[field.name].current?.files
            if (!files || files.length === 0) {
              formData.append(field.name, null)
            }
            if (files.length === 1) {
              const reader = new FileReader()
              reader.readAsDataURL(files[0])
              reader.onerror = () => {
                showInfoMessage("The requested file [" + files[0].name + "] could not be read, please reselect")
                const input = document.getElementById(field.name) as any
                input.value = ""
              }
              formData.append(field.name, files[0])
            } else {
              // TODO: temporary solution (2022-11-03, Li)
              for (let i = 0; i < files.length; i += 1) {
                const fileReader = new FileReader()
                const currentFile = files[i]
                fileReader.readAsDataURL(currentFile)

                fileReader.onerror = () => {
                  showInfoMessage("The requested file [" + currentFile.name + "] could not be read, please reselect")
                  const input = document.getElementById(field.name) as HTMLInputElement
                  input.value = ""
                }

                formData.append(field.name + "_FILES_" + i, currentFile)
              }
            }
          } else {
            formData.append(
              field.dataField ? field.dataField : field.name, // get sql column, if not, get field name
              refs[field.name].current?.value
            )
          }
        })
        return formData
      },
    }
  })

  useEffect(() => {
    initComboBox()
  }, [fields])

  const initComboBox = () => {
    // init fields combox data
    if (fields && fields.length > 0) {
      fields.map(async (element, index) => {
        if (element.widget.trim().toLowerCase() === "combobox") {
          if (!element.widgetParameter.data || element.widgetParameter.data === null) {
            var comboxDataUrl = element.widgetParameter.dataUrl
            if (comboxDataUrl) {
              await HttpGet(comboxDataUrl) // 3 situations, 1. string arr, no values 2. json arr, no values. 3. json arr, have values
                .then((response) => response.json())
                .then((result) => {
                  if (validateResponse(result, true)) {
                    element.widgetParameter.data = result.data
                    setUpdateFields(true) // noted: can't delete, otherwise, will can't init combobox data
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
    setData(simpleParams.data)
  }, [simpleParams.data])

  return (
    <>
      <form name={name} id={name} method="POST">
        <label className="fieldgroup_caption">{caption}</label>
        <table className="property_field">
          <tbody>
            {fields &&
              SetRows(fields, column).map((row, rowNum) => (
                <tr key={rowNum}>
                  {row.map((field, index) => (
                    <>
                      {field.groupTitle !== undefined ? (
                        field.groupTitle
                      ) : String(field.widget).trim().toLocaleLowerCase() === "label" ? (
                        <Label
                          key={index}
                          ref={refs[field.name]}
                          labelLabel={field.caption}
                          labelValue={formatValue(data, field)}
                          name={field.name}
                          tip={field.tooltip}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "textbox" ? (
                        <TextBox
                          key={index}
                          ref={refs[field.name]}
                          textBoxLabel={field.caption}
                          textBoxValue={formatValue(data, field)}
                          name={field.name}
                          editable={editable && field.editable}
                          style={field.style}
                          tip={field.tooltip}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "textarea" ? (
                        <TextArea
                          key={index}
                          ref={refs[field.name]}
                          textAreaLabel={field.caption}
                          textAreaValue={formatValue(data, field)}
                          name={field.name}
                          editable={editable && field.editable}
                          style={field.style}
                          tip={field.tooltip}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "password" ? (
                        <PasswordBox
                          key={index}
                          ref={refs[field.name]}
                          label={field.caption}
                          name={field.name}
                          editable={editable && field.editable}
                          style={field.style}
                          tip={field.tooltip}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "combobox" ? (
                        <ComboBox
                          key={index}
                          ref={refs[field.name]}
                          comboBoxLabel={field.caption}
                          widgetParameter={field.widgetParameter}
                          // data={data}
                          value={formatValue(data, field)}
                          require={field.required}
                          name={field.name}
                          onChangeEvent={props.onChangeEvent}
                          editable={editable && field.editable}
                          style={field.style}
                          tip={field.tooltip}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "listbox" ? (
                        <ListBox
                          key={index}
                          ref={refs[field.name]}
                          listBoxLabel={field.caption}
                          value={formatValue(data, field)}
                          require={field.required}
                          name={field.name}
                          onChangeEvent={props.onChangeEvent}
                          editable={field.editable}
                          style={field.style}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "advancedcombobox" ? (
                        <AdvancedComboBox
                          key={index}
                          ref={refs[field.name]}
                          advancedComboBoxLabel={field.caption}
                          value={formatValue(data, field)}
                          require={field.required}
                          name={field.name}
                          editable={field.editable}
                          style={field.style}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "advancedselection" ? (
                        <AdvancedSelection
                          key={index}
                          ref={refs[field.name]}
                          labelLabel={field.caption}
                          labelValue={formatValue(data, field)}
                          name={field.name}
                          tip={field.tooltip}
                          editable={editable && field.editable}
                          clickPrams={[field.eventHandler, field.eventHandlerParameter]}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "checkbox" ? (
                        <CheckBox
                          key={index}
                          ref={refs[field.name]}
                          checkBoxLabel={field.caption}
                          value={formatValue(data, field)}
                          name={field.name}
                          editable={editable && field.editable}
                          tip={field.tooltip}
                          widgetParameter={field.widgetParameter}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "datebox" ? (
                        <DateBox
                          key={index}
                          ref={refs[field.name]}
                          inputLabel={field.caption}
                          inputValue={formatValue(data, field)}
                          widgetParameter={field.widgetParameter}
                          editable={editable && field.editable}
                          style={field.style}
                          tip={field.tooltip}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "button" ? (
                        <ImageButton
                          key={index}
                          isField={true}
                          caption={field.caption}
                          name={field.name}
                          widgetParameter={field.widgetParameter}
                          clickEvent={() => props.btnClickEvent([field.eventHandler, field.eventHandlerParameter, field.widgetParameter])}
                          editable={props.editable && field.editable}
                        />
                      ) : String(field.widget).trim().toLocaleLowerCase() === "file" ? (
                        <FileUpload
                          key={index}
                          ref={refs[field.name]}
                          fileBoxLabel={field.caption}
                          name={field.name}
                          widgetParameter={field.widgetParameter}
                          editable={true}
                        />
                      ) : (
                        // default use Label
                        <Label
                          key={index}
                          ref={refs[field.name]}
                          labelLabel={field.caption}
                          labelValue={formatValue(data, field)}
                          name={field.name}
                          tip={field.tooltip}
                          widgetParameter={field.widgetParameter}
                        />
                      )}
                    </>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </form>
    </>
  )
})
export default React.memo(SimpleFg)

export function SetRows(fields: any[], column: number) {
  let rows = []
  let row1: any[] = []
  let column_index = 1
  fields.forEach((field) => {
    if (field.groupTitle !== undefined) {
      if (row1 !== undefined) {
        rows.push(row1)
        row1 = []
      }
      column_index = column
    }
    row1.push(field)
    if (column_index == column) {
      rows.push(row1)
      column_index = 1
      row1 = []
    } else {
      column_index = column_index + 1
    }
  })

  if (row1?.length > 0) {
    rows.push(row1)
  }

  return rows
}

export function formatValue(data: any, field: any) {
  let value = null
  if (!data) {
    return ""
  }

  if ((data[field.dataField] && data[field.dataField] !== null) || data[field.dataField] === 0 || data[field.dataField] === false) {
    value = data[field.dataField]
  } else {
    value = data[field.name]
  }

  const format = field.widgetParameter && field.widgetParameter["format"] ? field.widgetParameter["format"] : ""
  if (format && !isNaN(value)) {
    const index = format.indexOf(".")
    let newValue = Number(value) as any
    if (index !== -1) {
      const digits = format.slice(index + 1).length
      newValue = newValue.toFixed(Number(digits))
      newValue = newValue.replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",")
    }
    value = newValue
  }
  return value
}
