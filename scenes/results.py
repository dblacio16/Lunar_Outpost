from settings import *

def draw(g):
    s=g.surface;u=g.ui
    g.assets.draw_background(s,'menu')
    u.shade(s,190)
    won=g.state.won
    accent=GREEN if won else RED
    u.rect(s,(210,139,860,494),(9,24,36),accent,alpha=242,rad=18,width=2)
    u.text(s,'MISIÓN COMPLETADA' if won else 'MISIÓN FRACASADA',640,185,'title',accent,'center')
    u.lines(s,g.state.reason,270,271,750,'medium',WHITE,max_lines=4)
    u.text(s,f'SOL ALCANZADO: {g.state.sol} / 30',270,374,'medium',WHITE)
    u.text(s,f'MÓDULOS OPERATIVOS: {sum(g.state.operational.values())} / 4',270,413,'medium',WHITE)
    u.text(s,f'DECISIONES REGISTRADAS: {len(g.state.choices)}',270,451,'normal',MUTED)
    u.button(s,'NUEVA MISIÓN',(272,523,346,70),'new',True)
    u.button(s,'MENÚ PRINCIPAL',(649,523,344,70),'back_menu')
