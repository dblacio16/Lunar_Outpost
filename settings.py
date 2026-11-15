"""Configuration, asset locations and colors for Lunar Outpost v1.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
IMAGES = ASSETS / 'imagenes'
VIDEOS = ASSETS / 'video'
DATA = ROOT / 'data'
SAVE_FILE = DATA / 'savegame.json'
NASA_CACHE = DATA / 'nasa_cache.json'
WIDTH, HEIGHT = 1280, 720
FPS = 60
SOL_SECONDS = 180.0  # one game sol is a configurable cycle, not a real lunar day
FLOOR = 550

BG = (4, 12, 21)
PANEL = (12, 29, 44)
PANEL_LIGHT = (24, 49, 68)
EDGE = (74, 113, 134)
WHITE = (237, 249, 251)
MUTED = (166, 192, 205)
CYAN = (61, 219, 246)
GREEN = (102, 227, 168)
YELLOW = (251, 191, 89)
RED = (251, 104, 107)
PURPLE = (187, 149, 250)

ROOMS = ('life', 'generator', 'radiation', 'hydro')
ROOM_TITLES = {
 'life':'SOPORTE VITAL', 'generator':'BAHÍA DEL GENERADOR',
 'radiation':'CÚPULA DE PROTECCIÓN', 'hydro':'DOMO HIDROPÓNICO'
}
ROOM_ASSETS = {'life':'soporte_vital.png','generator':'generador.png',
               'radiation':'radiacion.png','hydro':'invernadero.png'}
RESOURCE_COLORS = {'life':CYAN,'energy':YELLOW,'food':GREEN,'integrity':PURPLE}
RESOURCE_NAMES = {'life':'SOPORTE VITAL','energy':'ENERGÍA','food':'ALIMENTOS','integrity':'INTEGRIDAD'}
