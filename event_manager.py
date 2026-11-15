"""Seeded, solvable events with real resource consequences."""

def pick_event(state):
    rng=state.rng('daily_event')
    # About every 3 game sols; higher NASA-derived risk raises simulated event frequency.
    prob=0.12+state.risk/400
    if rng.random()>prob:return None
    kind=rng.choice(['solar','freeze','power','leak'])
    data={
        'solar':{
            'title':'ALERTA DE PARTÍCULAS SOLARES',
            'body':'Evento simulado de radiación. ¿Cómo protegemos la base?',
            'choices':[('Reforzar blindaje','energy',-7,'integrity',2),('Mantener producción','integrity',-8-state.risk*.07,'food',2)]
        },
        'freeze':{
            'title':'CONDUCTO DE RIEGO CONGELADO',
            'body':'El domo perdió temperatura. ¿Qué prioridad eliges?',
            'choices':[('Activar calefacción','energy',-7,'food',3),('Ahorrar electricidad','food',-8,'energy',3)]
        },
        'power':{
            'title':'CAÍDA DE EFICIENCIA EN EL INVERSOR',
            'body':'Dos sistemas requieren la reserva. ¿Cuál proteger?',
            'choices':[('Proteger soporte vital','energy',-6,'life',5),('Proteger reservas','life',-6,'energy',5)]
        },
        'leak':{
            'title':'FUGA DE PRESIÓN INTERNA',
            'body':'Se detectó pérdida en un conducto secundario.',
            'choices':[('Cerrar válvula auxiliar','energy',-6,'life',5),('Aplazar reparación','life',-9,'energy',2)]
        }
    }[kind]
    # Damages a module sometimes; it becomes a new repair task.
    broken={'solar':'radiation','freeze':'hydro','power':'generator','leak':'life'}[kind]
    data={'kind':kind,'broken':broken,**data}
    return data


def resolve_event(state,index:int):
    event=state.pending_event
    if event is None:return False
    if not 0 <= index < len(event['choices']):return False
    title,key_a,val_a,key_b,val_b=event['choices'][index]
    state.adjust(**{key_a:val_a,key_b:val_b})
    if not state.lost and index==1 and state.rng('fault').random()<0.23:
        state.reset_room(event['broken'])
        state.log(f'Sistema averiado: {event["broken"]}. Debe repararse de nuevo.')
    state.choices.append({'sol':state.sol,'event':event['kind'],'choice':title,
                          'changes':{key_a:val_a,key_b:val_b}})
    state.log(f'{title}: {key_a} {val_a:+g}, {key_b} {val_b:+g} (simulado).')
    state.pending_event=None
    state.check_end()
    return True
