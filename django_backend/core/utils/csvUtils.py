from pathlib import Path
from .modelUtils import redcordsets2List

class CSVData:
    def __init__(self) -> None:
        self.data = {}
    
    def add(self, name, values) -> None:
        self.data[name] = values

    def addModelData(self, name, modelData, fields, removeDuplicateColumns = None) -> None:
        values = []
        colLastValues = {}
        for r in modelData:
            row = []
            col = -1
            for field in fields:
                col += 1
                v = r.__dict__[field]
                if removeDuplicateColumns is not None and col in removeDuplicateColumns:
                    lastV = colLastValues.get(col, None)
                    if lastV is None or lastV != v:
                        colLastValues[col] = v
                    elif lastV is not None and lastV == v:
                        v = None
                row.append(v)
                #value.append([r.seq, r.tp, r.wd, r.nh, r.kh])

            values.append(row)
        self.data[name] = values


    def getData(self) -> dict:
        return self.data



def exportModuleToCSVFile(csvFile, modelRcs, exportFieldNames, commentRows = None, headerRows = None, overwrite=True) -> None:
    '''
        This method can be use to genreate freecad csv input files. 
        The comment row starts with '#'.
    '''
    if exportFieldNames is None or len(exportFieldNames) == 0:
        raise Exception('exportFieldNames is mandatory.')
    p = Path(csvFile)
    if not overwrite and p.is_file():
        raise Exception('File [%s] is exists.' % csvFile)
    # generate csv content
    lines = []
    if commentRows is not None:
        for r in commentRows:
            if r is None:
                r = ''
            if len(r) > 0 and r[0] != '#':
                r = '#' + str(r)
            lines.append(r)
    if headerRows is not None:
        for r in headerRows:
            lines.append(r)
    if modelRcs is not None:
        for r in redcordsets2List(modelRcs, exportFieldNames):
            line = ''
            for item in r:
                if len(line) > 0:
                    line += ','
                line += '' if item is None else str(item)
            lines.append(line)
    # write to file
    csvContent = ''
    for i in range(len(lines)):
        line = lines[i]
        if i > 0:
            csvContent += '\n'
        csvContent += ('' if line is None else str(line))
    Path(p.parent).mkdir(parents=True, exist_ok=True)
    with open(csvFile, "w") as f: # overwrite
        f.write(csvContent)