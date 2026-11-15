"""NASA DONKI asynchronous client. Raw observations are never randomized."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import queue
import threading
import requests
from settings import NASA_CACHE

URL='https://api.nasa.gov/DONKI'
KINDS=('FLR','GST','SEP','CME')
CACHE_SECONDS=3*3600


def utc_now():return datetime.now(timezone.utc)


def offline_snapshot(message='Sin datos NASA disponibles'):
    return {'source':'NASA DONKI','mode':'offline','fetched_at':'','start':'','end':'',
            'events':{key:[] for key in KINDS},'error':message}


def read_cache(path=NASA_CACHE):
    try:
        obj=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(obj,dict) or not isinstance(obj.get('events'),dict):return None
        if not all(isinstance(obj['events'].get(k),list) for k in KINDS):return None
        obj['mode']='cache'
        return obj
    except (OSError,ValueError,TypeError,KeyError):return None


def cache_is_fresh(snapshot):
    try:
        dt=datetime.fromisoformat(snapshot['fetched_at'].replace('Z','+00:00'))
        return (utc_now()-dt).total_seconds()<CACHE_SECONDS
    except (KeyError,ValueError,TypeError):return False


def fetch_donki(path=NASA_CACHE,force=False,get=requests.get):
    cache=read_cache(path)
    if cache and cache_is_fresh(cache) and not force:return cache
    today=utc_now().date()
    params={'startDate':(today-timedelta(days=7)).isoformat(),'endDate':today.isoformat(),
            'api_key':os.getenv('NASA_API_KEY','DEMO_KEY')}
    events={}
    try:
        for kind in KINDS:
            response=get(f'{URL}/{kind}',params=params,timeout=5)
            response.raise_for_status()
            payload=response.json()
            if not isinstance(payload,list):raise ValueError(f'{kind} no devolvió una lista')
            if not all(isinstance(item,dict) for item in payload):
                raise ValueError(f'Elementos no válidos en {kind}')
            events[kind]=payload
        snapshot={'source':'NASA DONKI','mode':'online','fetched_at':utc_now().isoformat(),
                  'start':params['startDate'],'end':params['endDate'],'events':events,'error':''}
        try:
            p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
            tmp=p.with_suffix('.tmp')
            tmp.write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
            tmp.replace(p)
        except OSError:pass
        return snapshot
    except (requests.RequestException,ValueError,TypeError) as exc:
        if cache:
            cache['mode']='cache'
            cache['error']=f'Consulta fallida: {type(exc).__name__}. Datos de caché.'
            return cache
        obj=offline_snapshot(f'Consulta fallida: {type(exc).__name__}. Simulación local sin mediciones NASA.')
        return obj


class NasaWorker:
    def __init__(self, fetch=fetch_donki):
        self.result=queue.Queue(maxsize=3)
        self.thread=None
        self.fetch=fetch

    def start(self,force=False):
        if self.thread is not None and self.thread.is_alive():return False
        def work():
            try: result=self.fetch(force=force)
            except Exception as exc:result=offline_snapshot(f'Fallo inesperado: {type(exc).__name__}')
            self.result.put(result)
        self.thread=threading.Thread(target=work,daemon=True)
        self.thread.start()
        return True

    def poll(self):
        try:return self.result.get_nowait()
        except queue.Empty:return None
