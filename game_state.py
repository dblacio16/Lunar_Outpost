"""Pure Python persistent state and the 30-sol survival simulation."""
from __future__ import annotations
import json
import random
import secrets
from dataclasses import dataclass, field
from pathlib import Path

ROOMS = ('life','generator','radiation','hydro')
ALLOCATION_MINIMUM = {'life':30,'hydro':25,'radiation':20}


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


def clean_allocation(powers: dict) -> dict:
    """A safe grid cannot be configured above 100 fictitious teaching watts."""
    result = {key:max(0,int(powers.get(key,0))) for key in ALLOCATION_MINIMUM}
    if sum(result.values()) > 100:
        raise ValueError('Potencia total superior a 100 W')
    return result


def new_room_progress(room: str) -> dict:
    if room == 'life':return {'tool':False,'fissures':[False,False,False],'valve':0}
    if room == 'generator':return {'stage':0,'configured':False}
    if room == 'radiation':return {'coils':[1,1,1],'targets':[2,4,3], 'shield':False,'storm_clock':105.0,'storm_hit':False}
    if room == 'hydro':return {'tool':False,'heat':0.0,'lamps':[False,False,False]}
    raise ValueError('Sala inexistente')


@dataclass
class GameState:
    sol: int = 1
    sol_seconds: float = 0.0
    resources: dict = field(default_factory=lambda:{'life':88.0,'energy':80.0,'food':86.0,'integrity':90.0})
    operational: dict = field(default_factory=lambda:{room:False for room in ROOMS})
    progress: dict = field(default_factory=lambda:{room:new_room_progress(room) for room in ROOMS})
    allocation: dict = field(default_factory=lambda:{'life':35,'hydro':30,'radiation':20})
    inventory: list = field(default_factory=list)
    seed: int = 0
    risk: int = 25
    science: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    choices: list = field(default_factory=list)
    pending_event: dict | None = None
    player_x: float = 100.0
    current_scene: str = 'hub'
    won: bool = False
    lost: bool = False
    reason: str = ''

    @classmethod
    def fresh(cls, science: dict, risk: int, seed: int | None = None):
        if seed is None:
            seed = secrets.randbits(48)
        rand = random.Random(seed)
        risk = max(0,min(100,int(risk)))
        res = {
            'life':clamp(84-rand.randrange(0,8)-risk*.08,42,98),
            'energy':clamp(83-rand.randrange(0,10)-risk*.13,42,98),
            'food':clamp(89-rand.randrange(0,9)-risk*.07,42,98),
            'integrity':clamp(91-rand.randrange(0,9)-risk*.11,42,98),
        }
        state = cls(resources=res, seed=seed, risk=risk, science=science)
        state.reset_room('radiation')
        state.log('Misión de entrenamiento iniciada. Valores de la colonia simulados.')
        return state

    def rng(self, namespace='general', extra=0):
        # Stable arbitrary seed via string mixing, no randomized Python hash().
        entropy = sum((i+1)*ord(c) for i,c in enumerate(namespace))
        return random.Random(self.seed+entropy+self.sol*104729+extra*8191)

    def log(self, message: str):
        self.events.insert(0,{'sol':self.sol,'text':str(message)[:170]})
        self.events = self.events[:50]

    def adjust(self, **deltas):
        for name, delta in deltas.items():
            if name not in self.resources:
                raise KeyError(name)
            self.resources[name] = clamp(self.resources[name]+float(delta))
        self.check_end()

    def check_end(self):
        if self.won or self.lost:
            return
        gone = [name for name,value in self.resources.items() if value <= 0]
        if gone:
            self.lost = True
            self.reason = f'La colonia perdió un recurso crítico: {gone[0]}.'
        elif self.sol >= 30 and not self.pending_event and all(self.operational.values()):
            self.won = True
            self.reason = 'La colonia sobrevivió 30 soles con los cuatro módulos operativos.'

    def reset_room(self, room: str):
        self.progress[room] = new_room_progress(room)
        if room == 'radiation':
            r = self.rng('coils')
            self.progress[room]['targets'] = [r.randint(1,5) for _ in range(3)]
            self.progress[room]['storm_clock'] = max(65,140-self.risk*.65)
        self.operational[room] = False

    def repair(self, room: str):
        if room not in ROOMS:
            raise ValueError(room)
        if self.operational[room]:return
        self.operational[room] = True
        boost = {'life':('life',27),'generator':('energy',29),'radiation':('integrity',27),'hydro':('food',27)}
        key, value = boost[room]
        self.adjust(**{key:value})
        self.log(f'Sistema restablecido: {room}. +{value} puntos de {key} (simulado).')
        self.check_end()

    def configure_allocation(self, allocation):
        power = clean_allocation(allocation)
        self.allocation = power
        is_stable = all(power.get(k,0)>=v for k,v in ALLOCATION_MINIMUM.items())
        self.log(f'Red asignada: {sum(power.values())}/100 W. '+('Estable.' if is_stable else 'Asignación insuficiente.'))
        return is_stable

    def advance_sol(self):
        """Advance by one game sol; this is NOT a real physical lunar-day model."""
        if self.won or self.lost or self.pending_event or self.sol >= 30:
            return False
        deficits = {k:max(0,n-self.allocation[k]) for k,n in ALLOCATION_MINIMUM.items()}
        # Slow but meaningful attrition; reactor outputs are not real station kW.
        impact = {
            'life':-0.55-deficits['life']*.25-(0 if self.operational['life'] else 2.4),
            'energy':-1.15-(0 if self.operational['generator'] else 3.3) - (sum(self.allocation.values())/100)*.7,
            'food':-0.65-deficits['hydro']*.27-(0 if self.operational['hydro'] else 2.2),
            'integrity':-0.40-deficits['radiation']*.32-(0 if self.operational['radiation'] else 1.2),
        }
        # Greenhouse output and generator recharge, only after repairs.
        if self.operational['generator']:
            impact['energy'] += 1.15
        if self.operational['hydro']:
            impact['food'] += 1.20
        self.adjust(**impact)
        if self.lost:return True
        self.sol += 1
        self.sol_seconds = 0
        self.log(f'Sol {self.sol}: consumo de recursos calculado.')
        self.check_end()
        return True

    def to_dict(self):
        return {k:getattr(self,k) for k in self.__dataclass_fields__}

    def save(self,path: Path):
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps({'version':1,'state':self.to_dict()},ensure_ascii=False,indent=2),encoding='utf-8')
        tmp.replace(path)

    @classmethod
    def load(cls,path: Path):
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('version')!=1 or not isinstance(data.get('state'),dict):
            raise ValueError('Guardado no compatible')
        obj = data['state']
        if not all(k in obj for k in ('resources','operational','progress','seed','sol','science')):
            raise ValueError('Guardado incompleto')
        loaded = cls(**{k:v for k,v in obj.items() if k in cls.__dataclass_fields__})
        loaded.allocation = clean_allocation(loaded.allocation)
        loaded.resources = {name:clamp(loaded.resources.get(name,50)) for name in ('life','energy','food','integrity')}
        loaded.check_end()
        return loaded
