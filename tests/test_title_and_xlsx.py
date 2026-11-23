from scimap_agent.term_extraction import extract_terms
from scimap_agent.extended_analysis import resolve_term_source, prepare_with_terms
from scimap_agent.xlsx_reader import read_sheet_rows
import pandas as pd
import zipfile


def test_terms_not_misrepresented_as_author_keywords():
    raw=pd.DataFrame([{'record_id':'X1','year':'2024','title':'Machine learning for oil refinery carbon emissions',
           'doi':'','abstract':'','authors':'','author_keywords':'','index_keywords':'','citations':''}])
    out=prepare_with_terms(raw,'title',None,None)
    assert 'machine learning' in out.iloc[0]['keywords']
    assert 'oil refinery' in out.iloc[0]['keywords']
    assert not out.iloc[0]['author_keywords']
    assert out.iloc[0]['term_source'].startswith('title')


def test_auto_selects_title_if_no_keyword_abstract():
    raw=pd.DataFrame([{'author_keywords':'','index_keywords':'','abstract':'', 'title':'Carbon emissions'}])
    assert resolve_term_source(raw)=='title'


def test_english_terms_counted_once_per_paper():
    assert extract_terms('Refinery refinery and machine learning at oil refineries').count('oil refinery')==1


def test_xlsx_importer_inline_strings(tmp_path):
    p=tmp_path/'mini.xlsx'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('xl/workbook.xml','''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="合并去重936" sheetId="1" r:id="r1" /></sheets></workbook>''')
        z.writestr('xl/_rels/workbook.xml.rels','''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/sheet1.xml" /></Relationships>''')
        z.writestr('xl/worksheets/sheet1.xml','''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Title</t></is></c><c r="B1" t="inlineStr"><is><t>Year</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Refinery</t></is></c><c r="B2"><v>2025</v></c></row></sheetData></worksheet>''')
    assert read_sheet_rows(p)==[['Title','Year'],['Refinery',2025]]
