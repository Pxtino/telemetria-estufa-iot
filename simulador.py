#!/usr/bin/env python
# coding: utf-8

# %pip install paho-mqtt

# In[ ]:


import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime

BROKER = "broker.hivemq.com"
TOPICO = "empresa/produto/estufa/telemetria"
CLIENT_ID = f"No-Sensor-ESP32-{random.randint(1000, 9999)}"

sensor = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
sensor.connect(BROKER, 1883, 60)
sensor.loop_start() 

print("Iniciando amostragem de dados dos sensores...\n")
bateria = 100.0 

try:
    while True:
        dados = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dht22_temp_c": round(random.uniform(25.0, 30.0), 2),     
            "dht22_umidade_pct": round(random.uniform(35.0, 55.0), 2),
            "ldr_lux": int(random.uniform(300, 800)),              
            "bateria_pct": round(max(0, bateria), 1)         
        }

        bateria -= random.uniform(0.05, 0.2)
        if bateria < 0: bateria = 100.0 

        payload = json.dumps(dados)
        sensor.publish(TOPICO, payload, qos=1) 
        print(f"[TX] Pacote enviado: {payload}")
        time.sleep(5) 

except KeyboardInterrupt:
    print("\n[STATUS] Simulação encerrada.")
    sensor.loop_stop()
    sensor.disconnect()

