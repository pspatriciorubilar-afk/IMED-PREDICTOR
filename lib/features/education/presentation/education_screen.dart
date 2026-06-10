import 'package:flutter/material.dart';

class EducationScreen extends StatefulWidget {
  const EducationScreen({super.key});

  @override
  State<EducationScreen> createState() => _EducationScreenState();
}

class _EducationScreenState extends State<EducationScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  int _expandedIndex = -1;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF080810),
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) => [
          SliverAppBar(
            backgroundColor: const Color(0xFF080810),
            expandedHeight: 180,
            floating: false,
            pinned: true,
            elevation: 0,
            flexibleSpace: FlexibleSpaceBar(
              background: _buildHeader(),
            ),
            bottom: TabBar(
              controller: _tabController,
              indicatorColor: const Color(0xFF00E5FF),
              indicatorWeight: 2,
              labelColor: const Color(0xFF00E5FF),
              unselectedLabelColor: Colors.white38,
              labelStyle: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
              tabs: const [
                Tab(text: 'QUÉ ES'),
                Tab(text: 'CÓMO AYUDA'),
                Tab(text: 'PROTOCOLO'),
              ],
            ),
          ),
        ],
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildWhatIsTab(),
            _buildHowHelpsTab(),
            _buildProtocolTab(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF0A0A1A), Color(0xFF0D1A2A)],
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      border: Border.all(color: const Color(0xFF00E5FF), width: 0.8),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'CIENCIA COGNITIVA',
                      style: TextStyle(
                        color: Color(0xFF00E5FF),
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              const Text(
                'Fatiga Central\n& Rendimiento',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  height: 1.1,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Por qué medimos tu estado cognitivo cada día',
                style: TextStyle(
                  color: Colors.white54,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── TAB 1: QUÉ ES ──────────────────────────────────────────────────────────
  Widget _buildWhatIsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoCard(
          icon: Icons.bolt_rounded,
          iconColor: const Color(0xFF00E5FF),
          title: '¿Qué es la Fatiga Central?',
          body:
              'La fatiga central ocurre en el Sistema Nervioso Central (SNC), '
              'no en los músculos. Es la reducción de la capacidad del cerebro '
              'para reclutar y coordinar las fibras musculares, incluso cuando '
              'el músculo físicamente podría seguir trabajando.',
        ),
        const SizedBox(height: 12),
        _buildInfoCard(
          icon: Icons.device_hub_rounded,
          iconColor: const Color(0xFFB388FF),
          title: '¿Qué es el PVT?',
          body:
              'El Psychomotor Vigilance Task (PVT) es el estándar de oro '
              'científico para medir el tiempo de reacción simple. Evalúa la '
              'vigilancia sostenida: la capacidad del SNC de mantener la '
              'atención y responder a estímulos de forma rápida y precisa.',
        ),
        const SizedBox(height: 12),
        _buildInfoCard(
          icon: Icons.science_rounded,
          iconColor: const Color(0xFF69F0AE),
          title: 'El Modelo Ex-Gaussiano',
          body:
              'Nuestra tecnologia avanzada no usa "promedios" simples. Evaluamos tu rendimiento con un modelo matematico (Ex-Gauss) que separa tu Velocidad Motora Pura de los bloqueos atencionales profundos.',
        ),
        const SizedBox(height: 12),
        _buildInfoCard(
          icon: Icons.analytics_rounded,
          iconColor: const Color(0xFFFFD54F),
          title: '¿Qué es el Índice IRI?',
          body:
              'El Índice de Resiliencia Integrado (IRI) es tu score diario de '
              'disponibilidad. Combina inteligentemente tu velocidad de reacción '
              '(SNC) con el contexto de tus hábitos (sueño, estrés, fatiga), '
              'entregando un puntaje claro para ajustar tu entrenamiento.',
        ),
        const SizedBox(height: 12),
        _buildKeyMetricsCard(),
      ],
    );
  }

  // ── TAB 2: CÓMO AYUDA ──────────────────────────────────────────────────────
  Widget _buildHowHelpsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildBenefitItem(
          number: '01',
          color: const Color(0xFF00E5FF),
          title: 'Prevención de Lesiones',
          body:
              'Un TR elevado indica que el SNC no está procesando señales '
              'propioceptivas correctamente. Entrenar en ese estado multiplica '
              'el riesgo de esguinces, distensiones y errores técnicos.',
        ),
        _buildBenefitItem(
          number: '02',
          color: const Color(0xFFB388FF),
          title: 'Optimización de la Carga',
          body:
              'Saber tu nivel de readiness permite que el cuerpo técnico '
              'ajuste la intensidad del entrenamiento del día: más carga cuando '
              'estás en óptimo, trabajo técnico o recuperación cuando hay fatiga.',
        ),
        _buildBenefitItem(
          number: '03',
          color: const Color(0xFF69F0AE),
          title: 'Monitoreo de Supercompensación',
          body:
              'La curva de TR a lo largo de semanas revela si tu SNC está '
              'supercompensando tras las cargas de entrenamiento, o si acumulas '
              'fatiga hacia el sobreentrenamiento.',
        ),
        _buildBenefitItem(
          number: '04',
          color: const Color(0xFFFFD54F),
          title: 'Decisiones Basadas en Datos',
          body:
              'Elimina el "cómo te sientes hoy" subjetivo. Cada día tienes '
              'un número objetivo que respalda decisiones de '
              'rendimiento deportivo con evidencia real.',
        ),
        const SizedBox(height: 8),
        _buildResearchCard(),
      ],
    );
  }

  // ── TAB 3: PROTOCOLO ───────────────────────────────────────────────────────
  Widget _buildProtocolTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildSectionLabel('ANTES DE LA PRUEBA'),
        const SizedBox(height: 8),
        _buildProtocolStep(
          step: 1,
          icon: Icons.bedtime_rounded,
          text: 'Realízala siempre a la misma hora, idealmente al despertar o antes del entrenamiento.',
        ),
        _buildProtocolStep(
          step: 2,
          icon: Icons.coffee_rounded,
          text: 'No consumas cafeína ni alimentos 30 minutos antes para no distorsionar el TR.',
        ),
        _buildProtocolStep(
          step: 3,
          icon: Icons.phone_android_rounded,
          text: 'Elimina distracciones. El teléfono en silencio, entorno tranquilo.',
        ),
        const SizedBox(height: 16),
        _buildSectionLabel('DURANTE LA PRUEBA'),
        const SizedBox(height: 8),
        _buildProtocolStep(
          step: 4,
          icon: Icons.touch_app_rounded,
          text: 'Reacciona lo más rápido posible cuando aparezca el estímulo. Sin anticipar.',
        ),
        _buildProtocolStep(
          step: 5,
          icon: Icons.timer_rounded,
          text: 'La prueba de 30 estimulos dura ~4 minutos. Este volumen (PVT-B estandar) es vital para lograr precision matematica.',
        ),
        const SizedBox(height: 16),
        _buildSectionLabel('INTERPRETAR TU RESULTADO'),
        const SizedBox(height: 8),
        _buildInterpretationTable(),
        const SizedBox(height: 16),
        _buildFaqSection(),
      ],
    );
  }

  // ── WIDGETS REUTILIZABLES ─────────────────────────────────────────────────

  Widget _buildInfoCard({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String body,
  }) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1020),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  body,
                  style: const TextStyle(
                    color: Colors.white60,
                    fontSize: 12.5,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildKeyMetricsCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0A1A2A), Color(0xFF0A0F1E)],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'MÉTRICAS CLAVE QUE SE MIDEN',
            style: TextStyle(
              color: Color(0xFF00E5FF),
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 14),
          _metricRow('Velocidad Motora (μ)', 'Tu velocidad de reacción pura e instintiva (ms).'),
          _metricRow('Consistencia (σ)', 'Qué tan estable eres. A menor valor, mayor control motriz.'),
          _metricRow('Fatiga Central (τ)', 'Refleja los micro-bloqueos del SNC causados por cansancio.'),
          _metricRow('Z-Score Histórico', 'Tu rendimiento de hoy comparado con tus últimos 21 días.'),
        ],
      ),
    );
  }

  Widget _metricRow(String label, String desc) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: Color(0xFF00E5FF),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                Text(desc,
                    style: const TextStyle(color: Colors.white38, fontSize: 11)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBenefitItem({
    required String number,
    required Color color,
    required String title,
    required String body,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            number,
            style: TextStyle(
              color: color.withOpacity(0.4),
              fontSize: 32,
              fontWeight: FontWeight.w900,
              height: 1,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  body,
                  style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 12.5,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 8),
                Divider(color: Colors.white.withOpacity(0.06)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResearchCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1020),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFB388FF).withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          Text(
            '📚 RESPALDO CIENTÍFICO',
            style: TextStyle(
              color: Color(0xFFB388FF),
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
            ),
          ),
          SizedBox(height: 10),
          Text(
            'El PVT fue desarrollado por el Dr. David Dinges (Universidad de '
            'Pennsylvania) y es el instrumento más validado para medir el '
            'impacto de la restricción de sueño y la fatiga en la vigilancia '
            'sostenida (Dinges et al., 1997; Van Dongen et al., 2003).\n\n'
            'Más de 500 estudios peer-reviewed lo utilizan como gold standard '
            'en neurociencia del rendimiento y medicina del sueño.',
            style: TextStyle(
              color: Colors.white54,
              fontSize: 12,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionLabel(String label) {
    return Text(
      label,
      style: const TextStyle(
        color: Colors.white30,
        fontSize: 10,
        fontWeight: FontWeight.bold,
        letterSpacing: 2,
      ),
    );
  }

  Widget _buildProtocolStep({
    required int step,
    required IconData icon,
    required String text,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF0F1020),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white.withOpacity(0.06)),
        ),
        child: Row(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  '$step',
                  style: const TextStyle(
                    color: Color(0xFF00E5FF),
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Icon(icon, color: Colors.white38, size: 18),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12.5,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInterpretationTable() {
    final rows = [
      ['< 220 ms', 'ÓPTIMO', const Color(0xFF69F0AE)],
      ['220–280 ms', 'NORMAL', const Color(0xFFFFD54F)],
      ['280–350 ms', 'ALERTA', const Color(0xFFFF8A65)],
      ['> 350 ms', 'FATIGA CRÍTICA', const Color(0xFFFF5252)],
    ];

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F1020),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: Colors.white10)),
            ),
            child: Row(
              children: const [
                Expanded(
                    child: Text('TR MEDIO',
                        style: TextStyle(
                            color: Colors.white38,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1))),
                Expanded(
                    child: Text('ESTADO',
                        style: TextStyle(
                            color: Colors.white38,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1))),
              ],
            ),
          ),
          ...rows.map((row) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  border: Border(bottom: BorderSide(color: Colors.white10)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        row[0] as String,
                        style: const TextStyle(color: Colors.white70, fontSize: 13),
                      ),
                    ),
                    Expanded(
                      child: Text(
                        row[1] as String,
                        style: TextStyle(
                          color: row[2] as Color,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1,
                        ),
                      ),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildFaqSection() {
    final faqs = [
      {
        'q': '¿Por qué hacerlo todos los días?',
        'a':
            'La fatiga central fluctúa diariamente según el sueño, la carga de entrenamiento y el estrés. Una sola medición no es suficiente; el valor predictivo emerge de la tendencia longitudinal.',
      },
      {
        'q': '¿Afecta si no dormí bien?',
        'a':
            'Sí, y eso es exactamente lo que queremos medir. La restricción de sueño es la principal causa de fatiga central y el PVT la detecta con alta sensibilidad incluso tras una sola noche de mal sueño.',
      },
      {
        'q': '¿Puedo mejorar "practicando"?',
        'a':
            'El efecto de práctica es mínimo después de los primeros 2-3 días. A partir de ahí, las variaciones reflejan genuinamente tu estado del SNC, no la familiaridad con la prueba.',
      },
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionLabel('PREGUNTAS FRECUENTES'),
        const SizedBox(height: 10),
        ...faqs.asMap().entries.map((entry) {
          final i = entry.key;
          final faq = entry.value;
          final isOpen = _expandedIndex == i;
          return GestureDetector(
            onTap: () => setState(() => _expandedIndex = isOpen ? -1 : i),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isOpen
                    ? const Color(0xFF0A1A2A)
                    : const Color(0xFF0F1020),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: isOpen
                      ? const Color(0xFF00E5FF).withOpacity(0.3)
                      : Colors.white.withOpacity(0.06),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          faq['q']!,
                          style: TextStyle(
                            color: isOpen
                                ? const Color(0xFF00E5FF)
                                : Colors.white70,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      Icon(
                        isOpen
                            ? Icons.keyboard_arrow_up_rounded
                            : Icons.keyboard_arrow_down_rounded,
                        color: Colors.white38,
                        size: 20,
                      ),
                    ],
                  ),
                  if (isOpen) ...[
                    const SizedBox(height: 10),
                    Text(
                      faq['a']!,
                      style: const TextStyle(
                        color: Colors.white54,
                        fontSize: 12.5,
                        height: 1.5,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          );
        }),
      ],
    );
  }
}
