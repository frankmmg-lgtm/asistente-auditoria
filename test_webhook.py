import requests
import json

# URL de nuestro servidor local (el que abres con run_server.bat)
URL = "http://localhost:5000/webhook"

# Simulamos un lead que llega desde el formulario de la web
# Este es un "Lead Bueno" para que genere respuesta automatica
datos_test = {
    "nombre": "Carlos Perez (Prueba)",
    "email": "frankmmg@gmail.com",  # Lo mando a tu mismo correo para la prueba
    "asunto": "Necesito auditoría urgente para mi empresa",
    "mensaje": "Hola, somos una empresa de logística en Madrid y necesitamos una auditoría obligatoria de cuentas para presentar en un mes. ¿Podéis darnos presupuesto? Gracias."
}

print(f"Enviando lead de prueba a {URL}...")

try:
    response = requests.post(URL, json=datos_test)
    if response.status_code == 200:
        print("\n[ÉXITO] El servidor ha procesado el lead.")
        print("Respuesta del servidor:", response.json())
        print("\n--- SIGUIENTES PASOS ---")
        print("1. Revisa la ventana negra del servidor (run_server.bat). Veras el progreso.")
        print("2. Revisa el archivo 'seguimiento_leads.csv' en tu carpeta IA.")
        print("3. ¡Revisa tu correo! Deberías haber recibido/enviado el mail automático.")
    else:
        print(f"\n[ERROR] El servidor respondió con código {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\n[ERROR] No se pudo conectar con el servidor.")
    print("Asegúrate de que 'run_server.bat' esté abierto y funcionando.")
    print("Error:", e)
