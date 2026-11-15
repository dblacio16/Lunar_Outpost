"""Side-view character movement and simple gravity/platform collisions."""
from __future__ import annotations

class Player:
    def __init__(self,x=100,feet=545):
        self.x=float(x)
        self.feet=float(feet)
        self.velocity_y=0.0
        self.facing=1
        self.moving=False
        self.grounded=True
        self.on_platform=False
        self.anim=0.0
        self.interact_pulse=0.0

    def reset(self,x=100):
        self.__init__(x)

    def update(self,dt,keys,pygame,platform=None):
        ax=int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        self.moving=ax!=0
        if ax:self.facing=ax
        self.x=max(55,min(1216,self.x+ax*250*dt))
        old_feet=self.feet
        self.velocity_y+=1100*dt
        self.feet+=self.velocity_y*dt
        self.grounded=False
        self.on_platform=False
        if platform is not None:
            x1,x2,top=platform
            if x1<=self.x<=x2 and old_feet<=top and self.feet>=top and self.velocity_y>=0:
                self.feet=float(top)
                self.velocity_y=0
                self.grounded=True
                self.on_platform=True
        if self.feet>=545:
            self.feet=545.0
            self.velocity_y=0
            self.grounded=True
        self.anim+=dt
        self.interact_pulse=max(0.0,self.interact_pulse-dt)

    def jump(self):
        if self.grounded:
            self.velocity_y=-520.0
            self.grounded=False

    def near(self,x,distance=90):
        return abs(self.x-x) <= distance
