"""Logical interactables; artwork is separate from hitboxes and game actions."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Hotspot:
    key: str
    x: int
    y: int
    label: str
    platform: bool = False


def room_hotspots(state,room):
    if state.operational[room]:return []
    p=state.progress[room]
    if room=='life':
        if not p['tool']:
            return [Hotspot('get_sealant',224,455,'RECOGER SELLADOR')]
        missing=[Hotspot(f'fissure_{i}',x,448,f'SELLAR FISURA {i+1}')
                 for i,x in enumerate((427,618,811)) if not p['fissures'][i]]
        return missing or [Hotspot('purge',1030,464,'GIRAR VÁLVULA')]
    if room=='generator':
        return [
            Hotspot('remove_fuse',467,458,'RETIRAR FUSIBLE'),
            Hotspot('get_bridge',260,458,'RECOGER PUENTE'),
            Hotspot('install_bridge',635,458,'INSTALAR PUENTE'),
            Hotspot('grid_console',1030,456,'CONSOLA 100 W')
        ][p['stage']:p['stage']+1]
    if room=='radiation':
        if p['coils']!=p['targets']:
            return [Hotspot(f'coil_{i}',x,423,f'BOBINA {i+1} · {p["coils"][i]} / {p["targets"][i]}',True)
                    for i,x in enumerate((418,644,872)) if p['coils'][i]!=p['targets'][i]]
        return [Hotspot('shield_switch',1070,453,'ENCENDER DOMO')]
    if room=='hydro':
        if not p['tool']:return [Hotspot('get_heater',223,458,'RECOGER CALENTADOR')]
        if p['heat']<3:return [Hotspot('thaw_pipe',663,460,'MANTÉN F PARA CALENTAR')]
        return [Hotspot('uv_console',1050,456,'ACTIVAR LÁMPARAS')]
    return []
