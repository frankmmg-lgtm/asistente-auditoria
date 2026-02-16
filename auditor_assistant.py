import json
import csv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Puerto SMTP robusto
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
except (ValueError, TypeError):
    SMTP_PORT = 587

# Configurar Gemini
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Configuración de Correo
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
AUDITOR_NAME = os.getenv("AUDITOR_NAME", "Equipo de Auditoría")

# Archivo de seguimiento
ARCH_SEGUIMIENTO = os.getenv("ARCH_SEGUIMIENTO", "seguimiento_leads.csv")
if not os.access(".", os.W_OK):
    ARCH_SEGUIMIENTO = "/tmp/seguimiento_leads.csv"

def clasificar_con_ia(email_data):
    """
    Usa Gemini para clasificar el email según los criterios del auditor.
    """
    prompt = f"""
    Eres un asistente experto para un auditor en España. Tu objetivo es clasificar el interés de un cliente potential.
    
    Remitente: {email_data['remitente']}
    Asunto: {email_data['asunto']}
    Cuerpo: {email_data['cuerpo']}
    
    Criterios de clasificación ESTRICTOS:
    1) "Lead bueno" (prioridad alta): Cualquier solicitud de auditoría, revisión, consultoría ISO, presupuestos, o contacto directo de empresa. NO importa si faltan datos técnicos, si es un cliente potencial real, es un lead bueno.
    2) "Lead dudoso" (prioridad media): Preguntas muy genéricas sobre el sector sin intención de contratación clara, o estudiantes.
    3) "No relevante" (prioridad baja): Spam obvio, ofertas de trabajo (CVs), publicidad, o insultos.
    
    Responde ÚNICAMENTE en formato JSON con estas llaves:
    "clasificacion": (Lead bueno / Lead dudoso / No relevante),
    "prioridad": (Alta / Media / Baja),
    "razon": (breve explicación de por qué lo has clasificado así)
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpiar la respuesta por si viene con markdown
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        resultado = json.loads(json_text)
        return resultado.get("clasificacion", "Lead dudoso"), resultado.get("prioridad", "Media"), resultado.get("razon", "")
    except Exception as e:
        error_msg = f"Error en IA: {str(e)}"
        print(error_msg)
        return "Lead dudoso", "Media", error_msg

def enviar_email_automatico(email_destino, nombre_cliente):
    """
    Envía la respuesta profesional predefinida.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Error: Credenciales SMTP no configuradas.")
        return False

    mensaje = MIMEMultipart()
    mensaje['From'] = SMTP_USER
    mensaje['To'] = email_destino
    mensaje['Subject'] = "Re: Solicitud de información - Auditoría"

    cuerpo_texto = f"""
Hola {nombre_cliente},
Gracias por contactar.
Para poder orientarle correctamente, ¿podría indicarnos:

- Tipo de empresa y sector
- Qué necesita exactamente (auditoría, revisión, due diligence, etc.)
- Plazo o fecha objetivo

En cuanto lo tengamos, le proponemos una llamada breve.
Un saludo,
{AUDITOR_NAME}
"""
    mensaje.attach(MIMEText(cuerpo_texto, 'plain'))

    try:
        # Añadimos un timeout de 10 segundos para evitar que el servidor se cuelgue
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(mensaje)
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

def registrar_lead(email_data, clasificacion, prioridad, razon):
    if clasificacion == "No relevante":
        return

    try:
        file_exists = os.path.isfile(ARCH_SEGUIMIENTO)
        with open(ARCH_SEGUIMIENTO, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Fecha", "Nombre", "Email", "Asunto", "Clasificación", "Prioridad", "Razón", "Estatus", "Email Enviado"])
            
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                email_data['remitente'],
                email_data['email'],
                email_data['asunto'],
                clasificacion,
                prioridad,
                razon,
                "Pendiente",
                "Sí" if clasificacion == "Lead bueno" else "No"
            ])
    except Exception as e:
        print(f"Advertencia: No se pudo registrar el lead en el CSV: {e}")

def procesar_nuevo_contacto(email_data):
    """
    Función principal para procesar un contacto individual.
    Retorna un diccionario con todo el detalle del proceso.
    """
    print(f"Procesando contacto de: {email_data['remitente']}...")
    
    clasificacion, prioridad, razon = clasificar_con_ia(email_data)
    print(f"Resultado: {clasificacion} ({prioridad})")
    
    envio_intentado = False
    envio_exitoso = False
    if clasificacion == "Lead bueno":
        envio_intentado = True
        envio_exitoso = enviar_email_automatico(email_data['email'], email_data['remitente'])
        if envio_exitoso:
            print("Correo de respuesta enviado con éxito.")
        else:
            print("Fallo en el envío del correo automático.")
    
    registrar_lead(email_data, clasificacion, prioridad, razon)
    
    return {
        "clasificacion": clasificacion,
        "prioridad": prioridad,
        "razon": razon,
        "email_enviado": envio_exitoso,
        "email_intentado": envio_intentado
    }

if __name__ == "__main__":
    # Prueba rápida con un lead bueno
    test_contact = {
        "remitente": "Empresa Test SA",
        "email": "test@empresa.com",
        "asunto": "Auditoría obligatoria urgente",
        "cuerpo": "Hola, necesitamos auditar nuestras cuentas de 2025 de forma urgente. Gracias."
    }
    procesar_nuevo_contacto(test_contact)

