"""Loads actual PNG assets once; all missing resources have drawn Pygame fallbacks."""
from pathlib import Path
from settings import IMAGES, WIDTH, HEIGHT

class AssetManager:
    def __init__(self,pygame):
        self.pg=pygame
        self.images={}
        files={'menu':'fondo_inicio.png','hub':'fondo_base.png','life':'soporte_vital.png',
               'generator':'generador.png','radiation':'radiacion.png','hydro':'invernadero.png',
               'astronaut':'astronauta.png'}
        for key,name in files.items():
            path=IMAGES/name
            if not path.exists():continue
            try:
                raw=pygame.image.load(str(path))
                if key=='astronaut':
                    self.images[key]=pygame.transform.scale(raw.convert_alpha(),(66,94))
                else:
                    self.images[key]=pygame.transform.scale(raw.convert(),(WIDTH,HEIGHT))
            except (pygame.error,OSError) as exc:
                print(f'Recurso opcional no disponible: {path.name}: {exc}')
        for i in range(4):
            key=f'walk_{i}'
            path=IMAGES/f'astronauta_walk_{i}.png'
            if path.exists():
                try:self.images[key]=pygame.transform.scale(pygame.image.load(str(path)).convert_alpha(),(66,94))
                except (pygame.error,OSError):pass

    def draw_background(self,canvas,key):
        if key in self.images:
            canvas.blit(self.images[key],(0,0))
        else:
            canvas.fill((8,20,32))
            pg=self.pg
            # Fallback room/space gradient with functional floor.
            for x in range(0,WIDTH,45):
                pg.draw.line(canvas,(22,42,56),(x,120),(x,600),1)
            pg.draw.rect(canvas,(26,41,57),(0,535,WIDTH,185))
            for x in range(0,WIDTH,80):
                pg.draw.line(canvas,(40,56,70),(x,535),(x-50,720),1)
            for y in range(535,720,50):pg.draw.line(canvas,(40,56,70),(0,y),(WIDTH,y),1)

    def draw_astronaut(self,canvas,player):
        pg=self.pg
        key=f'walk_{int(player.anim*8)%4}' if player.moving and player.grounded else 'astronaut'
        img=self.images.get(key) or self.images.get('astronaut')
        x=int(player.x);feet=int(player.feet)
        if img:
            if player.facing<0:img=pg.transform.flip(img,True,False)
            canvas.blit(img,(x-img.get_width()//2,feet-img.get_height()))
        else:
            pg.draw.circle(canvas,(220,244,255),(x,feet-60),22)
            pg.draw.rect(canvas,(191,210,225),(x-17,feet-43,34,39),border_radius=7)
            pg.draw.rect(canvas,(33,157,193),(x-13,feet-68,26,16),border_radius=5)
            for dx in (-11,11):pg.draw.line(canvas,(240,246,252),(x+dx,feet-12),(x+dx,feet),7)
        if player.interact_pulse>0:
            pg.draw.circle(canvas,(60,223,249),(x,feet-48),50,2)
