from settings import WHITE,CYAN,MUTED,YELLOW,WIDTH,HEIGHT
from dialogue import INTRO

def draw_menu(g):
    s=g.surface;u=g.ui
    g.assets.draw_background(s,'menu')
    u.rect(s,(0,0,745,HEIGHT),(5,14,25),None,alpha=220,rad=0)
    u.text(s,'TRANSMISIÓN // LUNA',81,130,'small',MUTED)
    u.text(s,'LUNAR',74,195,'hero',WHITE)
    u.text(s,'OUTPOST',76,261,'hero',CYAN)
    u.text(s,'MISIÓN APOLO 5  ·  A.R.I.A. ONLINE',79,345,'medium',MUTED)
    u.button(s,'NUEVA PARTIDA',(79,405,520,68),'new',True)
    u.button(s,'CONTINUAR',(79,490,520,63),'continue',color=CYAN,disabled=not g.save_available())
    u.button(s,'CENTRO DE TELEMETRÍA',(79,566,520,58),'telemetry',color=YELLOW)
    u.button(s,'SALIR',(79,637,520,52),'quit')

def draw_intro(g):
    s=g.surface;u=g.ui
    if g.video_player.frame is not None:s.blit(g.video_player.frame,(0,0))
    else:g.assets.draw_background(s,'menu')
    u.shade(s,115)
    u.rect(s,(73,377,1128,268),(8,25,39),CYAN,alpha=240,rad=16,width=2)
    u.text(s,'PERSPECTIVA DEL ASTRONAUTA — COMUNICACIÓN ENTRANTE',101,396,'small',CYAN)
    n=min(len(INTRO),int(g.intro_time*35))
    u.lines(s,INTRO[:n],103,441,1025,'medium',WHITE,11,4)
    u.button(s,'INICIAR ENTRENAMIENTO',(745,565,425,58),'launch',True,disabled=n<len(INTRO))
    u.button(s,'VOLVER',(105,565,202,58),'back_menu')
