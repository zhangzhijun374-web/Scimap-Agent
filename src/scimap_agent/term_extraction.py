"""Transparent rule-based extraction of controlled research terms from titles/abstracts.

These are *inferred text terms*, NEVER original author/database keywords.
Terms and rules are editable in config/title_term_patterns.csv and auditable.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

DEFAULT_RULES = [
 ('carbon emissions',r'\b(?:carbon|co\s*2|co₂|carbon dioxide)[- ]?(?:emissions?|emitting)\b|\b(?:emissions? of co\s*2)\b'),
 ('greenhouse gas emissions',r'\b(?:ghg|greenhouse gas(?:es)?)[- ]?emissions?\b'),
 ('oil refinery',r'\b(?:oil|petroleum|crude oil)[- ]?refiner(?:y|ies)\b|\brefiner(?:y|ies)\b|\bpetroleum refining\b'),
 ('refining process',r'\brefining (?:process(?:es)?|industry|sector|operations?)\b'),
 ('carbon footprint',r'\bcarbon footprint(?:s)?\b'),
 ('life cycle assessment',r'\blife[- ]cycle (?:assessment|analysis|ghg)\b|\blca\b'),
 ('machine learning',r'\bmachine[- ]learning\b|\bautoml\b'),
 ('deep learning',r'\bdeep[- ]learning\b|\bdeep neural\b'),
 ('artificial intelligence',r'\bartificial intelligence\b|\bai[- ](?:based|aided|driven|assisted)\b'),
 ('random forest',r'\brandom forest\b'),
 ('xgboost',r'\bxgboost\b'),
 ('neural network',r'\b(?:artificial |convolutional |graph )?neural network(?:s)?\b'),
 ('SHAP',r'\bshap\b|\bshapley\b'),
 ('LMDI',r'\blmdi\b'),
 ('emission inventory',r'\b(?:emissions?|carbon) inventor(?:y|ies)\b'),
 ('emission intensity',r'\b(?:carbon|co\s*2|ghg|emissions?) intensity\b'),
 ('energy efficiency',r'\benergy[- ]efficien(?:t|cy)\b'),
 ('energy consumption',r'\benergy consumption\b|\benergy use\b'),
 ('carbon capture',r'\bcarbon capture\b|\bco\s*2 capture\b|\bccus?\b'),
 ('hydrogen',r'\bhydrogen\b'),
 ('renewable energy',r'\brenewable energ(?:y|ies)\b'),
 ('decarbonization',r'\bdecarboni[sz](?:ation|e|ing)\b|\bdefossili[sz]ation\b'),
 ('carbon neutrality',r'\bcarbon neutral(?:ity)?\b|\bnet[- ]zero\b'),
 ('carbon accounting',r'\bcarbon account(?:ing)?\b|\bcarbon quantification\b'),
 ('carbon pricing',r'\bcarbon pric(?:es|ing)\b|\bcarbon tax(?:es)?\b|\bcarbon trading\b'),
 ('optimization',r'\boptimi[sz](?:ation|ing|ed|e|er|ers)\b'),
 ('prediction and forecasting',r'\bforecast(?:s|ing|ed)?\b|\bpredict(?:ion|ions|ive|ing|ed)?\b'),
 ('simulation',r'\bsimulation(?:s)?\b|\bsimulat(?:ed|ion|ing)\b'),
 ('modeling',r'\bmodell?ing\b|\bmodels?\b'),
 ('remote sensing',r'\bremote sensing\b|\bsatellite (?:monitoring|imagery|observations?)\b'),
 ('nighttime lights',r'\bnight[- ]?time lights?\b|\bnightlight\b|\bviirs\b|\bdmsp[/-]ols\b'),
 ('spatial analysis',r'\bspatial\b|\bgeographic\b|\bgeospatial\b'),
 ('temporal analysis',r'\btemporal\b|\btime[- ]series\b|\bspatio[- ]temporal\b'),
 ('scenario analysis',r'\bscenario(?:s)?\b|\bpathways?\b'),
 ('driver analysis',r'\bdriving (?:factors?|forces?)\b|\b(?:influencing|driving) factors?\b'),
 ('decomposition analysis',r'\bdecomposition\b'),
 ('uncertainty analysis',r'\buncertaint(?:y|ies)\b|\bsensitivity analysis\b'),
 ('petrochemical industry',r'\bpetrochemical\b|\bpetroleum industr(?:y|ies)\b'),
 ('biofuels',r'\bbiofuel(?:s)?\b|\bbiofeedstocks?\b|\bbiomass\b'),
 ('fluid catalytic cracking',r'\bfluid catalytic crack(?:ing|er)?\b|\bfcc\b'),
 ('electricity',r'\belectricity\b|\belectrical power\b'),
 ('steam',r'\bsteam\b'),
 ('China',r'\bchina\b|\bchinese\b'),
 ('global',r'\bglobal\b|\bworldwide\b'),
 ('supply chain',r'\bsupply chain\b'),
 ('economic analysis',r'\beconomic(?:s)?\b|\bcost[- ](?:benefit|effectiveness)\b'),
 ('政策与减排',r'碳排放|减排|政策|节能'),
 ('炼油行业',r'炼油|炼厂|炼化|石化|石油加工'),
 ('机器学习',r'机器学习|深度学习|人工智能|神经网络'),
 ('生命周期评价',r'生命周期|碳足迹'),
]


def load_rules(path=None):
    if path and Path(path).is_file():
        with Path(path).open(encoding='utf-8-sig',newline='') as f:
            data = list(csv.DictReader(f))
        return [(x['term'],x['pattern']) for x in data if x.get('term') and x.get('pattern')]
    return DEFAULT_RULES


def extract_terms(text: str, rules=None) -> list[str]:
    text = str(text or '')
    patterns = rules if rules is not None else DEFAULT_RULES
    return [name for name, pattern in patterns if re.search(pattern,text,flags=re.IGNORECASE)]
