from settings import *
from interactables import room_hotspots

def draw(g,room):
    s=g.surface;p=g.pg;u=g.ui;state=g.state
    prog=state.progress[room]
    g.assets.draw_background(s,room)
    # A collision platform appears in the shield room. This is a new foreground object.
    if room=='radiation':
        p.draw.rect(s,(61,70,95),(346,474,572,19),border_radius=4)
        p.draw.rect(s,PURPLE,(346,474,572,4))
    p.draw.rect(s,(22,35,44),(0,545,WIDTH,32))
    if room=='life':
        for i,x in enumerate((427,618,811)):
            col=GREEN if prog['fissures'][i] else RED
            p.draw.line(s,col,(x-13,390),(x+13,427),6)
            if not prog['fissures'][i]:
                p.draw.line(s,col,(x+5,389),(x-12,410),4)
        if prog['tool']:
            u.text(s,'SELLADOR EQUIPADO',32,205,'small',GREEN)
    if room=='generator':
        u.text(s,f'INVERSOR · ETAPA {min(4,prog["stage"]+1)}/4',33,206,'small',GREEN if prog['stage']>=3 else YELLOW)
        if prog['stage']>=3:
            u.text(s,'CIRCUITO RESTABLECIDO',504,272,'medium',GREEN)
    if room=='radiation':
        t=max(0,round(prog['storm_clock']))
        u.rect(s,(945,169,291,70),(40,22,39),RED,alpha=236)
        u.text(s,'IMPACTO SOLAR SIMULADO',960,177,'tiny',WHITE)
        u.text(s,f'{t} s',959,198,'title',RED)
        u.text(s,'SUBE A LA PLATAFORMA',390,270,'small',YELLOW)
        for i,x in enumerate((418,644,872)):
            col=GREEN if prog['coils'][i]==prog['targets'][i] else PURPLE
            p.draw.rect(s,(20,25,55),(x-44,327,88,64),border_radius=8)
            p.draw.rect(s,col,(x-44,327,88,64),2,border_radius=8)
            u.text(s,f'{prog["coils"][i]} / {prog["targets"][i]}',x,342,'normal',col,'center')
    if room=='hydro':
        if prog['tool'] and prog['heat']<3:
            u.text(s,'MANTÉN F JUNTO A LA TUBERÍA',411,298,'small',YELLOW)
            p.draw.rect(s,(31,56,69),(418,335,433,15),border_radius=7)
            p.draw.rect(s,CYAN,(418,335,round(433*prog['heat']/3),15),border_radius=7)
        if prog['heat']>=3:u.text(s,'AGUA RESTABLECIDA',446,297,'medium',GREEN)
    g.assets.draw_astronaut(s,g.player)
    u.header(s,state,ROOM_TITLES[room])
    for item in room_hotspots(state,room):
        near=g.player.near(item.x,94) and (not item.platform or g.player.on_platform)
        u.marker(s,item,near,g.elapsed)
    if state.operational[room]:
        u.text(s,'● SISTEMA OPERATIVO',900,180,'medium',GREEN)
    u.aria(s,g.message,g.notice,'ESC = PAUSA / SALIR')
