import argparse
import os
import json
import sqlite3
import threading
from pathlib import Path

import paho.mqtt.client as mqtt
from fastapi import FastAPI
import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument('--id', type=int, choices=[1, 2, 3], required=True)
args = parser.parse_args()
ident = args.id
porta = 8100 + ident
banco = Path(__file__).resolve().parents[1] / 'dados' / f'replica_{ident}.db'
banco.parent.mkdir(exist_ok=True)
lock = threading.Lock()
con = sqlite3.connect(banco, check_same_thread=False)
with lock:
    con.execute('CREATE TABLE IF NOT EXISTS leituras (timestamp TEXT PRIMARY KEY, sensor TEXT, valor REAL, unidade TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS operacoes (id TEXT PRIMARY KEY, dispositivo TEXT, acao TEXT)')
    con.commit()
app = FastAPI(title=f'Replica {ident}')

from pydantic import BaseModel

class Comando(BaseModel):
    id: str
    dispositivo: str
    acao: str

@app.post('/comandos/preparar')
def preparar(cmd: Comando):
    if cmd.dispositivo != 'ventilador' or cmd.acao not in ('ligar', 'desligar') or not (1 <= len(cmd.id) <= 100):
        from fastapi import HTTPException
        raise HTTPException(400, 'Comando invalido')
    with lock:
        existente = con.execute('SELECT dispositivo, acao FROM operacoes WHERE id=?', (cmd.id,)).fetchone()
        if existente and existente != (cmd.dispositivo, cmd.acao):
            from fastapi import HTTPException
            raise HTTPException(409, 'ID reutilizado com comando diferente')
        con.execute('INSERT OR IGNORE INTO operacoes VALUES (?, ?, ?)', (cmd.id, cmd.dispositivo, cmd.acao))
        con.commit()
    return {'replica': ident, 'preparado': True, 'id': cmd.id}

@app.get('/saude')
def saude():
    return {'replica': ident, 'status': 'ativa'}


@app.get('/leituras/ultima')
def ultima():
    with lock:
        row = con.execute(
            'SELECT timestamp, sensor, valor, unidade '
            'FROM leituras ORDER BY timestamp DESC LIMIT 1'
        ).fetchone()

    if not row:
        return {'replica': ident, 'leitura': None}

    leitura = dict(zip(
        ('timestamp', 'sensor', 'valor', 'unidade'), row
    ))

    # Simulacao de controlador comprometido
    # Ativada somente para testes
    if os.getenv('SIMULAR_FALHA') == '1':
        leitura['valor'] = 99.0
        print(
            f'ALERTA: Replica {ident} enviando valor falso!',
            flush=True
        )

    return {'replica': ident, 'leitura': leitura}


@app.get('/leituras/quantidade')
def quantidade():
    with lock:
        total = con.execute('SELECT COUNT(*) FROM leituras').fetchone()[0]
    return {'replica': ident, 'quantidade': total}

def ao_conectar(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe('casa/sensores/temperatura', qos=1)
        print(f'Replica {ident}: MQTT conectado', flush=True)
    else:
        print('Falha na conexao MQTT:', reason_code, flush=True)

def ao_receber(client, userdata, mensagem):
    try:
        dados = json.loads(mensagem.payload.decode('utf-8'))
        timestamp = str(dados['timestamp'])
        sensor = str(dados['sensor'])
        valor = float(dados['valor'])
        unidade = str(dados['unidade'])
        with lock:
            con.execute('INSERT OR IGNORE INTO leituras VALUES (?, ?, ?, ?)', (timestamp, sensor, valor, unidade))
            con.commit()
        print(f'Replica {ident}: {valor} {unidade} - {timestamp}', flush=True)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as erro:
        print('Leitura rejeitada:', erro, flush=True)

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'smarthome-replica-{ident}')
cliente.on_connect = ao_conectar
cliente.on_message = ao_receber

if __name__ == '__main__':
    cliente.connect('localhost', 1883, 60)
    cliente.loop_start()
    try:
        uvicorn.run(app, host='127.0.0.1', port=porta, log_level='warning')
    finally:
        cliente.loop_stop()
        cliente.disconnect()
        con.close()
