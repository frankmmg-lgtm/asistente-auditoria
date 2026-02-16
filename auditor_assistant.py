import json
import csv
import os
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# Configurar Gemini
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Configuración de Correo
# En Resend, el Remitente debe estar verificado. 
# Si no tienes dominio, usa: "onboarding@resend.dev"
SMTP_USER = os.getenv("SMTP_USER", "onboarding@resend.dev")
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
        full_error = str(e)
        print(f"Error en IA: {full_error}")
        # Si es un error de cuota (429), damos un mensaje más amigable
        if "429" in full_error:
            razon_amigable = "Límite de mensajes temporales alcanzado (Cortesía de Google). Procesando como lead importante por defecto."
        else:
            # Recortamos otros errores
            razon_amigable = full_error[:100] + "..." if len(full_error) > 100 else full_error
        
        return "Lead bueno", "Alta", razon_amigable

def enviar_email_automatico(email_destino, nombre_cliente):
    """
    Envía la respuesta profesional predefinida usando la API de Resend.
    """
    if not RESEND_API_KEY:
        error_msg = "Error: RESEND_API_KEY no configurada en el servidor."
        print(error_msg)
        return False, error_msg

    cuerpo_texto = f"""
Hola {nombre_cliente},

Gracias por contactar con nosotros.

Para poder orientarle correctamente, ¿podría indicarnos:
- Tipo de empresa y sector
- Qué necesita exactamente (auditoría, revisión, etc.)
- Plazo o fecha objetivo

En cuanto recibamos estos datos, le propondremos una llamada breve para profundizar.

Un saludo cordial,
{AUDITOR_NAME}
"""

    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": f"{AUDITOR_NAME} <{SMTP_USER}>",
            "to": [email_destino], # Resend acepta una lista
            "subject": "Re: Solicitud de información - Auditoría",
            "text": cuerpo_texto
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            return True, ""
        else:
            error_data = response.json()
            error_msg = f"Error Resend ({response.status_code}): {error_data.get('message', 'Desconocido')}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error de Conexión API: {str(e)}"
        print(error_msg)
        return False, error_msg

def registrar_lead(email_data, clasificacion, prioridad, razon, email_error=None):
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
    error_email = ""
    if clasificacion == "Lead bueno":
        envio_intentado = True
        envio_exitoso, error_email = enviar_email_automatico(email_data['email'], email_data['remitente'])
        if envio_exitoso:
            print("Correo de respuesta enviado con éxito.")
        else:
            print(f"Fallo en el envío: {error_email}")
    
    registrar_lead(email_data, clasificacion, prioridad, razon, error_email)
    
    return {
        "clasificacion": clasificacion,
        "prioridad": prioridad,
        "razon": razon,
        "email_enviado": envio_exitoso,
        "email_intentado": envio_intentado,
        "email_error": error_email
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

