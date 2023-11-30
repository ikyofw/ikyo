import * as React from "react";
import * as Types from "./types";

const Row: Types.RowComponent = (props) => <tr id={'row_' + props.row + ' ' + props.tableName} {...props} />;

export default Row;
