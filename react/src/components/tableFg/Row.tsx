import * as Types from "./types"

const Row: Types.RowComponent = ({ tableName, row, ...restProps }) => <tr id={"row_" + row + " " + tableName} {...restProps} />

export default Row
