"""Comparison-ready corpus statistics, keyword rankings and longitudinal maps.

Explicitly distinguishes database keywords from controlled vocabulary terms
inferred from titles / abstracts. All counting is document-level full counting.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .analysis import build_keyword_network, prepare_records
from .report import write_report
from .term_extraction import extract_terms, load_rules
from .visualize import export_visuals, _configure_font

GROUPS = [
    ('Total literature', '01_Total_literature', '文献总库'),
    ('Carbon emissions', '02_Carbon_emissions', '碳排放相关'),
    ('Refinery carbon emissions', '03_Refinery_carbon_emissions', '炼油行业碳排放相关（自动标签）'),
    ('ML + carbon emissions', '04_ML_carbon_emissions', '机器学习与碳排放（自动标签）'),
    ('ML + refinery carbon emissions', '05_ML_refinery_carbon_emissions', '机器学习与炼油行业碳排放（自动标签）'),
]


def resolve_term_source(raw, choice='auto'):
    if choice != 'auto':
        return choice
    count = max(len(raw), 1)
    keywords = (raw['author_keywords'].fillna('').astype(str).str.strip().ne('') |
                raw['index_keywords'].fillna('').astype(str).str.strip().ne('')).sum()
    abstracts = raw['abstract'].fillna('').astype(str).str.strip().ne('').sum()
    if keywords / count >= 0.7:
        return 'bibliographic'
    if abstracts / count >= 0.7:
        return 'title_abstract'
    return 'title'


def prepare_with_terms(raw, mode, thesaurus, stopwords, rules_path=None):
    data = raw.copy()
    if mode in {'title', 'title_abstract'}:
        rules = load_rules(rules_path)
        texts = data['title'].fillna('').astype(str)
        if mode == 'title_abstract':
            texts = texts + ' ' + data['abstract'].fillna('').astype(str)
        data['extracted_terms'] = texts.map(lambda x: '; '.join(extract_terms(x,rules)))
        data['term_source'] = mode + '_inferred_controlled_terms'
    else:
        if not (data['author_keywords'].fillna('').astype(str).str.strip().ne('') |
                data['index_keywords'].fillna('').astype(str).str.strip().ne('')).any():
            raise ValueError('No supplied bibliographic keywords. Use --term-source title or title_abstract.')
        data['term_source'] = 'bibliographic_supplied'
    return prepare_records(data, thesaurus_path=thesaurus, stopwords_path=stopwords)


def keyword_frequency(records):
    counts = Counter(term for terms in records['keywords'] for term in set(terms))
    return pd.DataFrame([{'keyword': term, 'occurrences': count} for term,count in
        sorted(counts.items(), key=lambda t:(-t[1],t[0]))],columns=['keyword','occurrences'])


def year_term_counts(records):
    counts = Counter()
    for _, row in records.iterrows():
        yr = row.get('year_num')
        if pd.isna(yr): continue
        for term in set(row.get('keywords',[])):
            counts[(int(yr),term)] += 1
    return pd.DataFrame([{'year': year,'keyword': term,'documents': value} for (year,term), value in
        sorted(counts.items())], columns=['year','keyword','documents'])


def draw_timeline(records, frequencies, destination, dpi=600, n_terms=14):
    """Year-by-term heatmap (not a CiteSpace cluster timeline or burst metric)."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    _configure_font()
    top = frequencies.head(n_terms)['keyword'].tolist()
    years = sorted(set(int(x) for x in records['year_num'].dropna() if 1990 <= x <= 2100))
    if len(years)>25:
        years=years[-25:]
    arr=np.zeros((len(top),len(years)))
    year_index={y:i for i,y in enumerate(years)}
    term_index={t:i for i,t in enumerate(top)}
    for _,row in records.iterrows():
        yr=row.get('year_num')
        if pd.isna(yr) or int(yr) not in year_index: continue
        for t in set(row['keywords']):
            if t in term_index: arr[term_index[t],year_index[int(yr)]]+=1
    fig,ax=plt.subplots(figsize=(12.4,8.3))
    if arr.size:
        heat=ax.imshow(arr,aspect='auto',cmap='YlGnBu',interpolation='nearest')
        cbar=fig.colorbar(heat,ax=ax,label='Documents containing term',fraction=.032,pad=.012)
        cbar.ax.tick_params(labelsize=18)
        cbar.ax.yaxis.label.set_size(20)
        ax.set_yticks(range(len(top)),top,fontsize=18)
        step=max(1,len(years)//14)
        ax.set_xticks(range(0,len(years),step),[years[i] for i in range(0,len(years),step)],rotation=45,ha='right',fontsize=16)
        ax.set_xlim(-.5,len(years)-.5)
    else:
        ax.text(.5,.5,'No terms or years available',ha='center',va='center',transform=ax.transAxes,fontsize=18)
    ax.set_title('Annual distribution of high-frequency terms',fontsize=24,pad=10)
    ax.set_xlabel('Publication year',fontsize=18,labelpad=8)
    ax.set_ylabel('Research terms',fontsize=18,labelpad=12)
    fig.subplots_adjust(left=0.25,right=0.92,top=0.90,bottom=0.16)
    fig.savefig(destination,dpi=dpi,bbox_inches='tight',facecolor='white',pad_inches=0.08)
    fig.savefig(destination.with_suffix('.svg'),bbox_inches='tight',facecolor='white',pad_inches=0.08)
    fig.savefig(destination.with_suffix('.pdf'),bbox_inches='tight',facecolor='white',pad_inches=0.08)
    plt.close(fig)



def draw_cluster_timeline(records,nodes,destination,dpi=600):
    """Data-grounded cluster timeline, not CiteSpace's original cluster timeline."""
    destination=Path(destination)
    _configure_font()
    fig,ax=plt.subplots(figsize=(11.8,3.6))
    palette=['#E45B59','#438FC4','#36A56B','#C1B94F','#9470B7','#3CA6A1']
    long=year_term_counts(records)
    if len(nodes)==0 or len(long)==0:
        ax.text(.5,.5,'No cluster timeline data',ha='center',va='center',transform=ax.transAxes,fontsize=14)
    else:
        yrmax=int(long.year.max()); yrmin=max(2000,int(long.year.min()))
        long=long.loc[long['year']>=yrmin]
        if long.empty:
            ax.text(.5,.5,'No data after year 2000',ha='center',va='center',transform=ax.transAxes,fontsize=14)
        else:
            cids=sorted(nodes.cluster.astype(int).unique())
            n_clusters=len(cids)
            y_centers=np.linspace(n_clusters-1,0,n_clusters) * 0.78 + 0.58
            yticks=[]; ylabels=[]
            for j,cid in enumerate(cids):
                part=nodes.loc[nodes.cluster==cid].sort_values('occurrences',ascending=False)
                chosen=part.head(5).keyword.tolist()
                col=palette[j%len(palette)]
                y=float(y_centers[j])
                yticks.append(y)
                ylabels.append(f'#{cid} ' + ' / '.join(chosen[:2]))
                ax.hlines(y,yrmin,yrmax,linestyles='--',linewidth=1.4,color=col,alpha=.50)
                for k,term in enumerate(chosen):
                    series=long.loc[long.keyword==term].sort_values('year')
                    if series.empty:
                        continue
                    jitter=(k-2)*0.05
                    x=series.year.to_numpy(dtype=float)
                    n=series.documents.to_numpy(dtype=float)
                    yv=np.ones_like(x)*(y+jitter)
                    ax.plot(x,yv,color=col,alpha=.44,linewidth=1.1)
                    ax.scatter(x,yv,s=18+12*n,color=col,alpha=.86,edgecolors='white',linewidths=0.7,zorder=3)
            ax.set_yticks(yticks,ylabels,fontsize=12)
            ax.set_ylim(0.25, max(y_centers)+0.42)
            ax.set_xlim(yrmin-0.3, yrmax+0.25)
            ticks=list(range(yrmin, yrmax+1, 2))
            if ticks[-1] != yrmax:
                ticks.append(yrmax)
            ax.set_xticks(ticks)
            ax.grid(axis='x',alpha=.16)
            ax.set_xlabel('Publication year',fontsize=16,labelpad=4)
            ax.tick_params(axis='x',labelsize=10)
            for lbl in ax.get_xticklabels():
                lbl.set_rotation(45)
                lbl.set_ha('right')
            ax.set_title('High-frequency term timeline by detected cluster',fontsize=21,pad=6)
            fig.text(.5,.035,'Dots show document counts for representative cluster terms; group membership and time are algorithm-derived. Not CiteSpace native output.',
                     fontsize=8.5,color='#607078',ha='center')
    for spine in ['top','right','left']:
        ax.spines[spine].set_visible(False)
    fig.tight_layout(rect=(.03,.09,.985,.97), pad=0.25)
    fig.savefig(destination,dpi=dpi,bbox_inches='tight',facecolor='white',pad_inches=0.06)
    fig.savefig(destination.with_suffix('.svg'),bbox_inches='tight',facecolor='white',pad_inches=0.06)
    fig.savefig(destination.with_suffix('.pdf'),bbox_inches='tight',facecolor='white',pad_inches=0.06)
    plt.close(fig)


def draw_two_panel_keyword_overlay(panels, destination, dpi=600):
    """Create a two-panel overlay network figure resembling journal A/B panel layouts."""
    from .visualize import _configure_font, _layout, _node_size
    from matplotlib.collections import LineCollection
    from matplotlib.colors import to_rgba
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _configure_font()
    fig, axes = plt.subplots(2, 1, figsize=(13.0, 14.8), constrained_layout=False)
    cmap = plt.get_cmap('YlGnBu_r')
    letter_labels = ['A', 'B']
    fixed_vmin, fixed_vmax = 2016, 2026
    fixed_ticks = [2016, 2018, 2020, 2022, 2024, 2026]

    def edge_gradient(ax, p0, p2, c0, c1, width=1.15, alpha=0.38, index=0):
        p0=np.asarray(p0,dtype=float); p2=np.asarray(p2,dtype=float)
        delta=p2-p0
        dist=float(np.linalg.norm(delta))
        if dist < 1e-8:
            return
        normal=np.array([-delta[1], delta[0]])/dist
        bend=min(0.22,0.055*dist) * (1.0 if index % 2 == 0 else -1.0)
        control=(p0+p2)/2 + normal*bend
        t=np.linspace(0.0,1.0,26)
        curve=((1-t)[:,None]**2*p0 + 2*((1-t)*t)[:,None]*control + (t[:,None]**2)*p2)
        segs=np.stack([curve[:-1], curve[1:]], axis=1)
        cols=[]
        c0=np.array(c0); c1=np.array(c1)
        for s in np.linspace(0,1,len(segs)):
            c=(1-s)*c0 + s*c1
            cols.append((c[0], c[1], c[2], alpha))
        lc=LineCollection(segs, colors=cols, linewidths=width, zorder=1, capstyle='round', joinstyle='round')
        ax.add_collection(lc)

    for idx, panel in enumerate(panels[:2]):
        ax = axes[idx]
        ax.set_axis_off()
        ax.set_facecolor('white')
        graph = panel['graph']
        title = panel['title']
        if graph.number_of_nodes() == 0:
            ax.text(0.5,0.5,'No high-frequency terms',ha='center',va='center',transform=ax.transAxes,fontsize=16)
            continue
        pos = _layout(graph)
        max_occ = max(float(graph.nodes[n].get('occurrences', 1)) for n in graph.nodes)
        node_year = {}
        node_color = {}
        for n in graph.nodes:
            year = graph.nodes[n].get('avg_year')
            year = float(year) if year is not None else fixed_vmin
            year = min(max(year, fixed_vmin), fixed_vmax)
            node_year[n] = year
            node_color[n] = cmap((year-fixed_vmin)/max(fixed_vmax-fixed_vmin,1e-6))[:3]
        for i,(a,b,d) in enumerate(graph.edges(data=True)):
            edge_gradient(ax, pos[a], pos[b], node_color[a], node_color[b], width=1.25, alpha=0.42, index=i)
        order = sorted(graph.nodes, key=lambda n:(-float(graph.nodes[n].get('occurrences',0)),-float(graph.degree(n, weight='weight'))))
        for n in order:
            size = _node_size(graph.nodes[n].get('occurrences',1), max_occ) * 1.85
            ax.scatter([pos[n][0]],[pos[n][1]],s=size,color=node_color[n],alpha=0.97,edgecolors='white',linewidths=1.1,zorder=3)
            fontsize = 9.0 + 6.2 * (float(graph.nodes[n].get('occurrences',1))/max_occ)**0.65
            ax.text(pos[n][0],pos[n][1],str(n),ha='center',va='center',fontsize=fontsize,color='black',zorder=4)
        xy = np.array(list(pos.values()))
        low = xy.min(axis=0); high = xy.max(axis=0); span = np.maximum(high-low,1.0); margin = np.maximum(span*0.18,0.7)
        ax.set_xlim(low[0]-margin[0], high[0]+margin[0])
        ax.set_ylim(low[1]-margin[1], high[1]+margin[1])
        ax.set_aspect('equal', adjustable='box')
        ax.text(0.015, 0.985, letter_labels[idx], transform=ax.transAxes, va='top', ha='left', fontsize=28, fontweight='bold')
        ax.text(0.985, 0.082, title, transform=ax.transAxes, va='bottom', ha='right', fontsize=18)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=fixed_vmin, vmax=fixed_vmax))
        cax = ax.inset_axes([0.70, 0.035, 0.26, 0.030])
        cb = fig.colorbar(sm, cax=cax, orientation='horizontal', ticks=fixed_ticks)
        cb.ax.tick_params(labelsize=10, pad=1, length=2)
        cb.outline.set_visible(False)
    fig.subplots_adjust(left=0.05,right=0.985,top=0.985,bottom=0.035,hspace=0.08)
    fig.savefig(destination, dpi=dpi, bbox_inches='tight', facecolor='white', pad_inches=0.06)
    fig.savefig(destination.with_suffix('.svg'), bbox_inches='tight', facecolor='white', pad_inches=0.06)
    fig.savefig(destination.with_suffix('.pdf'), bbox_inches='tight', facecolor='white', pad_inches=0.06)
    plt.close(fig)


def _group_analyze(records,out,label,key,min_freq,args,mode):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    tables=out/'tables';tables.mkdir(exist_ok=True)
    freq=keyword_frequency(records)
    freq.to_csv(tables/'keyword_frequency_all.csv',index=False,encoding='utf-8-sig')
    filtered=freq.loc[freq['occurrences']>=min_freq]
    filtered.to_csv(tables/'high_frequency_keywords.csv',index=False,encoding='utf-8-sig')
    filtered.head(10).assign(rank=lambda d: range(1,len(d)+1)).to_csv(tables/'top10_keywords.csv',index=False,encoding='utf-8-sig')
    timeline=year_term_counts(records)
    timeline.to_csv(tables/'keyword_year_counts.csv',index=False,encoding='utf-8-sig')
    records[['record_id','title','year','keywords']].assign(keywords=lambda d:d['keywords'].map(lambda ts:'; '.join(ts))).to_csv(tables/'record_terms.csv',index=False,encoding='utf-8-sig')
    graph,nodes,edges=build_keyword_network(records,min_occurrences=min_freq,max_keywords=args.max_keywords)
    export_visuals(graph,nodes,out,max_labels=args.max_labels,dpi=args.dpi)
    cluster_rows=[]
    for cid, part in nodes.groupby('cluster') if len(nodes) else []:
        top=part.sort_values('occurrences',ascending=False).head(12)
        cluster_rows.append({'cluster':int(cid),'keyword_count':len(part),
                             'top_terms':'; '.join(top['keyword'].astype(str))})
    pd.DataFrame(cluster_rows,columns=['cluster','keyword_count','top_terms']).to_csv(tables/'cluster_summary.csv',index=False,encoding='utf-8-sig')
    draw_timeline(records,freq,out/'figures'/'keyword_timeline.png',dpi=args.dpi)
    draw_cluster_timeline(records,nodes,out/'figures'/'cluster_timeline.png',dpi=args.dpi)
    param={'min_occurrences':min_freq,'max_keywords':args.max_keywords,'max_labels':args.max_labels,'dpi':args.dpi,
           'term_source':mode,'theme_label':label,'community_detection':'NetworkX greedy modularity',
           'layout':'NetworkX ForceAtlas2 (spring fallback)','visualization_style':'journal-cluster'}
    write_report(records,nodes,edges,out/'reports'/'analysis_report.md',parameters=param)
    with (out/'reports'/'analysis_report.md').open('a',encoding='utf-8') as f:
        f.write('\n\n## 8. Source fidelity and timeline\n\n')
        f.write(f'- Group: **{label}**. These workbook flags are machine classifications, not manually validated inclusion decisions.\n')
        f.write(f'- Term source: **{mode}**. Title- or abstract-derived terms are NOT author keywords or database keywords.\n')
        f.write(f'- Frequency threshold: **{min_freq}**. High-frequency terms: **{len(filtered)}**.\n')
        f.write('- `keyword_timeline.png` is a document-count time heatmap, NOT a CiteSpace cluster timeline nor Kleinberg burst detection.\n')
        f.write('- `cluster_timeline.png` is an illustrative cluster-by-term/year visualization, not a native CiteSpace time-zone or burst algorithm.\n')
        f.write('- `keyword_year_counts.csv` contains the complete document counts by term and publication year.\n')
    valid=records['year_num'].dropna()
    return {'group':key,'label':label,'records':len(records),'years_valid':len(valid),'year_start':int(valid.min()) if len(valid) else None,
            'year_end':int(valid.max()) if len(valid) else None,'term_source':mode,
            'threshold':min_freq,'terms_all':len(freq),'terms_high_frequency':len(filtered),
            'clusters':int(nodes.cluster.nunique()) if len(nodes) else 0,
            'nodes':len(nodes),'edges':len(edges),'top10':filtered.head(10).to_dict('records')}


def run_comparative(raw,output_dir,args):
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    mode=resolve_term_source(raw,args.term_source)
    records=prepare_with_terms(raw,mode,args.thesaurus,args.stopwords,args.title_rules)
    # The 936-sheet categories are overlapping filters; this remains explicit in all outputs.
    groups=[(name,folder,label) for name,folder,label in GROUPS if name in records]
    if not groups: groups=[(None,'01_All_records','All records')]
    base_threshold=5 if str(args.min_occurrences)=='auto' else int(args.min_occurrences)
    stats=[]
    for name,folder,label in groups:
        subset=records.loc[records[name].astype(str).isin({'1','1.0','True'})].copy() if name else records.copy()
        if len(subset)==0:continue
        # Very small groups use 2 for exploratory maps; preserve main 5 threshold in metadata.
        threshold = min(base_threshold,2) if len(subset)<50 else base_threshold
        stats.append(_group_analyze(subset,output_dir/folder,label,name or 'All records',threshold,args,mode))
    rows=[{k:v for k,v in s.items() if k!='top10'} for s in stats]
    data_dir=output_dir/'comparison';data_dir.mkdir(exist_ok=True)
    year_rows=[]
    for _,rec in records.iterrows():
        yr=rec.get('year_num')
        if pd.isna(yr):continue
        for name,folder,label in groups:
            if name is None or str(rec.get(name,'')).strip() in {'1','1.0','True'}:
                year_rows.append({'year':int(yr),'group':name or 'All records','label':label})
    if year_rows:
        pd.DataFrame(year_rows).groupby(['year','group','label']).size().rename('documents').reset_index().to_csv(data_dir/'group_year_counts.csv',index=False,encoding='utf-8-sig')
    audit=[]
    for _,rec in records.iterrows():
        if str(rec.get('ML + refinery carbon emissions',0)) not in {'1','1.0','True'}:continue
        terms=set(rec.get('keywords',[]))
        no_refinery=not terms.intersection({'oil refinery','refining process','炼油行业','fluid catalytic cracking'})
        no_ml=not terms.intersection({'machine learning','deep learning','人工智能','机器学习','artificial intelligence','neural network','xgboost','SHAP'})
        if no_refinery or no_ml:
            audit.append({'id':rec['record_id'],'year':rec['year'],'title':rec['title'],'doi':rec.get('doi',''),
                'title_lacks_refinery_term':no_refinery,'title_lacks_ML_term':no_ml,
                'review_note':'Title evidence is insufficient; inspect abstract/full text before reclassifying.'})
    pd.DataFrame(audit,columns=['id','year','title','doi','title_lacks_refinery_term','title_lacks_ML_term','review_note']).to_csv(data_dir/'classification_review_queue.csv',index=False,encoding='utf-8-sig')
    coverage={key:int(records[key].fillna('').astype(str).str.strip().ne('').sum()) for key in ['title','year','abstract','author_keywords','index_keywords','doi']}
    (data_dir/'data_quality.json').write_text(json.dumps({'record_count':len(records),'field_coverage':coverage,
        'enrichment':raw.attrs.get('enrichment',{}),
        'potential_review_count_in_ML_refinery':len(audit)},ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(rows).to_csv(data_dir/'group_summary.csv',index=False,encoding='utf-8-sig')
    cmp=[]
    for stat in stats:
        for rank,term in enumerate(stat['top10'],start=1):
            cmp.append({'group':stat['group'],'rank':rank,'keyword':term['keyword'],'occurrences':term['occurrences'],'term_source':mode,'frequency_threshold':stat['threshold']})
    pd.DataFrame(cmp,columns=['group','rank','keyword','occurrences','term_source','frequency_threshold']).to_csv(data_dir/'top10_comparison_long.csv',index=False,encoding='utf-8-sig')
    # Publication-style A/B panel overlay figure for the two most relevant larger groups.
    panel_specs=[]
    preferred=['03_Refinery_carbon_emissions','04_ML_carbon_emissions','05_ML_refinery_carbon_emissions','02_Carbon_emissions']
    stat_map={s['group']:s for s in stats}
    by_folder={folder:name for name,folder,label in groups}
    for folder in preferred:
        if len(panel_specs)>=2: break
        name=by_folder.get(folder)
        if name is None or name not in stat_map: continue
        subset=records.loc[records[name].astype(str).isin({'1','1.0','True'})].copy()
        threshold=next((s['threshold'] for s in stats if s['group']==name), base_threshold)
        graph,nodes,_=build_keyword_network(subset,min_occurrences=threshold,max_keywords=args.max_keywords)
        label=next((s['label'] for s in stats if s['group']==name), folder.replace('_',' '))
        panel_specs.append({'graph':graph,'nodes':nodes,'title':label})
    if len(panel_specs)==2:
        draw_two_panel_keyword_overlay(panel_specs, data_dir/'two_panel_keyword_overlay.png', dpi=args.dpi)
    lines=['# SciMap-Agent | 五类主题文献高频术语对比','',
           f'> 研究术语来源：**{mode}**。标题/摘要自动抽取术语≠文献作者关键词。','',
           '> 五类标记由原始工作簿提供，存在交叉归类和潜在误判；以下不代表人工审查后的最终纳入研究。','',
           '| 主题 | 文献记录数 | 阈值 | 高频术语数 | 网络簇数 |', '|---|---:|---:|---:|---:|']
    for s in stats:
        lines.append(f"| {s['label']} | {s['records']} | {s['threshold']} | {s['terms_high_frequency']} | {s['clusters']} |")
    lines += ['','## 各组 Top 10','']
    for s in stats:
        lines += [f"### {s['label']} (N={s['records']}; 阈值≥{s['threshold']})",'', '| 排名 | 研究术语 | 含该术语的文献数 |','|---:|---|---:|']
        for i,row in enumerate(s['top10'],1):
            lines.append(f"| {i} | {row['keyword']} | {row['occurrences']} |")
        lines.append('')
    lines += ['## 方法学说明','',
        '1. 逐篇文献去重后，以一篇文献中是否含有某术语进行计数；同一术语在同篇记录出现多次，只计1次。',
        '2. 工作簿中没有作者关键词和摘要时，从标题使用公开词典与正则规则抽取受控主题术语；不能声称为数据库作者关键词共现。',
        '3. 正文统计阈值设为5；<50篇组为了生成探索性网络降低至2，须在论文中明确说明。',
        '4. 聚类使用NetworkX greedy modularity；时间线为逐年共现术语热力图，非CiteSpace原生时间线或突现分析。',
        '5. 分类结果由上传工作簿给定；应检查边界文献及期刊/会议/政策文件类型，2026年为不完整年度。',
    ]
    (data_dir/'comparison_report_zh.md').write_text('\n'.join(lines),encoding='utf-8')
    (data_dir/'summary.json').write_text(json.dumps({'term_source':mode,'main_threshold':base_threshold,'groups':stats},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Comparative analysis complete: {len(stats)} groups; term source: {mode}')
    print('Comparison report:',data_dir/'comparison_report_zh.md')
    return stats


def enrich_records_with_metadata(master, supplement):
    """Fill missing abstract/keyword fields from matched bibliographic exports.

    Match DOI first; otherwise normalized exact title. Never alter primary IDs,
    classification flags, dates or already populated master bibliographic values.
    """
    import re
    def doi_key(x):
        return re.sub(r'^https?://(?:dx\.)?doi\.org/', '',str(x or '').casefold().strip())
    def title_key(x):
        return re.sub(r'[^\w]+','',str(x or '').casefold().strip())
    doi_map={};title_map={}
    for _,r in supplement.iterrows():
        d=doi_key(r.get('doi'));t=title_key(r.get('title'))
        if d:doi_map.setdefault(d,[]).append(r)
        if t:title_map.setdefault(t,[]).append(r)
    matched=0; enriched_abs=0; enriched_kw=0
    out=master.copy()
    for idx,row in out.iterrows():
        d=doi_key(row.get('doi'));t=title_key(row.get('title'))
        candidates=(doi_map.get(d) if d and d in doi_map else title_map.get(t,[])) or []
        if not candidates:continue
        matched+=1
        for field in ('abstract','author_keywords','index_keywords'):
            if str(row.get(field,'') or '').strip():continue
            replacement=next((str(r.get(field) or '').strip() for r in candidates if str(r.get(field) or '').strip()),'')
            if replacement:
                out.at[idx,field]=replacement
                if field=='abstract':enriched_abs+=1
                else: enriched_kw+=1
    out.attrs['enrichment']={'matched_records':matched,'abstracts_filled':enriched_abs,'keyword_fields_filled':enriched_kw}
    return out
