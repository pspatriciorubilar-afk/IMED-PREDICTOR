import sys
import subprocess
import os

# Intentar importar fpdf2, si no, instalarlo
try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF

class AthleteGuidePDF(FPDF):
    def header(self):
        # Header premium para el deportista
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(57, 180, 20)  # Verde Volt oscuro
        self.cell(0, 10, 'IMED PREDICTOR - MANUAL DE NEURO-RENDIMIENTO DEPORTIVO', border=0, ln=1, align='L')
        self.set_draw_color(57, 180, 20)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        # Footer
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Manual del Deportista IMED PREDICTOR v3.0', align='C')

def generate_pdf():
    pdf = AthleteGuidePDF()
    pdf.alias_nb_pages()
    
    # -------------------------------------------------------------------------
    # PORTADA
    # -------------------------------------------------------------------------
    pdf.add_page()
    
    # Intentar colocar el logo
    logo_path = 'assets/logo.png'
    if os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=85, y=35, w=40)
            pdf.ln(50)
        except Exception:
            pdf.ln(20)
    else:
        pdf.ln(20)

    # Título de Portada
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 15, 'MANUAL DEL DEPORTISTA', ln=1, align='C')
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(57, 180, 20)  # Verde Volt oscuro
    pdf.cell(0, 10, 'Ecosistema de Rendimiento Deportivo IMED PREDICTOR', ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, 
        'Bienvenido a tu manual de usuario. Esta guía está diseñada para enseñarte cómo usar la '
        'aplicación móvil IMED PREDICTOR, responder correctamente el cuestionario de bienestar (Wellness), '
        'realizar el test de atención PVT y entender cómo tus resultados impactan directamente en tu '
        'rendimiento deportivo y en la prevención de lesiones.', 
        align='C'
    )
    pdf.ln(15)

    # Nota de Importancia
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 6, '¿POR QUÉ USAMOS IMED PREDICTOR?', ln=1, align='C')
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, 
        '"El rendimiento de tus músculos depende de la frescura de tu cerebro. '
        'Al medir tu fatiga central, ayudamos a que tu cuerpo técnico programe la dosis '
        'exacta de carga de entrenamiento para mantenerte en tu zona óptima de rendimiento y lejos de las lesiones."',
        align='C'
    )

    # -------------------------------------------------------------------------
    # PAGINA 2: INTRODUCCIÓN AL SISTEMA
    # -------------------------------------------------------------------------
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, 'Introducción al Sistema IMED PREDICTOR', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # 1. ¿Qué es?
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, '1. ¿Qué es IMED PREDICTOR?', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Es un ecosistema de rendimiento deportivo de élite diseñado para monitorear y predecir '
        'el estado de preparación neuromuscular y la fatiga del Sistema Nervioso Central (SNC). '
        'El sistema integra valoraciones diarias de tu estado mental y físico para proporcionar un '
        'análisis en tiempo real de tu disposición biológica antes del entrenamiento.')
    pdf.ln(5)

    # 2. ¿Qué medimos?
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, '2. ¿Qué medimos?', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Medimos dos dimensiones críticas del deportista de manera diaria:\n'
        '- Carga interna subjetiva mediante el cuestionario de bienestar (Wellness), registrando horas de sueño, '
        'calidad del descanso, nivel de estrés percibido y fatiga física.\n'
        '- Fatiga central y atención de manera objetiva mediante una prueba de tiempo de reacción rápida '
        'de 30 ensayos.')
    pdf.ln(5)

    # 3. ¿Qué ciencia utilizamos?
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, '3. ¿Qué ciencia utilizamos?', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Utilizamos la Tarea de Vigilancia Psicomotora (PVT-B), el estándar científico de referencia '
        '(Gold Standard) en la medicina del deporte y del sueño para evaluar la fatiga central. Los '
        'datos de tiempo de reacción se analizan mediante el algoritmo Ex-Gaussiano para separar de '
        'forma precisa tu velocidad física (mu) de tu cansancio cognitivo cerebral (tau).')
    pdf.ln(5)

    # 4. ¿Cuál es la utilidad de hacerlo a diario?
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, '4. ¿Cuál es la utilidad de medirlo a diario?', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'La utilidad clave es establecer tu perfil neurológico y físico personalizado. Al medirte todos '
        'los días al despertar, creamos tu línea base individual. Esto le permite al cuerpo técnico '
        'dosificar con precisión la carga de tus entrenamientos, evitar sobrecargas del sistema nervioso, '
        'prevenir lesiones musculares y asegurar que compitas siempre en tu máximo estado de rendimiento.')

    # -------------------------------------------------------------------------
    # PAGINA 3: LA RUTINA DIARIA (PASO A PASO)
    # -------------------------------------------------------------------------
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, '1. Tu Rutina Diaria: Paso a Paso', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5.5, 
        'Debes realizar esta rutina todos los días por la mañana, idealmente antes del desayuno y antes de '
        'iniciar cualquier actividad física de alta intensidad. Esto nos dará tu línea base de rendimiento del '
        'sistema nervioso sin interferencias de fatiga acumulada durante el día.')
    pdf.ln(4)

    # A. Wellness
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'Paso A: El Cuestionario de Bienestar (Wellness Survey)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Responde con total honestidad. No intentes "adivinar" lo que el preparador físico quiere ver; el objetivo '
        'es registrar tu estado biológico real. La aplicación te pedirá calificar:\n'
        '- Horas de Sueño: Cuántas horas dormiste de forma efectiva.\n'
        '- Calidad de Sueño (1-5): Siendo 1 una noche de insomnio o interrupciones y 5 un descanso profundo y reparador.\n'
        '- Nivel de Estrés (1-5): Siendo 1 libre de estrés y 5 un nivel de estrés o preocupaciones muy alto.\n'
        '- Fatiga General (1-5): Siendo 1 sin fatiga muscular y 5 un cansancio físico extremo (ejemplo: post-partido o entrenamiento de alta carga).')
    pdf.ln(4)

    # B. Test PVT
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'Paso B: La Prueba de Vigilancia Psicomotora (Test PVT-B)', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Esta prueba mide de forma científica tu tiempo de reacción cerebral (en milisegundos). Consta de 30 estímulos '
        'visuales en tu pantalla.\n\n'
        'Instrucciones de oro para realizar el Test:\n'
        '1. Entorno sin distracciones: Haz la prueba en un lugar silencioso. Apaga televisores o música.\n'
        '2. Sujeta tu teléfono cómodamente: Usa tu mano dominante o la posición en la que tu dedo pulgar reaccione de forma más natural.\n'
        '3. Reacciona al instante: En cuanto veas aparecer el contador numérico de milisegundos en tu pantalla, presiónalo lo más rápido posible.\n'
        '4. Evita falsas anticipaciones: Si presionas la pantalla antes de que aparezca el número, contará como una "anticipación" (falso inicio), lo cual penalizará la higiene del dato.')
    pdf.ln(8)

    # -------------------------------------------------------------------------
    # PAGINA 4: INTERPRETACIÓN DE LA PANTALLA
    # -------------------------------------------------------------------------
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, '2. Cómo Interpretar tus Resultados en el Teléfono', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5.5, 
        'Al terminar tu prueba PVT y tu cuestionario de Wellness, la aplicación procesará instantáneamente tus datos y te '
        'llevará al panel de control de Telemetría de Rendimiento. Verás la siguiente información en pantalla:')
    pdf.ln(4)

    # Anillo de Readiness
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'A. El Anillo de Readiness (Disponibilidad Deportiva):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Es tu puntuación global del día (de 0 a 100). Viene acompañado de un color de semáforo que te indica tu estado:\n'
        '- VERDE (Óptimo - Score >= 85): Tu sistema nervioso está fresco. ¡Listo para entrenar a máxima intensidad!\n'
        '- AMARILLO (Precaución - Score 70-84): Hay una leve fatiga en desarrollo. Entrena con atención y cuida el volumen de carga.\n'
        '- NARANJA (Fatiga - Score 50-69): Fatiga central detectada. Se sugiere atenuar la precisión neuromuscular y evitar ejercicios explosivos.\n'
        '- ROJO (Crítico - Score < 50): Agotamiento agudo. Tu SNC no está respondiendo a tiempo. Se sugiere priorizar la recuperación activa y descanso.')
    pdf.ln(3)

    # Análisis de Hábitos
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'B. Bloque de "Análisis de Hábitos" (Insights):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Aquí leerás un párrafo explicativo que traduce tus números a consejos sencillos de rendimiento. Por ejemplo, te indicará si tu '
        'degradación de atención de hoy fue causada por haber dormido pocas horas la noche anterior, o si estás experimentando '
        'estrés cognitivo acumulado.')
    pdf.ln(3)

    # Gráfico de Tendencia
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'C. Gráfica de Tendencia de Latencia (Últimos 7 días):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Te muestra el histórico de tus tiempos de reacción de la semana (desde el Día 1 al Día 7). Te sirve para evaluar si tus hábitos '
        'diarios (sueño, recuperación, nutrición) están ayudándote a estabilizar tus reflejos a lo largo de los microciclos de carga.')
    pdf.ln(8)

    # -------------------------------------------------------------------------
    # PAGINA 5: PSICÓLOGO DEPORTIVO Y EX-GAUSSIANO
    # -------------------------------------------------------------------------
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, '3. Tu Psicólogo Deportivo y la Ciencia Detrás de tus Datos', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Psicólogo Deportivo
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'El Rol de tu Psicólogo Deportivo:', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Mientras tú ves un semáforo fácil de interpretar en tu teléfono, en paralelo tu psicólogo deportivo estará '
        'monitoreando de cerca la telemetría avanzada de tu rendimiento neuromuscular. El especialista analizará los desvíos '
        'de tus datos y se comunicará contigo de forma diaria para entregarte retroalimentación, estrategias de manejo '
        'de estrés, técnicas de concentración y pautas de descanso personalizadas.')
    pdf.ln(4)

    # Ex-Gaussian
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'El Algoritmo Ex-Gaussiano Explicado Fácil:', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'Tu test de 30 estímulos genera una curva de reflejos. El sistema utiliza el algoritmo científico "Ex-Gaussiano" '
        'para separar tu rendimiento en tres partes transparentes:\n'
        '1. mu (Velocidad Motora): Representa tus reflejos musculares y velocidad física base en óptimo estado.\n'
        '2. sigma (Consistencia): Mide la variabilidad. Te dice qué tan estable mantienes el enfoque durante el test.\n'
        '3. tau (Fatiga Central): Mide los micro-lapsos atencionales. Representa esos milisegundos donde tu cerebro se '
        'desconecta por cansancio del Sistema Nervioso Central (SNC) antes de que tú lo notes físicamente.')
    pdf.ln(4)

    # Precisión Científica
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, '¿Cómo te ayuda la precisión de este algoritmo?', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 
        'La precisión científica de este algoritmo es vital para monitorear tu fatiga central de forma preventiva. Al separar '
        'tu velocidad física (mu) de tu cansancio cerebral (tau), tu psicólogo deportivo y tu entrenador pueden saber si '
        'estás experimentando sobrecarga del sistema nervioso (lo que requiere recuperación mental) o si es solo fatiga '
        'muscular en tus piernas. Esto garantiza entrenamientos más seguros, precisos y personalizados, maximizando tu '
        'vida útil deportiva.')

    # Salvar PDF
    pdf.output('c:/Users/Pato/Desktop/proyectos/IMED PREDICTOR/Manual_Deportista_IMED_SNC.pdf')
    print("¡Manual del Deportista PDF IMED PREDICTOR Generado con éxito!")

if __name__ == '__main__':
    generate_pdf()
