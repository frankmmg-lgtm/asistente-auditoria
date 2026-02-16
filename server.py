from flask import Flask, request, jsonify
from flask_cors import CORS
from auditor_assistant import procesar_nuevo_contacto
import os
import traceback

app = Flask(__name__)
CORS(app) # Habilitar CORS para todas las rutas

@app.route('/', methods=['GET'])
def home():
    """Ruta de verificación para confirmar que el servidor está activo."""
    return jsonify({"status": "ok", "message": "Servidor de auditoría activo"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Ruta que recibirá los datos del formulario web.
    Se espera un JSON con: nombre, email, asunto, cuerpo.
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400
    
    # Mapeo de campos del formulario a nuestra estructura
    email_data = {
        "remitente": data.get("nombre", "Desconocido"),
        "email": data.get("email"),
        "asunto": data.get("asunto", "Contacto desde la web"),
        "cuerpo": data.get("mensaje", "") or data.get("cuerpo", "")
    }
    
    if not email_data["email"]:
        return jsonify({"error": "Falta el campo email"}), 400

    try:
        # Llamamos a nuestra lógica principal
        reporte = procesar_nuevo_contacto(email_data)
        return jsonify({
            "status": "success",
            "reporte": reporte,
            "mensaje": "Contacto procesado correctamente"
        }), 200
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

@app.route('/test_email', methods=['GET'])
def test_email():
    """Ruta interna para probar la conectividad SMTP."""
    from auditor_assistant import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    import smtplib
    
    resultados = {
        "config": {
            "server": SMTP_SERVER,
            "port": SMTP_PORT,
            "user": SMTP_USER
        },
        "tests": {}
    }
    
    try:
        import socket
        socket.create_connection((SMTP_SERVER, SMTP_PORT), timeout=3)
        resultados["tests"]["socket"] = "✅ Conexión básica exitosa"
    except Exception as e:
        resultados["tests"]["socket"] = f"❌ Fallo de socket (3s): {str(e)}"

    try:
        if SMTP_PORT == 465:
            s = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=5)
        else:
            s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=5)
            s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.quit()
        resultados["tests"]["smtp"] = "✅ Autenticación SMTP exitosa"
    except Exception as e:
        resultados["tests"]["smtp"] = f"❌ Fallo SMTP: {str(e)}"
        
    return jsonify(resultados)

if __name__ == '__main__':
    # Ejecutar en el puerto 5000 (debug=False para evitar reinicios bruscos en Windows)
    app.run(port=5000, debug=False)
