"""NASA event interpretation; NEVER presents fictional colony numbers as NASA measurements."""
from __future__ import annotations


def safe_float(x):
    try:return float(x)
    except (ValueError,TypeError):return None


def flare_weight(class_type):
    if not isinstance(class_type,str) or not class_type:return 0.0
    strength={'A':0,'B':1,'C':2.5,'M':10,'X':24}.get(class_type[0].upper(),0)
    factor=safe_float(class_type[1:])
    if factor is None:factor=1.0
    return min(38,strength*min(8,max(.2,factor))**.55)


def sample_info(kind,record):
    """Real field summaries extracted from DONKI when available."""
    if not isinstance(record,dict):return {'type':kind, 'id':'', 'date':'', 'detail':'sin datos'}
    date_keys={'FLR':'beginTime','GST':'startTime','SEP':'eventTime','CME':'startTime'}
    id_keys={'FLR':'flrID','GST':'gstID','SEP':'sepID','CME':'activityID'}
    detail='evento registrado'
    if kind=='FLR':detail=f"Clase {record.get('classType') or 'sin clasificar'}"
    if kind=='GST':
        vals=[safe_float(item.get('kpIndex')) for item in (record.get('allKpIndex') or []) if isinstance(item,dict)]
        valid=[v for v in vals if v is not None]
        detail=f"Kp {max(valid):g}" if valid else 'Kp no disponible'
    if kind=='CME':
        analyses=record.get('cmeAnalyses') or []
        speeds=[safe_float(a.get('speed')) for a in analyses if isinstance(a,dict)]
        valid=[v for v in speeds if v is not None]
        detail=f"Vel. {max(valid):.0f} km/s" if valid else 'Velocidad no disponible'
    if kind=='SEP':detail='Evento de partículas solares'
    return {'type':kind,'id':str(record.get(id_keys[kind]) or ''),
            'date':str(record.get(date_keys[kind]) or ''),'detail':detail}


def calculate_risk(events):
    """Illustrative 0..100 educational score, not a NASA operational metric.

    Based on 7-day DONKI lists and reported severity when present.
    No authentic event is altered. Empty list = low rather than fabricated risk.
    """
    if not isinstance(events,dict):return 15
    flares=[f for f in events.get('FLR',[]) if isinstance(f,dict)]
    storms=[s for s in events.get('GST',[]) if isinstance(s,dict)]
    sep=[s for s in events.get('SEP',[]) if isinstance(s,dict)]
    cmes=[c for c in events.get('CME',[]) if isinstance(c,dict)]
    flare=max([flare_weight(f.get('classType')) for f in flares]+[0])
    kp_max=0
    for st in storms:
        indices=[safe_float(i.get('kpIndex')) for i in (st.get('allKpIndex') or []) if isinstance(i,dict)]
        kp_max=max(kp_max,*[x for x in indices if x is not None],0)
    kp=min(24,max(0,(kp_max-3)*4))
    speeds=[]
    for event in cmes:
        for analysis in (event.get('cmeAnalyses') or []):
            if isinstance(analysis,dict):
                speed=safe_float(analysis.get('speed'))
                if speed is not None:speeds.append(speed)
    cme_score=min(15,max(0,(max(speeds or [350])-350)/95))
    particle_score=min(30, 16*len(sep))
    # Add a smaller frequency component so quiet weather stays quiet.
    occurrence=min(10,len(flares)*.5+len(cmes)*.75)
    return round(max(0,min(100,flare+kp+particle_score+cme_score+occurrence)))


def snapshot_summary(snapshot):
    entries=snapshot.get('events',{}) if isinstance(snapshot,dict) else {}
    info=[]
    for kind in ('FLR','SEP','GST','CME'):
        records=entries.get(kind,[]) if isinstance(entries,dict) else []
        for record in records[-2:]:
            info.append(sample_info(kind,record))
    info.sort(key=lambda d:d['date'],reverse=True)
    return info[:6]
