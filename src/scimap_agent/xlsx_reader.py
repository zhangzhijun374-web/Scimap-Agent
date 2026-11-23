"""Small, read-only OOXML importer for bibliographic XLSX tables.

Only reads cell values from a selected worksheet; it does not execute formulas,
macros, external links, or modify the user workbook. No Excel installation needed.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET

S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PR = '{http://schemas.openxmlformats.org/package/2006/relationships}'


def read_sheet_rows(path, preferred='合并去重936') -> list[list[object]]:
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = wb.find(S + 'sheets')
        if sheets is None or not list(sheets):
            raise ValueError('XLSX has no worksheets')
        selected = next((s for s in sheets if s.attrib.get('name') == preferred), None)
        if selected is None:
            selected = next((s for s in sheets if s.attrib.get('name','').lower() in {'records','literature','bibliography','data'}),None)
        if selected is None:
            raise ValueError(f'No bibliographic master sheet found. Expected "{preferred}" or Records/Literature/Data; specify the supported table layout.')
        relid = selected.attrib.get(R + 'id')
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next((r.attrib['Target'] for r in rels if r.attrib.get('Id') == relid), None)
        if not target:
            raise ValueError(f'Missing worksheet relationship: {relid}')
        target = target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl') / target)
        if '..' in PurePosixPath(target).parts or target not in z.namelist():
            raise ValueError('Invalid worksheet reference')
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared = [''.join(t.text or '' for t in si.iter(S+'t')) for si in root.findall(S+'si')]
        sheet = ET.fromstring(z.read(target))
        rows = []
        data = sheet.find(S + 'sheetData')
        for row in (data.findall(S+'row') if data is not None else []):
            cells = {}
            for cell in row.findall(S+'c'):
                coord = cell.attrib.get('r','')
                col = re.match(r'[A-Z]+', coord)
                if not col: continue
                index = 0
                for letter in col.group(): index = index * 26 + ord(letter) - 64
                index -= 1
                value_tag = cell.find(S+'v')
                raw = value_tag.text if value_tag is not None else None
                typ = cell.attrib.get('t','')
                if typ == 's' and raw is not None:
                    val = shared[int(raw)]
                elif typ == 'inlineStr':
                    val = ''.join(t.text or '' for t in cell.iter(S+'t'))
                elif typ == 'b':
                    val = raw == '1'
                elif raw is None:
                    val = ''
                else:
                    try:
                        val = float(raw)
                        if val.is_integer(): val = int(val)
                    except (TypeError, ValueError): val = raw
                cells[index] = val
            if cells:
                rows.append([cells.get(i, '') for i in range(max(cells)+1)])
    return rows
