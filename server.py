from flask import Flask, request, jsonify
from flask_cors import CORS
# from auditor_assistant import procesar_nuevo_contacto (Movido a rutas locales para evitar bloqueos)
import os
import traceback

app = Flask(__name__)
CORS(app) # Habilitar CORS para todas las rutas

# Versión del servidor
from auditor_assistant import VERSION

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
    from auditor_assistant import get_config
    
    config = get_config()
    resend_key = config.get("RESEND_API_KEY", "")
    from_email = config.get("SMTP_USER", "")

    # Mask key for safety
    masked_key = "No configurada"
    if resend_key:
        masked_key = f"{resend_key[:6]}...{resend_key[-4:]}"

    return jsonify({
        "status": "diagnostic",
        "version": VERSION,
        "config": {
            "resend_api_key_present": bool(resend_key),
            "resend_api_key_masked": masked_key,
            "actual_sender": "Auditor <onboarding@resend.dev>"
        },
        "instructions": "Prueba /test_resend para verificar la conexión real con Resend.com"
    })

@app.route('/test_resend', methods=['GET'])
def test_resend():
    """Prueba real de conexión con la API de Resend."""
    from auditor_assistant import get_config
    import requests
    
    config = get_config()
    resend_key = config.get("RESEND_API_KEY", "")
    
    if not resend_key:
        return jsonify({"error": "RESEND_API_KEY no configurada"}), 400

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {resend_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "onboarding@resend.dev",
        "to": ["frankmmg@gmail.com"],
        "subject": "Prueba de Diagnóstico v1.4.1",
        "text": "Si recibes esto, el servidor DE VERDAD puede enviar correos a frankmmg@gmail.com."
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return jsonify({
            "status_code": response.status_code,
            "message": "Enviado" if response.status_code in [200, 201] else "Error en respuesta",
            "detail": response.json() if response.ok else response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test_env_keys', methods=['GET'])
def test_env_keys():
    """Ruta de diagnóstico para listar CLAVES de entorno (sin valores)."""
    import os
    keys = sorted(os.environ.keys())
    return jsonify({
        "status": "diagnostic",
        "env_keys": keys,
        "message": "Usa esto para verificar si RESEND_API_KEY aparece en la lista exactamente con ese nombre."
    })

if __name__ == '__main__':
    # Ejecutar en el puerto 5000 (debug=False para evitar reinicios bruscos en Windows)
    app.run(port=5000, debug=False)
