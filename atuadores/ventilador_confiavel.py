import json
import sqlite3
import threading
from pathlib import Path
import paho.mqtt.client as mqtt

banco = Path(__file__).resolve().parents[1] / 'dados' / 'ventilador.db'
banco.parent.mkdir(exist_ok=True)
con = sqlite3.connect(banco, check_same_thread=False)
lock = threading.Lock()
with lock:
    con.execute('CREATE TABLE IF NOT EXISTS executados (id TEXT PRIMARY KEY, acao TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS estado (dispositivo TEXT PRIMARY KEY, acao TEXT)')
    con.commit()

def conectado(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe('casa/comandos/ventilador', qos=1)
        print('Ventilador confiavel conectado', flush=True)

def recebido(client, userdata, msg):
    try:
        comando = json.loads(msg.payload)
        ident, acao = comando['id'], comando['acao']
        if not isinstance(ident, str) or not ident or acao not in ('ligar', 'desligar'):
            return
        with lock:
            anterior = con.execute('SELECT acao FROM executados WHERE id=?', (ident,)).fetchone()
            if anterior is not None and anterior[0] != acao:
                return
            if anterior is None:
                con.execute('INSERT INTO executados VALUES (?, ?)', (ident, acao))
                con.execute('INSERT OR REPLACE INTO estado VALUES (?, ?)', ('ventilador', acao))
                con.commit()
                print('VENTILADOR:', acao.upper(), flush=True)
            else:
                print('Comando repetido ignorado:', ident, flush=True)
        client.publish('casa/confirmacoes/ventilador', json.dumps({'id': ident, 'acao': acao, 'executado': True}), qos=1)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as erro:
        print('Comando rejeitado:', erro, flush=True)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='atuador-ventilador-confiavel')
client.on_connect = conectado
client.on_message = recebido
client.connect('127.0.0.1', 1883, 60)
try:
    client.loop_forever()
finally:
    con.close()
