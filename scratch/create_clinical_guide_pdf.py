import sys
import subprocess

# Intentar importar fpdf2, si no, instalarlo
try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF

class ClinicalGuidePDF(FPDF):
    def header(self):
        # Header premium
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(0, 200, 220)  # Cian
        self.cell(0, 10, 'IMED PREDICTOR - GUÍA PASO A PASO DE INTERPRETACIÓN NEUROMUSCULAR', border=0, ln=1, align='L')
        self.set_draw_color(0, 200, 220)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        # Footer
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - IMED PREDICTOR Manual de Usuario', align='C')

def generate_pdf():
    pdf = ClinicalGuidePDF()
    pdf.alias_nb_pages()
    
    # -------------------------------------------------------------------------
    # PAGINA 1: PANTALLA PRINCIPAL (DASHBOARD)
    # -------------------------------------------------------------------------
    pdf.add_page()
    
    # Título del Documento
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, 'MANUAL DE INTERPRETACIÓN PASO A PASO', ln=1, align='L')
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, 'Guía de Navegación por las Pantallas y Métricas de IMED PREDICTOR', ln=1)
    pdf.ln(8)

    # Sección 1: Pantalla Principal
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, 'PANTALLA 1: DASHBOARD DE PREDICCIÓN (PANEL PRINCIPAL)', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, 'En tu pantalla principal verás el estado global de tu plantilla en tiempo real. Está diseñada para darte una alerta visual rápida antes de comenzar cualquier sesión de entrenamiento.')
    pdf.ln(3)

    # Elemento A: Tarjetas superiores
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'A. Tarjetas de Resumen Superior (Contadores):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Indican la cantidad total de atletas en cada estado: "Riesgo Crítico" (Rojo), "Riesgo de Coordinación" (Amarillo) y "Adaptación Óptima" (Verde). Te ayuda a saber de un vistazo cuántos jugadores requieren modificaciones de carga hoy.')
    pdf.ln(3)

    # Elemento B: Semáforo de Riesgo
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'B. Panel de Alertas - Semáforo de Riesgo:', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Muestra la lista de tus atletas evaluados en el día con tres métricas básicas:\n'
                           '1. Score IRI: Nota de recuperación del 0 al 100 (SNC + Wellness).\n'
                           '2. Lapses: Cantidad de fallas atencionales severas (>500ms) durante la prueba.\n'
                           '3. Estado GPS: Indica si tiene cargada carga mecánica externa o si está en "Sin GPS".\n'
                           '4. Badge de Estado: Verde (Óptimo), Amarillo (Advertencia) o Rojo (Crítico).')
    pdf.ln(3)

    # Elemento C: Gráfico de Correlación
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'C. Gráfico de Correlación IRI vs Desaceleraciones:', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Este gráfico de dispersión cruza el Score IRI (eje X) con la Carga Mecánica (eje Y). Los puntos deben concentrarse en la zona verde derecha. Si un punto se desplaza hacia la izquierda e inferior/superior, muestra una alerta visual de que el atleta tiene baja resiliencia central para la carga física que está tolerando.')
    pdf.ln(5)

    # -------------------------------------------------------------------------
    # PAGINA 2: FICHA DETALLADA DEL ATLETA
    # -------------------------------------------------------------------------
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, 'PANTALLA 2: FICHA DETALLADA (ANÁLISIS NEURO-RENDIMIENTO)', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, 'Al hacer clic en "Ficha Completa" de cualquier atleta, se abre esta ventana emergente detallada. Estas métricas muestran la relación directa entre el cerebro y el cuerpo:')
    pdf.ln(3)

    # Tarjetas Principales
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'A. Tarjetas de Resumen Fisiológico:', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, '- IRI Score: Tu indicador global de recuperación.\n'
                           '- Lapses: Desconexiones cerebrales del día.\n'
                           '- Latencia Media: Tiempo de reacción promedio en milisegundos durante todo el test.\n'
                           '- Wellness Score: Nivel de bienestar reportado (calidad de sueño, estrés y fatiga física).')
    pdf.ln(3)

    # Bloque Ex-Gaussiano
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0, 100, 150)
    pdf.cell(0, 6, 'B. Sección: Análisis Ex-Gaussiano (Distribución Atencional):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Estas métricas separan con precisión matemática la capacidad de atención de la lentitud muscular:\n'
                           '- mu (Velocidad Motora): Velocidad de transmisión nerviosa pura. A menor número, mayor frescura física.\n'
                           '- sigma (Consistencia): Mide la variabilidad. Un valor alto indica que el foco del atleta es inestable.\n'
                           '- tau (Fatiga Central / Cola): Mide el agotamiento del SNC. Un valor elevado indica micro-lapsos.\n'
                           '- tau Z-Score y Wellness Z-Score: Muestran cuántas desviaciones estándar se desvía el atleta de su propia línea base histórica de 21 días. Si el Z-score de tau es mayor a 1.5, hay fatiga central.')
    pdf.ln(3)

    # Bloque Diagnóstico Integrado
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(150, 100, 0)
    pdf.cell(0, 6, 'C. Sección: Diagnóstico Integrado NA-GPS - Prescripción:', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Cruza la Disponibilidad Neural (NA) con el índice de Carga Mecánica (CM). El sistema te arroja aquí una "Prescripción Deportiva" escrita basada en el algoritmo (ejemplo: "Mantener cargas" o "Evitar desaceleraciones y saltos bruscos").')
    pdf.ln(5)

    # -------------------------------------------------------------------------
    # PAGINA 3: PANTALLA DE TENDENCIAS Y ACCION CLINICA
    # -------------------------------------------------------------------------
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, 'PANTALLA 3: MONITOREO SNC (GRÁFICOS DE TENDENCIAS)', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, 'Al ingresar al menú lateral en "Monitoreo SNC" verás las gráficas de comportamiento temporal. Se interpretan de esta manera:')
    pdf.ln(3)

    # Gráficas
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'A. Gráfica mu (Velocidad Motora Base):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Debe mantenerse plana o con variaciones leves. Un pico hacia arriba (incremento en ms) indica fatiga muscular acumulada en las extremidades.')
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'B. Gráfica sigma (Variabilidad Cognitiva):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Mide la estabilidad mental. Si la línea sube, el deportista está perdiendo la capacidad de mantener un foco constante.')
    pdf.ln(3)

    # Gráfica tau
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, 'C. Gráfica tau (Fatiga Central del SNC):', ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, 'Esta es la gráfica preventiva más importante. Si la línea asciende durante 3 o 4 días seguidos, el atleta está acumulando estrés en su sistema nervioso. Debes aplicar una sesión de descarga o descanso antes de que el semáforo general pase a Rojo.')
    pdf.ln(5)

    # Matriz de Acción
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 8, 'RESUMEN DE MEDIDAS PRÁCTICAS PARA EL ENTRENADOR', ln=1)
    pdf.set_draw_color(0, 120, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, '- Si tau está elevado (SNC Fatigado): Reducir volumen, evitar ejercicios de toma de decisiones rápidas o tácticas complejas. No realizar pliometría.\n'
                           '- Si mu está elevado (Músculo Fatigado): Reducir sprints o velocidad lineal. Trabajar flexibilidad y rodaje suave.\n'
                           '- Si ambos están elevados (Fatiga Aguda Mixta): Descanso total o sesión de fisioterapia.')

    # Salvar PDF
    pdf.output('c:/Users/Pato/Desktop/proyectos/IMED PREDICTOR/Guia_Clinica_IMED_SNC.pdf')
    print("¡Guía Clínica PDF IMED PREDICTOR Generada con éxito!")

if __name__ == '__main__':
    generate_pdf()
