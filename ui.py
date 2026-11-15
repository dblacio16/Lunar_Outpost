"""Reusable Pygame pixel-style HUD, action buttons, subtitles and panels."""
from __future__ import annotations
from settings import *

class UI:
    def __init__(self,pygame):
        self.pg=pygame
        pygame.font.init()
        self.fonts={
          'tiny':pygame.font.SysFont('dejavusans',12),
          'small':pygame.font.SysFont('dejavusans',15),
          'normal':pygame.font.SysFont('dejavusans',18),
          'medium':pygame.font.SysFont('dejavusans',21,bold=True),
          'title':pygame.font.SysFont('dejavusans',31,bold=True),
          'hero':pygame.font.SysFont('dejavusans',56,bold=True),
        }
        self.actions=[]
        self.cursor=(0,0)

    def reset(self,mouse):
        self.actions=[]
        self.cursor=mouse

    def rect(self,surface,box,fill=PANEL,border=EDGE,alpha=255,rad=10,width=1):
        p=self.pg
        r=p.Rect(box)
        if alpha==255:
            p.draw.rect(surface,fill,r,border_radius=rad)
        else:
            layer=p.Surface(r.size,p.SRCALPHA)
            p.draw.rect(layer,(*fill,alpha),(0,0,r.w,r.h),border_radius=rad)
            surface.blit(layer,r.topleft)
        if border:
            p.draw.rect(surface,border,r,width,border_radius=rad)

    def text(self,surface,message,x,y,kind='normal',color=WHITE,align='left'):
        message=str(message)
        img=self.fonts[kind].render(message,True,color)
        if align=='center':x-=img.get_width()/2
        if align=='right':x-=img.get_width()
        surface.blit(img,(int(x),int(y)))
        return img.get_width()

    def lines(self,surface,message,x,y,width=700,kind='normal',color=WHITE,spacing=4,max_lines=6):
        font=self.fonts[kind];text=str(message)
        arr=[]
        for original in text.split('\n'):
            row=''
            for word in original.split():
                test=(row+' '+word).strip()
                if font.size(test)[0]<=width:
                    row=test
                else:
                    if row:arr.append(row)
                    row=word
            arr.append(row)
        for i,line in enumerate(arr[:max_lines]):
            self.text(surface,line,x,y+i*(font.get_linesize()+spacing),kind,color)
        return min(len(arr),max_lines)*(font.get_linesize()+spacing)

    def button(self,surface,text,box,action,primary=False,color=CYAN,disabled=False):
        p=self.pg;r=p.Rect(box)
        hover=r.collidepoint(self.cursor)
        fill=(27,72,92) if primary else (17,34,49)
        if hover and not disabled: fill=(39,86,107)
        self.rect(surface,r,fill,(76,94,105) if disabled else color if primary or hover else EDGE,rad=8,width=2 if hover else 1)
        if primary:p.draw.rect(surface,color,(r.x,r.y,5,r.h),border_radius=2)
        self.text(surface,text,r.centerx,r.centery-12,'medium' if r.h>=56 else 'normal',MUTED if disabled else WHITE,'center')
        if action is not None and not disabled:self.actions.append((r,action))

    def shade(self,surface,alpha=170):
        layer=self.pg.Surface((WIDTH,HEIGHT),self.pg.SRCALPHA)
        layer.fill((2,9,17,alpha))
        surface.blit(layer,(0,0))

    def header(self,surface,state,scene=''):
        p=self.pg
        p.draw.rect(surface,(3,15,25),(0,0,WIDTH,99))
        p.draw.line(surface,EDGE,(0,98),(WIDTH,98),2)
        self.text(surface,'LUNAR',24,22,'medium',WHITE)
        self.text(surface,'OUTPOST',25,48,'medium',CYAN)
        self.text(surface,'A.R.I.A. / NASA',25,77,'tiny',MUTED)
        data=[('life',CYAN),('energy',YELLOW),('food',GREEN),('integrity',PURPLE)]
        for index,(key,col) in enumerate(data):
            x=220+index*214
            val=round(state.resources[key])
            self.text(surface,RESOURCE_NAMES[key],x,21,'tiny',MUTED)
            self.text(surface,f'{val}%',x+170,15,'medium',col if val>25 else RED,'right')
            p.draw.rect(surface,(39,60,75),(x,62,174,14),border_radius=6)
            if val:p.draw.rect(surface,col if val>25 else RED,(x,62,round(174*val/100),14),border_radius=6)
        self.text(surface,'SOL ACTUAL',1110,18,'tiny',MUTED)
        self.text(surface,f'{state.sol} / 30',1110,43,'title',WHITE)
        if scene:
            self.text(surface,scene,33,112,'title',WHITE)

    def aria(self,surface,message,notice='',context=''):
        p=self.pg
        self.rect(surface,(0,579,WIDTH,141),(5,19,29),CYAN,alpha=235,rad=0,width=1)
        p.draw.circle(surface,CYAN,(43,626),25,3)
        self.text(surface,'AI',43,615,'medium',CYAN,'center')
        self.text(surface,'A.R.I.A. // COMUNICACIÓN',85,595,'tiny',CYAN)
        self.lines(surface,message,85,618,960,'normal',WHITE,5,3)
        if context:self.text(surface,context,1256,591,'tiny',GREEN,'right')
        self.text(surface,'A/D: MOVER   ESPACIO: SALTAR   E: INTERACTUAR   F: HERRAMIENTA   TAB: OBJETIVOS   T: NASA   ESC: PAUSA',86,693,'tiny',MUTED)
        if notice:
            self.rect(surface,(240,533,800,38),(23,46,60),YELLOW,alpha=255,rad=6,width=1)
            self.text(surface,notice,640,542,'small',WHITE,'center')

    def marker(self,surface,spot,near=False,progress=0.0):
        p=self.pg
        col=GREEN if near else CYAN
        cx,cy=spot.x,spot.y
        pulse=3*__import__('math').sin(progress*5)
        p.draw.circle(surface,col,(cx,cy),int(16+pulse),2)
        p.draw.circle(surface,col,(cx,cy),5)
        width=min(278,max(145,self.fonts['tiny'].size(spot.label)[0]+27))
        x=min(WIDTH-width-8,max(8,cx-width//2))
        self.rect(surface,(x,cy+21,width,30),(5,17,28),col if near else EDGE,alpha=235,rad=4)
        self.text(surface,spot.label,x+width/2,cy+27,'tiny',WHITE,'center')
        if near:self.text(surface,'E',cx,cy-31,'medium',YELLOW,'center')
