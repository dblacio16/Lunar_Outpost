"""ARIA instructions; dynamic on-screen dialogue is state-aware."""
INTRO = ('Bienvenido a la Misión Apolo 5. Estás iniciando tu entrenamiento '
         'para la misión más importante de la humanidad. ¿Estás listo?')

INITIAL = {
'life':'Alerta: despresurización en el ducto B. Toma el sellador térmico de la pared y repara las tres fisuras marcadas en rojo antes de que el oxígeno baje de cero.',
'generator':'El inversor eléctrico colapsó. Retira el fusible fundido del módulo central y coloca el puente de repuesto para restablecer el circuito de baterías.',
'radiation':'Tormenta solar detectada en trayectoria directa. Sube a la plataforma del emisor magnético y alinea las tres bobinas exteriores con la frecuencia del panel.',
'hydro':'La temperatura cayó a 2 °C y las bombas de riego están congelándose. Usa la herramienta de calor sobre la tubería de suministro para descongelar el flujo de agua.',
}
SECOND = {
'life':'Fisuras selladas con éxito. Ahora gira la válvula de purga en la consola para estabilizar el flujo de oxígeno.',
'generator':'Circuito restablecido. Solo dispones de 100 vatios: ajusta los controles de la pantalla para distribuir la energía entre los módulos sin sobrecargar la red.',
'radiation':'Frecuencia sincronizada. Activa el interruptor principal del domo para desplegar el escudo electromagnético antes del impacto.',
'hydro':'Tubería descongelada. Enciende manualmente los paneles de luz UV en el tablero para reanudar la fotosíntesis de los cultivos. Se usarán lámparas de cultivo con luz fotosintéticamente activa.',
}

def instruction(state,room):
    if state.operational[room]:return f'Sistema {room} operativo. Puedes regresar a la base.'
    p=state.progress[room]
    if room=='life':
        return SECOND[room] if all(p['fissures']) else INITIAL[room]
    if room=='generator':
        return SECOND[room] if p['stage']>=3 else INITIAL[room]
    if room=='radiation':
        return SECOND[room] if p['coils']==p['targets'] else INITIAL[room]
    if room=='hydro':
        return SECOND[room] if p['heat']>=3 else INITIAL[room]
    return ''
