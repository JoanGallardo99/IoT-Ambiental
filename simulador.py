import requests
import random
import time

URL = "http://127.0.0.1:5000/api/data"

while True:
    data = {
        "temp": round(random.uniform(20, 30), 1),
        "hum": round(random.uniform(40, 60), 1),
        "luz": random.randint(200, 800),
        "ruido": round(random.uniform(50, 100), 1)
    }
    try:
        r = requests.post(URL, json=data, timeout=5)
        print(f"Enviado: {data} -> {r.status_code}")
    except requests.exceptions.RequestException as e: # Clase base que engloba todos los errores posibles de la librería "requests"
        print("Error enviando datos:", e)
    time.sleep(5)

