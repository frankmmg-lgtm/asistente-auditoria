from flask import Flask, request, jsonify
from flask_cors import CORS
# from auditor_assistant import procesar_nuevo_contacto (Movido a rutas locales para evitar bloqueos)
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
        # Importación local para evitar cuelgues al inicio
        from auditor_assistant import procesar_nuevo_contacto
        
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
    """Ruta interna para verificar la configuración sin ataques de red."""
    from auditor_assistant import RESEND_API_KEY, SMTP_USER
    
    # Mask key for safety
    masked_key = "No configurada"
    if RESEND_API_KEY:
        masked_key = f"{RESEND_API_KEY[:6]}...{RESEND_API_KEY[-4:]}"

    return jsonify({
        "status": "diagnostic",
        "config": {
            "resend_api_key_present": bool(RESEND_API_KEY),
            "resend_api_key_masked": masked_key,
            "from_email": SMTP_USER
        },
        "instructions": "Prueba /test_resend para verificar la conexión real con Resend.com"
    })

@app.route('/test_resend', methods=['GET'])
def test_resend():
    """Prueba real de conexión con la API de Resend."""
    from auditor_assistant import RESEND_API_KEY
    import requests
    
    if not RESEND_API_KEY:
        return jsonify({"error": "RESEND_API_KEY no configurada"}), 400

    try:
        # Probamos una llamada simple a la API de Resend con un timeout agresivo
        url = "https://api.resend.com/api-keys"
        headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=3)
        
        return jsonify({
            "status_code": response.status_code,
            "message": "Conexión exitosa" if response.status_code == 200 else "Error en respuesta",
            "detail": response.json() if response.ok else response.text
        })
    except Exception as e:
        return jsonify({"error": f"Fallo de conexión: {str(e)}"}), 500

if __name__ == '__main__':
    # Ejecutar en el puerto 5000 (debug=False para evitar reinicios bruscos en Windows)
    app.run(port=5000, debug=False)
