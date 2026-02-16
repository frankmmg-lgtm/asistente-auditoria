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
        clasificacion = procesar_nuevo_contacto(email_data)
        return jsonify({
            "status": "success",
            "clasificacion": clasificacion,
            "mensaje": "Contacto procesado correctamente"
        }), 200
    except Exception as e:
        error_info = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"ERROR: {error_info}")
        return jsonify(error_info), 500

if __name__ == '__main__':
    # Ejecutar en el puerto 5000 (debug=False para evitar reinicios bruscos en Windows)
    app.run(port=5000, debug=False)
