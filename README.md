# LUNAR OUTPOST — A.R.I.A. · V1.0

Videojuego educativo 2D creado en Python + **Pygame**. Basado en `version_01.pdf` (23 páginas).

## Instalar y jugar (Windows / VS Code)

1. Descomprime el ZIP. Abre con VS Code la carpeta `LunarOutpost_V1` que contiene `main.py`.
2. Abre **Terminal → Nueva terminal**.
3. Ejecuta:

```powershell
py -m pip install -r requirements.txt
py main.py
```

Si `py` no se reconoce, prueba `python`. Para Linux/macOS utiliza `python3`.
También puedes ejecutar `EJECUTAR_WINDOWS.bat` en Windows. No ejecutes el script de Linux desde PowerShell.

## Controles

| Tecla | Función |
|---|---|
| A / D, flechas | Mover astronauta |
| Espacio | Saltar (para alcanzar la plataforma del emisor) |
| E | Interactuar con marcador / puerta cercana |
| F (mantener) | Utilizar calentador sobre tubería |
| Ratón | Menús, consola eléctrica, válvula, lámparas |
| T | Telemetría NASA |
| TAB | Objetivos, herramientas e inventario |
| N | Avanzar un sol desde la base (también hay botón) |
| ESC | Pausa / volver de telemetría |

## Flujo del juego

**Menú** → introducción A.R.I.A. (Misión Apolo 5) → carga NASA u opción sin conexión → centro de operaciones → cuatro módulos → supervivencia hasta **Sol 30**.

Los módulos iniciales están averiados. Camina hasta una puerta y presiona **E**; el clic en la puerta también funciona cuando estés cerca.

1. **Soporte vital:** recoge sellador, repara tres fisuras y completa tres giros de válvula.
2. **Generador:** quita fusible, recoge el puente, instálalo, mueve sliders y confirma la distribución segura (vida ≥30 W, invernadero ≥25 W, escudos ≥20 W, total ≤100 W).
3. **Escudos:** salta a la plataforma, pulsa E para ajustar tres bobinas a sus frecuencias objetivo y activa el interruptor antes de la tormenta. Si llega, su daño es simulado.
4. **Invernadero:** recoge calentador, acércate a la tubería y mantén **F** unos 3 s; utiliza la consola y enciende tres lámparas.

Luego avanza soles desde el hub. Las reservas se modifican por consumo y decisiones. Al final de algunos soles aparecen **eventos simulados**: debes elegir entre dos opciones con costos y beneficios reales. Algunas malas decisiones pueden averiar módulos que deberás reparar otra vez.

**Victoria:** sobrevivir 30 soles con todos los módulos operativos y ningún recurso agotado. **Derrota:** cualquier recurso crítico llega a 0.

## Datos NASA y simulación: distinción esencial

- Fuente oficial: `https://api.nasa.gov/DONKI` con **FLR, GST, SEP, CME**.
- Consulta los **últimos siete días UTC** en un hilo separado. El juego sigue mostrando la pantalla de carga sin congelarse.
- Cada consulta descarga las observaciones originales, con identificadores, fechas y magnitudes solo cuando DONKI realmente las proporciona.
- El **Índice de riesgo espacial (0–100)** es una **fórmula didáctica del juego**, no un índice oficial de la NASA ni una medición de dosis lunar. Consulta el código `nasa_simulation.py`.
- Oxígeno, temperatura de invernadero, reserva de batería, integridad y el reparto de 100 W son **variables simuladas**, no datos tomados directamente de NASA.
- La API GST incluye índices Kp geomagnéticos terrestres. Se usan solo como contexto del clima espacial y del índice educativo, no como mediciones de radiación lunar.
- Cada nueva partida usa una **semilla aleatoria diferente** para su escenario simulado, sin modificar los datos NASA. La semilla se guarda en la partida.
- La caché dura hasta 3 horas; puedes pulsar **ACTUALIZAR NASA** en Telemetría para solicitar datos frescos. Una actualización no cambia el estado de una partida en curso.
- Si falla la conexión o se agota la cuota: usa caché identificada como tal o **MODO SIMULACIÓN SIN CONEXIÓN**. No se falsifican observaciones NASA.

### Configurar tu NASA API Key (opcional, recomendable)

Obtén tu clave en https://api.nasa.gov/ . La clave **DEMO_KEY** sirve para pruebas y tiene cuotas limitadas. Configúrala como variable de entorno (NO la pongas en el código):

**PowerShell (solo terminal actual):**

```powershell
$env:NASA_API_KEY="TU_CLAVE_NASA"
py main.py
```

**Linux/macOS:**

```bash
export NASA_API_KEY="TU_CLAVE_NASA"
python3 main.py
```

No subas tu clave a GitHub ni incluyas `.env` en un repositorio público.

## Vídeo de introducción (opcional)

El documento solicita `assets/video/fondo_lunar.mp4`, pero **no se incluyó un MP4 con los archivos de origen**. Por eso el juego usa de forma predeterminada una ilustración pixel art.

Si añades tu propio `assets/video/fondo_lunar.mp4`, ejecuta:

```powershell
py -m pip install -r requirements-video-opcional.txt
```

El programa reproducirá el MP4 de forma opcional durante la introducción. Si no tienes el vídeo o OpenCV, usará el fondo PNG y el juego funcionará igual.

## Proyecto / personalización

- `main.py`: inicio.
- `game.py`: bucle, transiciones, interacción y control de estados.
- `game_state.py`: simulación, recursos, 30 soles y guardado.
- `nasa_api.py`: solicitudes NASA no bloqueantes, caché, errores.
- `nasa_simulation.py`: índice didáctico documentado.
- `event_manager.py`: eventos y elecciones.
- `interactables.py`: objetos interactivos y posiciones.
- `player.py`: desplazamiento, salto, gravedad, colisiones con plataforma.
- `ui.py`: HUD, barras, botones y paneles.
- `dialogue.py`: textos A.R.I.A.
- `scenes/`: menú, intro, base, habitaciones, telemetría y resultados.
- `assets/imagenes/`: fondos PNG y astronauta transparente.
- `data/`: guardado y caché generados automáticamente; fuera del control de Git.

### Pruebas sin conexión

```powershell
py -m unittest discover -s tests -v
```

Las pruebas cubren el modelo de 30 soles, la semilla, persistencia, eventos, distribución, validación de API, fallos y recursos. La inspección visual con ventana Pygame debe hacerse en un equipo compatible.

## GitHub y despliegue web

El proyecto es un videojuego de escritorio. **Subirlo directamente a Vercel no lo convierte en un juego web**. Para navegador se requiere una adaptación específica con Pygbag/Pygame-ce o una reimplementación web. `main.py` no contiene una variable `app` de Flask/FastAPI y no debe agregarse solo para silenciar un error de Vercel.

## Nota técnica / educativa

- El reparto de 100 W es un modelo didáctico, no la potencia real de una base lunar.
- La protección electromagnética pertenece a la ciencia ficción del juego.
- Las lámparas de cultivo requieren luz fotosintéticamente activa, no únicamente UV.
- Los soles son ciclos acelerados del videojuego y no días lunares físicos.
- No se ha verificado una descarga en vivo desde NASA en el entorno de creación. Requiere conexión cuando lo ejecutes localmente.
