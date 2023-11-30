import React from "react"
import pyiLocalStorage from "../../utils/pyiLocalStorage"
import useDispatch from "./use-dispatch"
import * as Actions from "./actions"
import * as Point from "./point"
import * as Types from "./types"

const pyiGlobal = pyiLocalStorage.globalParams
const iconFalse = pyiGlobal.PUBLIC_URL + "images/checkbox_false.gif"
const iconTrue = pyiGlobal.PUBLIC_URL + "images/checkbox_true.gif"
const iconNull = pyiGlobal.PUBLIC_URL + "images/checkbox_null.gif"

const CHECKBOX_STATES = {
  True: "true",
  False: "false",
  Null: "null",
}

interface ICheckCell {
  stateNumber: 2 | 3
  editable: boolean
  state: string
  active: Point.Point
  initialData: any[]
}

export const CheckCell: React.FC<ICheckCell> = (props) => {
  const stateNumber = props.stateNumber
  let state = props.state.trim().toLocaleLowerCase()
  if (state !== CHECKBOX_STATES.False && state !== CHECKBOX_STATES.True && state !== CHECKBOX_STATES.Null) {
    if (stateNumber === 2) {
      state = CHECKBOX_STATES.False
    } else if (stateNumber === 3) {
      state = CHECKBOX_STATES.Null
    }
  }

  const dispatch = useDispatch()
  const setCellData = React.useCallback(
    (active: Point.Point, data: Types.CellBase, initialData?: any[], isMultiSelectBox?: boolean) =>
      dispatch(Actions.setCellData(active, data, initialData, isMultiSelectBox)),
    [dispatch]
  )

  const checkClick = () => {
    if (props.editable) {
      setCellData(props.active, { value: getNextValue(state) }, props.initialData)
    }
  }
  const scr = state === CHECKBOX_STATES.False ? iconFalse : state === CHECKBOX_STATES.Null ? iconNull : iconTrue

  return <img alt="" onClick={checkClick} src={scr} className="Spreadsheet__data-viewer" />
}

export function getNextValue(value: string) {
  var nextValue: string
  if (value === CHECKBOX_STATES.False) {
    nextValue = CHECKBOX_STATES.True
  } else if (value === CHECKBOX_STATES.True) {
    nextValue = CHECKBOX_STATES.False
  } else if (value === CHECKBOX_STATES.Null) {
    nextValue = CHECKBOX_STATES.False
  }
  return nextValue
}
