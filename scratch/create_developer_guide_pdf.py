import sys
import subprocess
import os

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF

class DeveloperGuidePDF(FPDF):
    def header(self):
        # Header premium para el desarrollador
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(0, 119, 255)  # Azul Premium
        self.cell(0, 10, 'IMED PREDICTOR - MANUAL DE INDUCCION PARA DESARROLLADORES Y EDITORES', border=0, ln=1, align='L')
        self.set_draw_color(0, 119, 255)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        # Footer
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Dossier Técnico IMED PREDICTOR v4.0', align='C')

def generate_pdf():
    pdf = DeveloperGuidePDF()
    pdf.alias_nb_pages()
    
    # -------------------------------------------------------------------------
    # PORTADA
    # -------------------------------------------------------------------------
    pdf.add_page()
    
    # Intentar colocar el logo
    logo_path = 'assets/logo.png'
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=85, y=40, w=40)
        pdf.ln(60)
    else:
        pdf.ln(30)
        
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(10, 12, 15)  # Fondo oscuro elegante
    
    # Rellenar fondo de portada
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Volver a escribir logo para portada oscura
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=85, y=50, w=40)
        
    pdf.set_y(110)
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(0, 229, 255)  # Cyan
    pdf.cell(0, 15, 'IMED PREDICTOR v4.0', ln=1, align='C')
    
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, 'Dossier de Inducción Técnica', ln=1, align='C')
    pdf.cell(0, 10, 'Arquitectura de Software y Guía de Despliegue', ln=1, align='C')
    
    pdf.ln(30)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(161, 161, 170)
    pdf.cell(0, 8, 'Preparado para: Equipo de Desarrollo y Editores', ln=1, align='C')
    pdf.cell(0, 8, 'Plataforma: Mobile App (Flutter) + Backend Serverless (GCP/Firebase) + Dashboard Web', ln=1, align='C')
    pdf.cell(0, 8, 'Fecha de Actualización: Julio de 2026', ln=1, align='C')
    
    # -------------------------------------------------------------------------
    # PAGINA 2: RESUMEN DE LA ARQUITECTURA
    # -------------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 119, 255)
    pdf.cell(0, 10, '1. Resumen Ejecutivo y Arquitectura del Sistema', ln=1)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(30, 30, 30)
    
    intro_text = (
        "IMED Predictor es una plataforma clínica de telemetría y prevención de lesiones diseñada para "
        "atletas de alto rendimiento. El ecosistema está diseñado bajo un enfoque Serverless (Sin Servidor) "
        "y modular para maximizar la escalabilidad, la velocidad de cómputo de Z-Scores y mitigar costos. "
        "La arquitectura consta de tres capas principales fuertemente desacopladas, comunicadas a través de "
        "Google Cloud Firebase:"
    )
    pdf.multi_cell(0, 6, intro_text)
    pdf.ln(4)
    
    # Listado de capas
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'A. Aplicación Móvil (Athlete HUD - Flutter)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    app_text = (
        "Construida con Flutter SDK (Dart) versión >=3.0.0. Utiliza Isar Database y Hive para almacenamiento "
        "local offline-first (permite registrar Wellness y PVT sin internet). La app móvil se conecta a "
        "Google Firestore de manera transparente para subir datos clínicos enriquecidos."
    )
    pdf.multi_cell(0, 6, app_text)
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'B. Backend Serverless (GCP Cloud Functions - Python 3.13)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    back_text = (
        "Ubicado en la carpeta /functions. Consiste en microservicios en la nube basados en triggers de "
        "Firestore e interfaces HTTP. Desarrollado en Python, utiliza Pandas, Numpy y Scipy (L-BFGS-B) "
        "para modelar la distribución Ex-Gaussiana de fatiga neuro-motora y el Índice de Vulnerabilidad (IVN). "
        "El Admin SDK se utiliza para evadir las reglas de Firestore de manera interna y asegurar operaciones idempotentes."
    )
    pdf.multi_cell(0, 6, back_text)
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'C. Dashboard Web (SaaS - HTML5 / Vanilla CSS / JS SDK v9)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    dash_text = (
        "Ubicado en la carpeta /public. Interfaz de analítica clínica con diseño glassmorphism de alto "
        "impacto visual (Elite Dark Mode) construida en JavaScript nativo. Se comunica en tiempo real con "
        "Firestore a través de Listeners reactivos (onSnapshot) para reflejar las métricas de los atletas sin refrescar."
    )
    pdf.multi_cell(0, 6, dash_text)
    
    # -------------------------------------------------------------------------
    # PAGINA 3: GUIA DE GESTIÓN Y SERVIDORES (FIREBASE Y GITHUB)
    # -------------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 119, 255)
    pdf.cell(0, 10, '2. Servidores, Base de Datos y Control de Versiones', ln=1)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Google Firebase (Proyecto: app-imed-sport)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    fb_text = (
        "Toda la infraestructura cloud está alojada en Firebase bajo el ID de proyecto 'app-imed-sport'.\n"
        "- Base de Datos (Cloud Firestore): Repositorio NoSQL. Alberga las colecciones /athletes (perfiles y "
        "mediciones), /Daily_Performance (KPIs procesados por día), /tenants (inquilinos del SaaS) y /clinical_notes.\n"
        "- Autenticación (Firebase Auth): Gestión de cuentas de entrenadores y psicólogos. Utiliza Custom Claims "
        "en el token JWT para almacenar de manera segura el rol ('SUPER_ADMIN', 'PSICOLOGO', 'COACH') y el 'tenantId'.\n"
        "- Hosting: Sirve el frontend web desde la carpeta public/ en la dirección https://app-imed-sport.web.app."
    )
    pdf.multi_cell(0, 6, fb_text)
    pdf.ln(4)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Control de Versiones (GitHub)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    gh_text = (
        "El repositorio maestro está alojado en GitHub en la siguiente ruta:\n"
        "https://github.com/pspatriciorubilar-afk/IMED-PREDICTOR\n"
        "Flujo de trabajo: La rama principal de producción es 'main'. Al empujar cambios a esta rama, "
        "se consolidan las actualizaciones. Para pruebas locales, el programador debe configurar las "
        "credenciales en la raíz y carpetas de funciones."
    )
    pdf.multi_cell(0, 6, gh_text)
    pdf.ln(4)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Seguridad y Credenciales (serviceAccount.json)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    sa_text = (
        "Por motivos de seguridad, las llaves de acceso administrativo no se suben a GitHub (están en .gitignore).\n"
        "El programador debe recibir de forma externa el archivo de credenciales de Google Service Account y "
        "ubicarlo en: functions/serviceAccount.json. Esto le permitirá ejecutar scripts en local (/scratch) "
        "y conectarse como administrador a la base de datos Firestore de producción."
    )
    pdf.multi_cell(0, 6, sa_text)

    # -------------------------------------------------------------------------
    # PAGINA 4: FUNCIONALIDADES MULTI-TENANT (SPRINT 4)
    # -------------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 119, 255)
    pdf.cell(0, 10, '3. Lógica Multi-Inquilino (SaaS) y Reglas de Seguridad', ln=1)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(30, 30, 30)
    mt_intro = (
        "Durante el Sprint 4, la plataforma migró a un modelo SaaS multi-inquilino (Multi-Tenant). Esto permite "
        "que cada club u organización deportiva opere de forma 100% aislada, viendo únicamente a sus propios "
        "deportistas y entrenadores."
    )
    pdf.multi_cell(0, 6, mt_intro)
    pdf.ln(4)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'A. Aislamiento en Firestore Rules (firestore.rules)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    rules_explanation = (
        "Se implementó el helper getTenantId() que extrae el inquilino del usuario logueado desde su token.\n"
        "- Lectura de Atletas y Rendimiento: Restringida mediante belongsToTenant(resource.data.tenantId). Un coach "
        "de un club no puede consultar atletas de otro club.\n"
        "- Escritura de Atletas: Permitida de forma anónima para la app móvil de telemetría (para evitar fricción "
        "de logueo en deportistas), y restringida por tenantId para usuarios autenticados.\n"
        "- Notas Clínicas: Aisladas de forma estricta por psicólogo creador (psychologist_uid) y por inquilino."
    )
    pdf.multi_cell(0, 6, rules_explanation)
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'B. Gestión de Usuarios y Roles en Cloud Functions', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    functions_explanation = (
        "Las Cloud Functions de administración de usuarios en functions/main.py se adaptaron al multi-tenant:\n"
        "- list_dashboard_users: Si el llamador es un psicólogo (Admin de Club), solo se listan los usuarios creados "
        "con su mismo tenantId. El SuperAdmin puede ver todos de forma global.\n"
        "- create_dashboard_user: Copia de forma automática el tenantId del creador al token claim del nuevo "
        "usuario (ej: cuando un psicólogo da de alta a un preparador físico de su mismo club).\n"
        "- delete_dashboard_user y update_dashboard_user_team: Protegidas para validar pertenencia al tenant."
    )
    pdf.multi_cell(0, 6, functions_explanation)
    
    # -------------------------------------------------------------------------
    # PAGINA 5: LOGICA EN LA APP MOVIL Y FLUX DE DESPLIEGUE
    # -------------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 119, 255)
    pdf.cell(0, 10, '4. Código de Asociación en la App Móvil y Guía de Deploy', ln=1)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Flujo de Asociación en la App Móvil (Flutter)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    app_flow = (
        "1. Al registrarse en la pantalla de Onboarding de la app móvil, el deportista debe ingresar el "
        "Código Maestro de su club (ej: 'COLO26').\n"
        "2. La app busca online ese código en la colección de /tenants de Firestore. Si el código es válido, "
        "obtiene el tenantId y lo guarda en su base de datos Isar local junto a sus datos.\n"
        "3. Si está offline, guarda localmente el código para resolver el tenantId apenas recupere conexión.\n"
        "4. Al realizar mediciones, el sync_service.dart escribe el tenantId tanto en el documento del atleta "
        "como en Daily_Performance, lo que permite que el backend serverless lo procese y se muestre en el "
        "dashboard correspondiente."
    )
    pdf.multi_cell(0, 6, app_flow)
    pdf.ln(4)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Comandos de Despliegue en Producción (Firebase CLI)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    deploy_cmds = (
        "- Desplegar Cloud Functions del Backend:\n"
        "  firebase deploy --only functions\n"
        "- Desplegar Frontend Web (Hosting) y Reglas de Base de Datos:\n"
        "  firebase deploy --only hosting,firestore:rules\n"
        "- Compilar APK de la App Móvil en versión de producción libre de errores:\n"
        "  flutter build apk --release\n"
        "  (Ubicación del APK: build/app/outputs/flutter-apk/app-release.apk)"
    )
    pdf.multi_cell(0, 6, deploy_cmds)
    pdf.ln(5)
    
    # Mensaje final
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0, 119, 255)
    pdf.cell(0, 8, 'Ecosistema IMED Predictor 2026 - Listo para producción multi-inquilino.', ln=1, align='C')

    # Guardar en raíz del proyecto
    pdf.output('Guia_Desarrollador_IMED_SNC.pdf')
    print("PDF generado exitosamente en: Guia_Desarrollador_IMED_SNC.pdf")

if __name__ == '__main__':
    generate_pdf()
