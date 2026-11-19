from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from uuid import uuid4
from threading import Event, Lock
import paho.mqtt.client as mqtt
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path
import uvicorn

app = FastAPI(title='SmartHome SD - Middleware')
REPLICAS = [f'http://127.0.0.1:{porta}' for porta in (8101, 8102, 8103)]

def consultar(url):
    try:
        with urlopen(url + '/leituras/ultima', timeout=1.5) as resposta:
            return json.load(resposta)
    except Exception:
        return None

@app.get('/estado')
def estado():
    with ThreadPoolExecutor(max_workers=3) as pool:
        respostas = list(pool.map(consultar, REPLICAS))
    ativas = [r for r in respostas if r is not None]
    # Votacao exige ao menos duas replicas concordando na MESMA leitura.
    # Leituras recentes podem divergir temporariamente por atraso de entrega MQTT.
    votos = Counter(json.dumps(r['leitura'], sort_keys=True) for r in ativas if r['leitura'] is not None)
    if not votos:
        return JSONResponse(status_code=503, content={'status': 'sem_leituras', 'replicas_ativas': len(ativas)})
    vencedor, contagem = votos.most_common(1)[0]
    if contagem < 2:
        return JSONResponse(status_code=503, content={'status': 'sem_consenso', 'replicas_ativas': len(ativas), 'respostas': ativas})
    leitura = json.loads(vencedor)
    divergentes = [r['replica'] for r in ativas if r['leitura'] != leitura]
    return {'status': 'consenso', 'leitura': leitura, 'votos': contagem, 'replicas_ativas': len(ativas), 'replicas_divergentes': divergentes}


# Confirmacoes recebidas pelo MQTT. So retornamos sucesso apos ACK do atuador.
pendentes = {}
pendentes_lock = Lock()
confirmados = {}

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='middleware-comandos')

def mqtt_conectado(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe('casa/confirmacoes/ventilador', qos=1)

def mqtt_recebido(client, userdata, msg):
    try:
        dados = json.loads(msg.payload)
        ident = dados['id']
        if dados.get('executado') is True:
            with pendentes_lock:
                confirmados[ident] = dados
                if ident in pendentes:
                    pendentes[ident].set()
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        pass

mqtt_client.on_connect = mqtt_conectado
mqtt_client.on_message = mqtt_recebido

@app.on_event('startup')
def iniciar_mqtt():
    mqtt_client.connect('127.0.0.1', 1883, 60)
    mqtt_client.loop_start()

@app.on_event('shutdown')
def parar_mqtt():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

class Pedido(BaseModel):
    acao: str
    id: str | None = None

@app.post('/comandos/ventilador')
def comandar(pedido: Pedido):
    if pedido.acao not in ('ligar', 'desligar'):
        return JSONResponse(status_code=400, content={'erro': 'acao deve ser ligar ou desligar'})
    ident = pedido.id or str(uuid4())
    if not (1 <= len(ident) <= 100):
        return JSONResponse(status_code=400, content={'erro': 'id invalido'})
    comando = {'id': ident, 'dispositivo': 'ventilador', 'acao': pedido.acao}
    # Fallback: se uma replica cair, tentamos outra.
    preparada = None
    for replica in REPLICAS:
        try:
            requisicao = Request(replica + '/comandos/preparar',
                data=json.dumps(comando).encode(),
                headers={'Content-Type': 'application/json'}, method='POST')
            with urlopen(requisicao, timeout=1.5) as resposta:
                preparada = json.load(resposta)['replica']
                break
        except HTTPError as erro:
            if erro.code in (400, 409):
                return JSONResponse(status_code=erro.code, content={'erro': 'comando rejeitado pela replica', 'id': ident})
        except Exception:
            continue
    if preparada is None:
        return JSONResponse(status_code=503, content={'status': 'sem_controlador', 'id': ident})
    evento = Event()
    with pendentes_lock:
        pendentes[ident] = evento
        if ident in confirmados and confirmados[ident].get('acao') == pedido.acao:
            evento.set()
    try:
        # Reenvio seguro: o atuador deduplica por ID no SQLite.
        for tentativa in range(3):
            mqtt_client.publish('casa/comandos/ventilador', json.dumps(comando), qos=1)
            if evento.wait(2):
                with pendentes_lock:
                    ack = confirmados.get(ident)
                if ack and ack.get('acao') == pedido.acao:
                    return {'status': 'executado', 'id': ident, 'acao': pedido.acao,
                            'controlador_utilizado': preparada, 'tentativas': tentativa + 1}
        return JSONResponse(status_code=504, content={'status': 'sem_confirmacao', 'id': ident,
            'aviso': 'Pode ter sido executado. Reenvie o MESMO id para consultar/repetir com seguranca.'})
    finally:
        with pendentes_lock:
            pendentes.pop(ident, None)

@app.get('/', response_class=HTMLResponse, include_in_schema=False)
def pagina_cliente():
    arquivo = Path(__file__).resolve().parents[1] / 'cliente' / 'index.html'
    return HTMLResponse(arquivo.read_text(encoding='utf-8'))

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
