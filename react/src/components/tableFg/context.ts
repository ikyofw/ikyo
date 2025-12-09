import * as React from "react"
import { createContext } from "use-context-selector"
import reducer, { INITIAL_STATE } from "./reducer"

type ReducerStateOf<R> = R extends React.Reducer<infer S, any> ? S : never
type ReducerActionOf<R> = R extends React.Reducer<any, infer A> ? A : never

export type ReducerState = ReducerStateOf<typeof reducer>
export type Dispatch = React.Dispatch<ReducerActionOf<typeof reducer>>
export type Value = [ReducerState, Dispatch]

const context = createContext<Value>([INITIAL_STATE as ReducerState, (() => {}) as Dispatch])

export default context
