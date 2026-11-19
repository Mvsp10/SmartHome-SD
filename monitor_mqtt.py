import paho.mqtt.client as mqtt


def ao_conectar(cliente, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Conectado ao broker MQTT. Aguardando mensagens...")
        cliente.subscribe("casa/sensores/#", qos=1)
    else:
        print(f"Falha na conexão: {reason_code}")


def ao_receber(cliente, userdata, mensagem):
    print(f"[{mensagem.topic}] {mensagem.payload.decode('utf-8')}")


def main():
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="monitor-smarthome")
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber
    cliente.connect("localhost", 1883, keepalive=60)
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("Monitor encerrado.")
    finally:
        cliente.disconnect()


if __name__ == "__main__":
    main()
