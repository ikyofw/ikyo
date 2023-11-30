import * as Types from "./types"
import { range } from "./util"

const Table: Types.TableComponent = ({ children, columns, hideColumnIndicators, tableName }) => {
  const columnCount = columns + (hideColumnIndicators ? 0 : 1)
  const columnNodes = range(columnCount).map((i) => <col key={i} />)
  return (
    <table id={"table " + tableName} className="Spreadsheet__table">
      <colgroup>{columnNodes}</colgroup>
      <thead id={"thead " + tableName}>{[children[0], children[1]]}</thead>
      {/* children[0]: headerRow,  children[1]: filterRow */}
      <tbody id={"tbody " + tableName}>{children[2]}</tbody>
      {/* children[2]: normalRow */}
      <tfoot id={"tbody " + tableName}>{children[3]}</tfoot>
      {/* children[3]: footerRow */}
    </table>
  )
}

export default Table
