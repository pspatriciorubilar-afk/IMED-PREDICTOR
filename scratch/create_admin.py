"""
Crear usuario admin inicial
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))

from firebase_admin import credentials, initialize_app, auth

# Initialize with explicitly found credential file
cred = credentials.Certificate('C:\\Users\\Pato\\Desktop\\proyectos\\IMED PREDICTOR\\functions\\app-imed-sport-firebase-adminsdk-v4m2w-81f1853ec7.json')
try:
    initialize_app(cred)
except ValueError:
    pass # App already initialized

email = "patricio@imedpredictor.com"
password = "AdminImed2026!"

try:
    user = auth.create_user(email=email, password=password)
    auth.set_custom_user_claims(user.uid, {'role': 'ADMIN'})
    print(f"Usuario {email} creado exitosamente con rol ADMIN.")
except Exception as e:
    # Si el usuario ya existe, actualizar su rol
    try:
        user = auth.get_user_by_email(email)
        auth.set_custom_user_claims(user.uid, {'role': 'ADMIN'})
        print(f"Usuario {email} ya existía. Se actualizó su rol a ADMIN.")
    except Exception as inner_e:
        print(f"Error: {e}")
        print(f"Inner Error: {inner_e}")
