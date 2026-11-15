"""Lunar Outpost V1.0: main Pygame loop, transitions and actual player interactions."""
from __future__ import annotations
import json
import math
import sys

import pygame

from settings import *
from assets_loader import AssetManager
from video_player import IntroVideo
from dialogue import INTRO,INITIAL,SECOND,instruction
from game_state import GameState,ALLOCATION_MINIMUM
from nasa_api import NasaWorker,offline_snapshot,read_cache
from nasa_simulation import calculate_risk
from event_manager import pick_event,resolve_event
from interactables import room_hotspots
from player import Player
from ui import UI
from scenes import menu,hub,rooms,telemetry,results


class Game:
    def __init__(self):
        pygame.init()
        self.pg=pygame
        pygame.display.set_caption('Lunar Outpost V1.0 - A.R.I.A. / Misión Apolo 5')
        self.window=pygame.display.set_mode((WIDTH,HEIGHT),pygame.RESIZABLE)
        self.surface=pygame.Surface((WIDTH,HEIGHT)).convert()
        self.clock=pygame.time.Clock()
        self.ui=UI(pygame)
        self.assets=AssetManager(pygame)
        self.video_player=IntroVideo(pygame)
        self.worker=NasaWorker()
        self.state=None
        self.mode='menu'
        self.modal=None
        self.message='A.R.I.A. conectada. Bienvenido al puesto lunar.'
        self.notice=''
        self.notice_time=0.0
        self.intro_time=0.0
        self.elapsed=0.0
        self.prev_mode='menu'
        self.loading_for_new=False
        self.start_time=0
        self.preview_snapshot=read_cache() or offline_snapshot('Todavía no se consultó NASA.')
        self.preview_risk=calculate_risk(self.preview_snapshot.get('events',{}))
        self.player=Player()
        self.drag_slider=None
        self.last_room=None
        self.alive=True

    def save_available(self):return SAVE_FILE.is_file()

    def telemetry_snapshot(self):
        if self.state is not None:return self.state.science
        return self.preview_snapshot

    def show_notice(self,message):
        self.notice=str(message)[:130]
        self.notice_time=3.8

    def save(self):
        if self.state is None:return
        self.state.current_scene=self.mode if self.mode in ROOMS or self.mode=='hub' else 'hub'
        self.state.player_x=self.player.x
        try:self.state.save(SAVE_FILE)
        except (OSError,ValueError) as exc:self.show_notice(f'No se pudo guardar: {exc}')

    def load(self):
        try:
            loaded=GameState.load(SAVE_FILE)
            self.state=loaded
            self.mode='results' if loaded.won or loaded.lost else (loaded.current_scene if loaded.current_scene in ROOMS else 'hub')
            self.player.reset(loaded.player_x)
            self.modal='event' if loaded.pending_event else None
            self.message='A.R.I.A.: partida restaurada. '+(instruction(loaded,self.mode) if self.mode in ROOMS else 'Continúa administrando la colonia.')
        except (OSError,ValueError,TypeError,KeyError) as exc:
            self.show_notice(f'No se pudo cargar la partida: {exc}')

    def new_intro(self):
        self.state=None
        self.intro_time=0.0
        self.mode='intro'
        self.modal=None
        self.message=INTRO

    def begin_loading(self):
        self.mode='loading'
        self.start_time=self.elapsed
        self.loading_for_new=True
        self.worker.start(force=False)

    def use_snapshot(self,snapshot):
        self.preview_snapshot=snapshot
        self.preview_risk=calculate_risk(snapshot.get('events',{}))
        if not self.loading_for_new:return
        self.loading_for_new=False
        self.state=GameState.fresh(snapshot,self.preview_risk)
        self.mode='hub'
        self.modal=None
        self.player.reset(100)
        self.message='A.R.I.A.: misión iniciada. Repara los cuatro sistemas y protege la colonia durante 30 soles.'
        self.save()

    def refresh_nasa(self):
        if self.worker.start(force=True):self.show_notice('Actualizando observaciones NASA sin bloquear el juego...')
        else:self.show_notice('Ya hay una consulta en curso.')

    def to_telemetry(self):
        self.prev_mode=self.mode
        self.mode='telemetry'
        self.modal=None

    def enter_room(self,room):
        if room not in ROOMS or self.state is None:return
        self.mode=room
        self.player.reset(105)
        self.modal=None
        self.message=instruction(self.state,room)
        self.state.current_scene=room
        self.save()

    def back_to_hub(self):
        if self.state is None:
            self.mode='menu';return
        self.mode='hub'
        self.player.reset(91)
        self.message='A.R.I.A.: la base requiere mantenimiento. Completa los cuatro sistemas.'
        self.modal=None
        self.state.current_scene='hub'
        self.save()

    def complete_room(self,room):
        self.state.repair(room)
        self.message='A.R.I.A.: sistema restablecido. Trabajo completado; puedes volver a la base.'
        self.show_notice(f'{ROOM_TITLES[room]}: REPARACIÓN COMPLETADA')
        self.save()

    def handle_action(self,action):
        if action=='quit':self.alive=False
        elif action=='new':self.new_intro()
        elif action=='continue':self.load()
        elif action=='launch':
            if self.intro_time>=len(INTRO)/35:self.begin_loading()
            else:self.intro_time=len(INTRO)/35
        elif action=='back_menu':
            self.mode='menu';self.modal=None
        elif action=='skip_nasa':
            if self.loading_for_new:
                self.use_snapshot(offline_snapshot('Inicio sin conexión elegido por el jugador.'))
        elif action=='telemetry':self.to_telemetry()
        elif action=='telemetry_back':
            self.mode=self.prev_mode
            if self.mode not in ('menu','hub')+ROOMS:self.mode='menu'
        elif action=='refresh_nasa':self.refresh_nasa()
        elif action.startswith('enter:'):
            room=action.split(':',1)[1]
            x=hub.ROOM_X.get(room,0)
            if self.player.near(x,95):self.enter_room(room)
            else:self.show_notice('Acerca al astronauta a la puerta. Usa A y D para caminar.')
        elif action=='advance':self.advance_sol()
        elif action=='pause_resume':self.modal=None
        elif action=='pause_save':self.save();self.show_notice('Partida guardada.');self.modal=None
        elif action=='pause_hub':self.back_to_hub()
        elif action=='pause_menu':self.save();self.modal=None;self.mode='menu'
        elif action=='objectives_close':self.modal=None
        elif action=='valve_turn':
            if self.mode=='life' and self.modal=='valve':
                self.state.progress['life']['valve']+=1
                if self.state.progress['life']['valve']>=3:
                    self.modal=None
                    self.complete_room('life')
        elif action.startswith('uv_') and self.mode=='hydro' and self.modal=='uv':
            i=int(action[-1]);p=self.state.progress['hydro']
            p['lamps'][i]=not p['lamps'][i]
            if all(p['lamps']):
                self.state.adjust(energy=-4)
                self.modal=None
                if not self.state.lost:self.complete_room('hydro')
        elif action=='grid_apply' and self.mode=='generator' and self.modal=='grid':
            if self.state.configure_allocation(self.state.allocation):
                self.state.progress['generator']['configured']=True
                self.modal=None
                self.complete_room('generator')
            else:self.show_notice('Asignación insuficiente. Mínimos: 30W vida, 25W cultivos, 20W escudos.')
        elif action=='grid_cancel':self.modal=None
        elif action.startswith('choose_') and self.modal=='event':
            i=int(action[-1])
            resolve_event(self.state,i)
            self.modal=None
            self.save()
            self.message='A.R.I.A.: decisión aplicada. Sus efectos continúan en la colonia.'
            self.sync_end_state()
        elif action=='next_menu':self.save();self.mode='menu';self.modal=None

    def sync_end_state(self):
        if self.state is None:return
        self.state.check_end()
        if self.state.won or self.state.lost:
            self.mode='results'
            self.modal=None
            self.save()

    def advance_sol(self):
        if self.state is None or self.state.pending_event:
            return
        was=self.state.sol
        if not self.state.advance_sol():return
        if self.state.lost:
            self.sync_end_state();return
        # No new event on the victory sol: successful bases may finish fairly.
        if self.state.sol<30:
            event=pick_event(self.state)
            if event:
                self.state.pending_event=event
                self.modal='event'
                self.message='A.R.I.A.: nueva emergencia detectada. Elige cómo responder.'
        elif not all(self.state.operational.values()):
            self.show_notice('Sol 30 alcanzado: vuelve a reparar los módulos pendientes para ganar.')
        self.save()
        self.sync_end_state()
        if not self.modal and self.mode!='results':self.show_notice(f'Sol {self.state.sol} / 30: balance de recursos actualizado.')

    def interact(self):
        if self.mode not in ROOMS or self.state is None or self.state.operational[self.mode]:return
        hotspots=room_hotspots(self.state,self.mode)
        valid=[h for h in hotspots if self.player.near(h.x,90)]
        if not valid:
            self.show_notice('Acércate al marcador para interactuar.')
            return
        hit=min(valid,key=lambda h:abs(h.x-self.player.x))
        if hit.platform and not self.player.on_platform:
            self.show_notice('Salta a la plataforma del emisor para ajustar esta bobina.')
            return
        self.player.interact_pulse=.23
        self.use_hotspot(hit.key)

    def use_hotspot(self,key):
        s=self.state
        if self.mode=='life':
            p=s.progress['life']
            if key=='get_sealant':
                p['tool']=True
                if 'sellador' not in s.inventory:s.inventory.append('sellador')
                self.show_notice('Sellador térmico recogido. Busca las tres fisuras.')
            elif key.startswith('fissure_') and p['tool']:
                i=int(key.split('_')[-1]);p['fissures'][i]=True
                s.adjust(energy=-.5)
                self.show_notice(f'Fisura {i+1} reparada: {sum(p["fissures"])} / 3.')
            elif key=='purge' and all(p['fissures']):self.modal='valve'
        elif self.mode=='generator':
            p=s.progress['generator']
            if key=='remove_fuse' and p['stage']==0:
                p['stage']=1;self.show_notice('Fusible retirado. Encuentra el puente de repuesto.')
            elif key=='get_bridge' and p['stage']==1:
                p['stage']=2;s.inventory.append('puente');self.show_notice('Puente recogido. Vuelve al inversor.')
            elif key=='install_bridge' and p['stage']==2:
                p['stage']=3
                if 'puente' in s.inventory:s.inventory.remove('puente')
                self.show_notice('Circuito reactivado. Configura el reparto eléctrico.')
            elif key=='grid_console' and p['stage']==3:self.modal='grid'
        elif self.mode=='radiation':
            p=s.progress['radiation']
            if key.startswith('coil_'):
                i=int(key.split('_')[-1]);p['coils'][i]=1+p['coils'][i]%5
                if p['coils']==p['targets']:
                    self.show_notice('Tres bobinas sincronizadas. Activa el interruptor.')
            elif key=='shield_switch' and p['coils']==p['targets']:
                self.complete_room('radiation')
        elif self.mode=='hydro':
            p=s.progress['hydro']
            if key=='get_heater':
                p['tool']=True
                if 'calentador' not in s.inventory:s.inventory.append('calentador')
                self.show_notice('Calentador equipado. Mantén F cerca de la tubería.')
            elif key=='thaw_pipe':
                self.show_notice('Mantén pulsada la tecla F durante tres segundos.')
            elif key=='uv_console':self.modal='uv'
        self.message=instruction(s,self.mode)
        self.sync_end_state()
        if self.mode!='results':self.save()

    def hit_slider(self,mouse):
        if self.modal!='grid':return None
        x,y=mouse
        for idx,name in enumerate(('life','hydro','radiation')):
            yrow=300+idx*76
            if 420<=x<=900 and yrow-18<=y<=yrow+34:
                return name
        return None

    def set_slider(self,name,mouse):
        if name is None or self.state is None:return
        x=mouse[0]
        new_value=int(round((x-420)/480*100/5)*5)
        new_value=max(0,min(100,new_value))
        others=sum(v for k,v in self.state.allocation.items() if k!=name)
        new_value=min(new_value,100-others)
        self.state.allocation[name]=new_value

    def virtual_mouse(self):
        sw,sh=self.window.get_size()
        scale=min(sw/WIDTH,sh/HEIGHT)
        ox=(sw-WIDTH*scale)/2
        oy=(sh-HEIGHT*scale)/2
        mx,my=pygame.mouse.get_pos()
        return ((mx-ox)/scale,(my-oy)/scale)

    def event(self,event):
        if event.type==pygame.QUIT:self.alive=False;return
        if event.type==pygame.VIDEORESIZE:
            self.window=pygame.display.set_mode(event.size,pygame.RESIZABLE);return
        if event.type==pygame.MOUSEBUTTONUP and event.button==1:
            self.drag_slider=None;return
        if event.type==pygame.MOUSEMOTION and self.drag_slider:
            self.set_slider(self.drag_slider,self.virtual_mouse())
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mouse=self.virtual_mouse()
            slider=self.hit_slider(mouse)
            if slider:
                self.drag_slider=slider
                self.set_slider(slider,mouse)
                return
            for rect,action in reversed(self.ui.actions):
                if rect.collidepoint(mouse):
                    self.handle_action(action)
                    return
        if event.type!=pygame.KEYDOWN:return
        key=event.key
        if key==pygame.K_ESCAPE:
            if self.mode=='telemetry':self.handle_action('telemetry_back')
            elif self.mode in ('hub',)+ROOMS:
                if self.modal=='event':self.show_notice('Resuelve la emergencia antes de continuar.')
                else:self.modal=None if self.modal else 'pause'
            elif self.mode=='intro':self.mode='menu'
            elif self.mode=='menu':self.alive=False
            return
        if self.modal:
            if self.modal=='grid' and key in (pygame.K_RETURN,pygame.K_KP_ENTER):self.handle_action('grid_apply')
            elif self.modal=='event' and key in (pygame.K_1,pygame.K_2):self.handle_action('choose_'+str(key-pygame.K_1))
            return
        if self.mode=='intro' and key==pygame.K_RETURN:
            if self.intro_time>=len(INTRO)/35:self.begin_loading()
            else:self.intro_time=len(INTRO)/35
            return
        if self.mode=='loading' and key==pygame.K_RETURN:self.handle_action('skip_nasa')
        if self.mode=='hub' or self.mode in ROOMS:
            if key==pygame.K_SPACE:self.player.jump()
            elif key==pygame.K_t:self.to_telemetry()
            elif key==pygame.K_TAB:self.modal='objectives'
            elif key==pygame.K_e:
                if self.mode=='hub':
                    nearest=min(ROOMS,key=lambda r:abs(hub.ROOM_X[r]-self.player.x))
                    if self.player.near(hub.ROOM_X[nearest],95):self.enter_room(nearest)
                    else:self.show_notice('Acércate a la puerta de un módulo.')
                else:self.interact()
            elif key==pygame.K_n and self.mode=='hub':self.advance_sol()

    def update(self,dt):
        self.elapsed+=dt
        self.notice_time=max(0,self.notice_time-dt)
        if self.notice_time==0:self.notice=''
        snapshot=self.worker.poll()
        if snapshot is not None:
            if self.loading_for_new:self.use_snapshot(snapshot)
            else:
                self.preview_snapshot=snapshot
                self.preview_risk=calculate_risk(snapshot.get('events',{}))
                self.show_notice('Consulta NASA terminada. Se aplicará a la próxima partida.')
        if self.mode=='intro':
            self.intro_time+=dt
            self.video_player.update()
        if self.mode not in ('hub',)+ROOMS or self.modal or self.state is None:return
        platform=(346,918,474) if self.mode=='radiation' else None
        self.player.update(dt,pygame.key.get_pressed(),pygame,platform=platform)
        s=self.state
        s.sol_seconds+=dt
        if self.mode=='life' and not s.operational['life']:
            s.adjust(life=-dt*(.030+s.risk*.00022))
        if self.mode=='generator' and not s.operational['generator']:
            s.adjust(energy=-dt*.028)
        if self.mode=='radiation' and not s.operational['radiation']:
            p=s.progress['radiation']
            p['storm_clock']-=dt
            if p['storm_clock']<=0 and not p['storm_hit']:
                p['storm_hit']=True
                s.adjust(integrity=-15-s.risk*.12)
                s.log('Impacto solar SIMULADO: daños en integridad.')
                self.show_notice('Tormenta impactó la colonia. Repara el emisor lo antes posible.')
        if self.mode=='hydro' and not s.operational['hydro']:
            s.adjust(food=-dt*.020)
            p=s.progress['hydro']
            keys=pygame.key.get_pressed()
            if p['tool'] and p['heat']<3 and self.player.near(663,95) and keys[pygame.K_f]:
                p['heat']=min(3,p['heat']+dt)
                s.adjust(energy=-dt*.2)
                if p['heat']>=3:
                    self.message=instruction(s,'hydro')
                    self.show_notice('Tubería descongelada. Activa las tres lámparas de cultivo.')
        if s.lost:
            self.sync_end_state()
            return
        if s.sol_seconds>=SOL_SECONDS:
            self.advance_sol()

    def draw_loading(self):
        s=self.surface;u=self.ui
        self.assets.draw_background(s,'menu');u.shade(s,180)
        u.rect(s,(292,186,700,322),(8,26,39),CYAN,alpha=244,width=2)
        u.text(s,'CONECTANDO CON NASA DONKI',640,219,'title',WHITE,'center')
        u.lines(s,'Consultando actividad solar reciente (FLR / GST / SEP / CME). Los recursos de la colonia serán parámetros simulados.',340,284,603,'normal',MUTED,max_lines=4)
        time=int(self.elapsed-self.start_time)
        dots='.'*(1+(time%3))
        u.text(s,'Recuperando datos'+dots,640,391,'medium',CYAN,'center')
        u.button(s,'INICIAR SIN CONEXIÓN',(389,440,502,56),'skip_nasa')

    def draw_modal(self):
        if not self.modal:return
        s=self.surface;u=self.ui
        u.actions.clear() # disables controls underneath any modal
        u.shade(s,202)
        if self.modal=='pause':
            u.rect(s,(354,152,572,454),(9,30,47),CYAN,alpha=250,width=2)
            u.text(s,'PAUSA',640,183,'title',WHITE,'center')
            for i,(title,action) in enumerate([('REANUDAR','pause_resume'),('GUARDAR PARTIDA','pause_save'),('VOLVER A LA BASE','pause_hub'),('MENÚ PRINCIPAL','pause_menu')]):
                u.button(s,title,(412,246+82*i,457,62),action,i==0)
        elif self.modal=='objectives':
            u.rect(s,(230,157,820,448),(9,29,44),CYAN,alpha=252,width=2)
            u.text(s,'OBJETIVOS DE LA MISIÓN',266,186,'title',WHITE)
            for i,room in enumerate(ROOMS):
                y=257+i*47
                col=GREEN if self.state.operational[room] else YELLOW
                u.text(s,'✓' if self.state.operational[room] else '○',268,y,'medium',col)
                u.text(s,ROOM_TITLES[room],309,y,'normal',WHITE)
            u.text(s,'INVENTARIO: '+(', '.join(self.state.inventory) or 'Sin herramientas'),267,479,'small',MUTED)
            u.button(s,'VOLVER AL JUEGO',(626,533,378,51),'objectives_close',True)
        elif self.modal=='valve':
            p=self.state.progress['life']
            u.rect(s,(304,175,671,408),(8,28,44),CYAN,alpha=247,width=2)
            u.text(s,'CONSOLA DE PURGA',640,209,'title',WHITE,'center')
            u.text(s,f'GIROS COMPLETADOS: {p["valve"]} / 3',640,276,'medium',CYAN,'center')
            pygame.draw.circle(s,(39,77,99),(640,372),74,15)
            pygame.draw.line(s,CYAN,(640,372),(640+int(54*math.cos(p['valve']*1.6)),372+int(54*math.sin(p['valve']*1.6))),7)
            u.button(s,'GIRAR VÁLVULA +1',(448,482,384,67),'valve_turn',True)
        elif self.modal=='uv':
            p=self.state.progress['hydro']
            u.rect(s,(253,170,775,420),(9,29,43),GREEN,alpha=250,width=2)
            u.text(s,'ILUMINACIÓN PARA CULTIVOS',640,205,'title',WHITE,'center')
            u.text(s,'La luz PAR permite recuperar la fotosíntesis de las plantas.',640,253,'small',MUTED,'center')
            for i in range(3):
                on=p['lamps'][i]
                color=GREEN if on else YELLOW
                u.rect(s,(303+225*i,318,201,128),(22,62,57),color,alpha=243)
                u.text(s,f'PANEL {i+1}',402+225*i,347,'medium',WHITE,'center')
                u.text(s,'ENCENDIDO' if on else 'APAGADO',402+225*i,386,'normal',color,'center')
                u.actions.append((pygame.Rect(303+225*i,318,201,128),f'uv_{i}'))
            u.text(s,'ACTIVA LOS TRES PANELES PARA COMPLETAR EL REINICIO',640,499,'small',WHITE,'center')
        elif self.modal=='grid':
            a=self.state.allocation
            total=sum(a.values())
            u.rect(s,(250,126,780,500),(8,28,43),YELLOW,alpha=249,width=2)
            u.text(s,'CENTRAL DE DISTRIBUCIÓN: 100 W',640,156,'title',WHITE,'center')
            u.text(s,f'Asignados: {total} W   ·   Disponibles: {100-total} W',640,210,'medium',YELLOW,'center')
            rows=[('life','SOPORTE VITAL',CYAN),('hydro','INVERNADERO',GREEN),('radiation','ESCUDOS',PURPLE)]
            for i,(key,label,color) in enumerate(rows):
                y=300+76*i
                u.text(s,label,298,y-13,'normal',WHITE)
                u.text(s,f'MÍNIMO {ALLOCATION_MINIMUM[key]} W',301,y+12,'tiny',MUTED)
                pygame.draw.rect(s,(41,58,70),(420,y,480,14),border_radius=7)
                if a[key]:pygame.draw.rect(s,color,(420,y,int(a[key]/100*480),14),border_radius=7)
                pygame.draw.circle(s,WHITE,(420+int(a[key]/100*480),y+7),12)
                u.text(s,f'{a[key]} W',932,y-5,'medium',color)
            u.text(s,'Arrastra las barras. La suma nunca puede superar 100 W.',640,541,'small',MUTED,'center')
            u.button(s,'APLICAR ESTRATEGIA',(519,562,464,51),'grid_apply',True,color=YELLOW)
        elif self.modal=='event':
            event=self.state.pending_event
            if not event:return
            u.rect(s,(226,141,827,505),(37,24,37),RED,alpha=250,width=2)
            u.text(s,event['title'],639,169,'title',RED,'center')
            u.lines(s,event['body'],280,249,750,'medium',WHITE,max_lines=3)
            for i,choice in enumerate(event['choices']):
                title,k1,v1,k2,v2=choice
                u.button(s,title.upper(),(286,342+i*118,706,70),f'choose_{i}',i==0,color=CYAN if i==0 else YELLOW)
                u.text(s,f'{k1}: {v1:+.1f}   |   {k2}: {v2:+.1f}  [variables simuladas]',327,411+i*118,'small',MUTED)

    def draw(self):
        mouse=self.virtual_mouse()
        self.ui.reset(mouse)
        if self.mode=='menu':menu.draw_menu(self)
        elif self.mode=='intro':menu.draw_intro(self)
        elif self.mode=='loading':self.draw_loading()
        elif self.mode=='hub':hub.draw(self)
        elif self.mode in ROOMS:rooms.draw(self,self.mode)
        elif self.mode=='telemetry':telemetry.draw(self)
        elif self.mode=='results':results.draw(self)
        if self.modal:self.draw_modal()
        if self.notice_time>0 and self.mode not in ('hub',)+ROOMS:
            self.ui.rect(self.surface,(177,663,929,42),(12,36,49),YELLOW,rad=8)
            self.ui.text(self.surface,self.notice,640,673,'small',WHITE,'center')
        sw,sh=self.window.get_size()
        scale=min(sw/WIDTH,sh/HEIGHT)
        nw,nh=max(1,int(WIDTH*scale)),max(1,int(HEIGHT*scale))
        ox,oy=(sw-nw)//2,(sh-nh)//2
        self.window.fill((0,0,0))
        target=pygame.transform.scale(self.surface,(nw,nh)) if (nw,nh)!=(WIDTH,HEIGHT) else self.surface
        self.window.blit(target,(ox,oy))
        pygame.display.flip()

    def run(self):
        try:
            while self.alive:
                dt=min(.05,self.clock.tick(FPS)/1000.0)
                for event in pygame.event.get():self.event(event)
                self.update(dt)
                self.draw()
        finally:
            self.video_player.release()
            pygame.quit()
