from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
from datetime import datetime
from mysql.connector import pooling, Error
from dotenv import load_dotenv

app = Flask(__name__)
# fecha = datetime.now()
# fecha_form = fecha.strftime("%d/%m/%Y %H:%M:%S")
load_dotenv()

# --- Configuración 
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")       
DB_PASS = os.getenv("DB_PASS")  
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT"))

# --- Pool de conexiones ---
cnxpool = pooling.MySQLConnectionPool(
    pool_name="iot_pool",
    pool_size=5,
    pool_reset_session=True,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    port=DB_PORT,
    autocommit=True,   # para no tener que hacer conn.commit() manual
)

def init_db():
    """Crea la tabla si no existe (se ejecuta al arrancar)."""
    conn = cnxpool.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensores (
                id    INT AUTO_INCREMENT PRIMARY KEY,
                temp  DOUBLE,
                hum   DOUBLE,
                luz   INT,
                ruido FLOAT,
                fecha DATETIME
            )
        """)
    finally:
        cur.close()
        conn.close()

@app.route('/api/data', methods=['POST'])
def recibir_datos():
    data = request.get_json(silent=True) or {}
    # Validación mínima
    for k in ("temp", "hum", "luz", "ruido"):
        if k not in data:
            return jsonify({"status": "error", "msg": f"Campo faltante: {k}"}), 400
    try:
        temp = float(data["temp"])
        hum  = float(data["hum"])
        luz  = int(data["luz"])
        ruido = float(data["ruido"])
    except (ValueError, TypeError):
        return jsonify({"status": "error", "msg": "Tipos de datos inválidos"}), 400

    try:
        conn = cnxpool.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sensores (temp, hum, luz, ruido, fecha) VALUES (%s, %s, %s, %s, %s)",
            (temp, hum, luz, ruido, datetime.now())
        )
        # autocommit=True ya persiste los cambios
        return jsonify({"status": "ok", "received": {"temp": temp, "hum": hum, "luz": luz}})
    except Error as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.route("/ultimos", methods=["GET"])
def ultimos():
    try:
        conn = cnxpool.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, temp, hum, luz, ruido, fecha FROM sensores ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        return jsonify(rows)
    except Error as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/api/series')
def api_series():
    """
    Devuelve últimas N lecturas o un rango temporal.
    Parámetros opcionales:
      - limit (int): número de filas (por defecto 200)
      - from, to: ISO datetime (ej. 2025-10-06T00:00:00)
    """

    limit = int(request.args.get("limit", 200))
    dt_from = request.args.get("from")
    dt_to = request.args.get("to")

    query = "SELECT fecha, temp, hum, luz, ruido FROM sensores"
    params = []

    if dt_from and dt_to:
        try:
            fecha_desde = datetime.fromisoformat(dt_from)
            fecha_hasta = datetime.fromisoformat(dt_to)

            if fecha_desde > fecha_hasta:
                return jsonify({"status": "error", "msg": "El rango de fechas es inválido"}), 400
            
            query += " WHERE fecha BETWEEN %s AND %s ORDER BY fecha ASC"
            params += [fecha_desde, fecha_hasta]

        except ValueError:
            return jsonify({"status": "error", "msg": "Formato de fecha incorrecto"}), 400

    if not (dt_from and  dt_to):
        query += " ORDER BY fecha DESC LIMIT %s"
        params.append(limit)

    conn = cnxpool.get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    rows.reverse()
    labels = [r[0].strftime("%Y-%m-%d %H:%M:%S") if isinstance(r[0], datetime) else str(r[0]) for r in rows]
    temp = [float(r[1]) if r[1] is not None else None for r in rows]
    hum  = [float(r[2]) if r[2] is not None else None for r in rows]
    luz  = [int(r[3])   if r[3] is not None else None for r in rows]
    ruido = [float(r[4]) if r[4] is not None else None for r in rows]

    return jsonify({
        "labels": labels,
        "series": {
            "temp": temp,
            "hum": hum,
            "luz": luz,
            "ruido": ruido
        },
        "count": len(labels)
    })

@app.route('/api/ultimo', methods=['GET'])
def ultimo():
    try:
        conn = cnxpool.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT temp, hum, luz, ruido, fecha FROM sensores ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return jsonify(row or {})
    except Error as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
    finally:
        cur.close()
        conn.close()

            

if __name__ == "__main__":
    print(f"Conectando a MySQL {DB_HOST}:{DB_PORT} / DB: {DB_NAME}")
    init_db()   # Ejecuta aquí la creación de la tabla
    app.run(debug=True)
