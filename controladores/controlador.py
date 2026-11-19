
import json
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORTA = 1883

TOPICO_SENSOR = "casa/sensores/temperatura"
TOPICO_VENTILADOR = "casa/atuadores/ventilador"

ventilador_ligado = False


def ao_conectar(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Controlador conectado ao MQTT!")
        client.subscribe(TOPICO_SENSOR)
    else:
        print("Erro de conexão:", reason_code)


def ao_receber(client, userdata, msg):
    global ventilador_ligado

    try:
        dados = json.loads(msg.payload.decode())
        temperatura = float(dados["valor"])

        print(f"Temperatura recebida: {temperatura:.1f} °C")

        novo_estado = ventilador_ligado

        if temperatura > 30:
            novo_estado = True
        elif temperatura < 25:
            novo_estado = False

        if novo_estado != ventilador_ligado:
            ventilador_ligado = novo_estado

            comando = {
                "dispositivo": "ventilador",
                "acao": "ligar" if ventilador_ligado else "desligar",
                "origem": "controlador_1"
            }

            client.publish(
                TOPICO_VENTILADOR,
                json.dumps(comando),
                qos=1
            )

            print("Comando enviado:", comando["acao"])
        else:
            print("Estado mantido.")

    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as erro:
        print("Mensagem inválida:", erro)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="controlador_1"
)

client.on_connect = ao_conectar
client.on_message = ao_receber

client.connect(BROKER, PORTA, 60)

print("Controlador iniciado. Aguardando temperaturas...")
client.loop_forever()
