import sys
import subprocess
import os
from fpdf import FPDF

# Intentar importar fpdf2, si no, instalarlo
try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF

class AthleteFlyerPDF(FPDF):
    def header(self):
        # Fondo decorativo del encabezado (Azul marino profundo)
        self.set_fill_color(10, 25, 47)
        self.rect(0, 0, 210, 40, 'F')
        
        # Título en el encabezado
        self.set_y(10)
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(57, 180, 20)  # Verde Volt
        self.cell(0, 10, 'IMED PREDICTOR', border=0, ln=1, align='C')
        
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, 'NEURO-RENDIMIENTO Y PREVENCIÓN DE LESIONES DE ÉLITE', border=0, ln=1, align='C')

    def footer(self):
        # Footer decorativo
        self.set_y(-25)
        self.set_fill_color(10, 25, 47)
        self.rect(0, 272, 210, 25, 'F')
        
        self.set_y(-18)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(57, 180, 20)
        self.cell(0, 5, '¡ESCUCHA A TU CEREBRO, DOMINA TU JUEGO!', border=0, ln=1, align='C')
        
        self.set_font('Helvetica', 'I', 7.5)
        self.set_text_color(200, 200, 200)
        self.cell(0, 4, 'Plataforma oficial de rendimiento neuromuscular para deportistas de alto rendimiento', border=0, ln=1, align='C')

def generate_flyer():
    pdf = AthleteFlyerPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # -------------------------------------------------------------------------
    # EL GANCHO / HOOK (Caja de texto destacada en celeste claro)
    # -------------------------------------------------------------------------
    pdf.set_fill_color(240, 248, 255)  # Celeste muy claro
    pdf.rect(10, 48, 190, 30, 'F')
    
    pdf.set_y(51)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(0, 5, '¿SABÍAS QUE EL CANSANCIO EMPIEZA EN TU CEREBRO, NO EN TUS MÚSCULOS?', ln=1, align='C')
    pdf.ln(1)
    
    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 4.5, 
        'Antes de que sientas fatiga física o dolor en tus piernas, tu Sistema Nervioso Central (SNC) ya '
        'comienza a emitir impulsos más lentos. Entrenar a máxima intensidad con un cerebro fatigado '
        'provoca desbalance motor, menor fuerza y aumenta drásticamente tu riesgo de lesiones musculares. '
        'IMED PREDICTOR mide tu frescura neural a diario para protegerte.',
        align='C'
    )
    
    # -------------------------------------------------------------------------
    # SECCIÓN 1: ¿CÓMO FUNCIONA? (La rutina de 2 minutos)
    # -------------------------------------------------------------------------
    pdf.set_y(86)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 6, 'TU RUTINA DIARIA EN SOLO 2 MINUTOS', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Dos columnas para los pasos
    y_pasos = pdf.get_y()
    
    # Paso A
    pdf.set_xy(10, y_pasos)
    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(90, 5, 'Paso A: Cuestionario de Bienestar', ln=1)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(70, 70, 70)
    pdf.set_x(10)
    pdf.multi_cell(90, 4, 
        'Al despertar, califica con honestidad tus hábitos diarios en la app: horas y calidad de sueño, '
        'estrés y fatiga percibida. Esto entrega el contexto crucial sobre tu estado físico.', 
        border=0
    )
    
    # Paso B
    pdf.set_xy(105, y_pasos)
    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(95, 5, 'Paso B: Test de Reflejos PVT-B', ln=1)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(70, 70, 70)
    pdf.set_x(105)
    pdf.multi_cell(95, 4, 
        'Realiza la prueba rápida de 30 toques en tu celular. Presiona la pantalla lo más rápido posible '
        'cuando aparezca el contador de milisegundos. Evita las anticipaciones para cuidar tu dato.',
        border=0
    )
    
    # -------------------------------------------------------------------------
    # SECCIÓN 2: BENEFICIOS CLAVE
    # -------------------------------------------------------------------------
    pdf.set_xy(10, 132)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 6, '¿QUÉ BENEFICIOS LOGRAS PARA TU RENDIMIENTO?', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Beneficio 1
    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(0, 5, '1. PREVENCIÓN REAL DE LESIONES MUSCULARES', ln=1)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4, 
        'El sistema detecta la fatiga central encubierta (antes de que sientas cansancio). Si tus reflejos '
        'están lentos, el preparador físico ajustará la carga de tus ejercicios para proteger tus '
        'músculos y articulaciones, evitando desgarros y sobrecargas.')
    pdf.ln(3)
    
    # Beneficio 2
    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(0, 5, '2. ENTRENA EN TU ZONA ÓPTIMA (SUPERCOMPENSACIÓN)', ln=1)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4, 
        'Cuando el semáforo de tu celular está en Verde (Adaptación Óptima), es el momento de empujar '
        'tus límites. Entrenarás fuerte cuando tu cuerpo esté 100% receptivo para asimilar la carga.')
    pdf.ln(3)
    
    # Beneficio 3
    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(0, 5, '3. APOYO DIARIO DE TU PSICÓLOGO DEPORTIVO', ln=1)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4, 
        'A diferencia de otras aplicaciones, tus datos no se quedan en el aire. Tu psicólogo deportivo '
        'monitorea tu curva atencional avanzada y te entregará feedback diario con técnicas de relajación, '
        'concentración y consejos personalizados de higiene del sueño para acelerar tu recuperación.')
    
    # -------------------------------------------------------------------------
    # SECCIÓN 3: LLAMADO A LA ACCIÓN (Caja de color Verde Volt oscuro)
    # -------------------------------------------------------------------------
    pdf.set_xy(10, 228)
    pdf.set_fill_color(57, 180, 20)  # Verde Volt oscuro
    pdf.rect(10, pdf.get_y(), 190, 24, 'F')
    
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 6, '¡TU CEREBRO GUÍA TU CUERPO! HAZ EL TEST MAÑANA AL DESPERTAR', ln=1, align='C')
    pdf.ln(1)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(0, 5, 'Abre tu aplicación IMED PREDICTOR, responde tu Wellness y haz tu test. ¡Solo toma 2 minutos!', ln=1, align='C')
    
    # Salvar PDF
    pdf.output('c:/Users/Pato/Desktop/proyectos/IMED PREDICTOR/Flyer_Deportista_IMED_PREDICTOR.pdf')
    print("¡Flyer para Atletas IMED PREDICTOR Generado con éxito!")

if __name__ == '__main__':
    generate_flyer()
