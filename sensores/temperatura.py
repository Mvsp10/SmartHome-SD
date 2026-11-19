import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORTA = 1883
TOPICO = "casa/sensores/temperatura"


def main():
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sensor-temperatura")
    cliente.connect(BROKER, PORTA, keepalive=60)
    cliente.loop_start()
    try:
        while True:
            leitura = {
                "sensor": "temperatura_sala",
                "valor": round(random.uniform(18, 35), 1),
                "unidade": "C",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            resultado = cliente.publish(TOPICO, json.dumps(leitura), qos=1)
            resultado.wait_for_publish()
            print(f"Publicado em {TOPICO}: {leitura}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("Sensor encerrado.")
    finally:
        cliente.loop_stop()
        cliente.disconnect()


if __name__ == "__main__":
    main()
