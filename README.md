# Estación IoT – Dashboard

Dashboard web desarrollado con **Flask** y **Chart.js** para visualizar datos de sensores (temperatura, humedad, luz y ruido) en tiempo real.

## Características
- Modo oscuro completo
- Actualización automática cada 5 segundos
- Filtros de fecha/hora y límite de lecturas
- Gráficos de línea interactivos
- API REST para recibir datos desde ESP32

## Tecnologías
- Python (Flask)
- MySQL
- HTML / CSS / JavaScript
- Chart.js

## Estructura
iot-dashboard/
   - endpoint.py
   - /templates/dashboard.html
   - simulador.py

## Instalación
```bash
pip install -r requirements.txt
python app.py
