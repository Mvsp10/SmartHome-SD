
import json
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORTA = 1883

TOPICO = "casa/atuadores/ventilador"


def ao_conectar(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Ventilador conectado ao MQTT!")
        client.subscribe(TOPICO)
    else:
        print("Erro de conexão:", reason_code)


def ao_receber(client, userdata, msg):
    try:
        comando = json.loads(msg.payload.decode())
        acao = comando.get("acao")

        if acao == "ligar":
            print("VENTILADOR LIGADO!")
        elif acao == "desligar":
            print("VENTILADOR DESLIGADO!")
        else:
            print("Comando desconhecido:", acao)

    except json.JSONDecodeError:
        print("Mensagem inválida recebida.")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="atuador_ventilador"
)

client.on_connect = ao_conectar
client.on_message = ao_receber

client.connect(BROKER, PORTA, 60)

print("Ventilador aguardando comandos...")
client.loop_forever()
