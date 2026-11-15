from settings import *
ROOM_X={'life':220,'generator':492,'radiation':760,'hydro':1036}

def draw(g):
    s=g.surface;u=g.ui;p=g.pg
    g.assets.draw_background(s,'hub')
    u.shade(s,50)
    # Four accessible corridors; actual collision and activation use the player's x coordinate.
    for room,x in ROOM_X.items():
        operational=g.state.operational[room]
        col=GREEN if operational else CYAN
        u.rect(s,(x-101,310,201,152),(8,29,43),col,alpha=223,rad=12,width=2)
        u.text(s,ROOM_TITLES[room],x,330,'small',WHITE,'center')
        p.draw.circle(s,col,(x,395),26,3)
        u.text(s,'✓' if operational else '!',x,380,'medium',col,'center')
        u.text(s,'OPERATIVO' if operational else 'REQUIERE REPARACIÓN',x,434,'tiny',col,'center')
        if g.player.near(x,92):
            u.text(s,'[E] ENTRAR AL MÓDULO',x,290,'small',YELLOW,'center')
        u.actions.append((p.Rect(x-101,310,201,152),f'enter:{room}'))
    p.draw.rect(s,(25,42,53),(0,545,WIDTH,32))
    g.assets.draw_astronaut(s,g.player)
    u.header(s,g.state,'CENTRO DE OPERACIONES')
    u.rect(s,(32,160,610,94),(6,22,33),EDGE,alpha=228)
    u.text(s,'MISIÓN: MANTENER LA COLONIA HASTA EL SOL 30',49,175,'small',WHITE)
    u.lines(s,'Entra en cada módulo, repara los fallos y administra los cuatro recursos.',49,205,575,'small',MUTED,max_lines=2)
    u.button(s,'AVANZAR UN SOL',(926,478,319,57),'advance',True)
    u.aria(s,g.message,g.notice,'T = TELEMETRÍA')
