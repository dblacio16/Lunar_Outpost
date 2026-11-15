from settings import *
from nasa_simulation import snapshot_summary

def draw(g):
    s=g.surface;u=g.ui
    g.assets.draw_background(s,'hub')
    u.shade(s,210)
    snap=g.telemetry_snapshot()
    events=snap.get('events',{})
    status=snap.get('mode','offline')
    name={'online':'NASA ONLINE','cache':'DATOS EN CACHÉ','offline':'SIMULACIÓN SIN CONEXIÓN'}.get(status,'NO DISPONIBLE')
    col={'online':GREEN,'cache':YELLOW,'offline':RED}.get(status,RED)
    u.rect(s,(68,86,1146,572),(9,27,41),CYAN,alpha=247,rad=17,width=2)
    u.text(s,'CENTRO DE TELEMETRÍA ESPACIAL',97,114,'title',WHITE)
    u.text(s,name,1099,126,'medium',col,'right')
    u.text(s,'FUENTE: NASA DONKI · Observaciones registradas (no simuladas)',98,169,'small',MUTED)
    u.text(s,'Fecha UTC: '+(snap.get('fetched_at') or 'No disponible')[:19],98,194,'small',WHITE)
    u.text(s,f'Intervalo: {snap.get("start") or "—"} a {snap.get("end") or "—"}',98,222,'small',MUTED)
    counts='   '.join(f'{key}: {len(events.get(key,[]))}' for key in ('FLR','SEP','GST','CME'))
    u.text(s,counts,98,258,'medium',CYAN)
    u.rect(s,(91,300,730,271),(7,20,34),EDGE,rad=10)
    info=snapshot_summary(snap)
    if not info:
        u.text(s,'Sin eventos disponibles en esta consulta.',119,334,'normal',MUTED)
    for i,item in enumerate(info[:5]):
        txt=f"{item['type']} | {item['date'][:16] or 'sin fecha'} | {item['detail']}"
        u.text(s,txt[:91],110,322+i*47,'small',WHITE)
    u.rect(s,(848,300,321,271),(24,44,63),PURPLE,rad=10)
    u.text(s,'SIMULACIÓN EDUCATIVA',864,321,'small',YELLOW)
    risk=g.state.risk if g.state else g.preview_risk
    u.text(s,f'Riesgo: {risk}/100',867,366,'title',WHITE)
    u.lines(s,'Índice propio del juego, NO una escala oficial NASA ni dosis de radiación lunar.',867,423,271,'small',MUTED,max_lines=5)
    if snap.get('error'):u.lines(s,snap['error'],101,584,705,'small',YELLOW,max_lines=2)
    u.button(s,'ACTUALIZAR NASA',(851,583,318,55),'refresh_nasa',True)
    u.button(s,'VOLVER',(96,582,234,55),'telemetry_back')
