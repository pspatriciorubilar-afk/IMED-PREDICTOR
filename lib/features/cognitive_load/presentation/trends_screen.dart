import 'package:flutter/material.dart';
import 'package:isar/isar.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../auth/domain/user_profile.dart';
import '../../../core/network/sync_service.dart';
import '../domain/pvt_session.dart';

// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTES DE DISEÑO
// ─────────────────────────────────────────────────────────────────────────────
const _accent   = Color(0xFF00E5FF); // Cyan Eléctrico
const _volt     = Color(0xFF2FF801); // Volt Green → VERDE
const _yellow   = Color(0xFFFFD600); // Amarillo → ADVERTENCIA
const _red      = Color(0xFFFF4B4B); // Rojo      → CRÍTICO
const _surface  = Color(0xFF131313);
const _bgDark   = Color(0xFF0E0E0E);

// ─────────────────────────────────────────────────────────────────────────────
// MODELO INTERNO DE ANÁLISIS
// ─────────────────────────────────────────────────────────────────────────────
class _BaselineAnalysis {
  /// Promedio de latencia de las primeras 7 sesiones (línea de referencia personal).
  final double baselineMs;

  /// Latencia de la sesión más reciente (hoy).
  final double latestMs;

  /// Desviación porcentual respecto al baseline.
  /// Positivo = peor que el baseline (más lento). Negativo = mejor.
  final double deviationPct;

  /// Total de sesiones registradas.
  final int totalSessions;

  const _BaselineAnalysis({
    required this.baselineMs,
    required this.latestMs,
    required this.deviationPct,
    required this.totalSessions,
  });

  // ── SEMÁFORO DE DESVIACIÓN ─────────────────────────────────────────────────
  // Verde  : desviación ≤ +10% → rendimiento en línea con el baseline personal
  // Amarillo: +10% < desviación ≤ +25% → fatiga leve / inicio de sobrecarga
  // Rojo   : desviación > +25% → fatiga central significativa / riesgo
  Color get semaphoreColor {
    if (deviationPct <= 10.0)  return _volt;
    if (deviationPct <= 25.0)  return _yellow;
    return _red;
  }

  String get semaphoreLabel {
    if (deviationPct <= 10.0)  return 'ÓPTIMO';
    if (deviationPct <= 25.0)  return 'CARGA MODERADA';
    return 'FATIGA CENTRAL';
  }

  String get semaphoreNarrative {
    if (deviationPct <= 0.0) {
      return 'Rendimiento superior al baseline personal. Tu SNC muestra una recuperación completa.';
    } else if (deviationPct <= 10.0) {
      return 'Rendimiento dentro del rango de tu línea base. Estás disponible para carga de alta intensidad.';
    } else if (deviationPct <= 25.0) {
      return 'Leve incremento de latencia respecto a tu baseline. Considera sesiones de técnica o volumen moderado.';
    } else {
      return 'Fatiga central detectada (+${deviationPct.toStringAsFixed(1)}% sobre baseline). Prioriza la recuperación activa hoy.';
    }
  }

  bool get hasBaseline => totalSessions >= 7;
}

// ─────────────────────────────────────────────────────────────────────────────
// WIDGET PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────
class TrendsScreen extends StatefulWidget {
  final Isar isar;
  const TrendsScreen({super.key, required this.isar});

  @override
  State<TrendsScreen> createState() => _TrendsScreenState();
}

class _TrendsScreenState extends State<TrendsScreen> {
  UserProfile? _profile;
  bool _isLoading = true;
  List<dynamic> _serverTrends = [];
  _BaselineAnalysis? _analysis;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final profile = await widget.isar.collection<UserProfile>().where().findFirst();

    // 1. Intentar servidor Hostinger primero
    const dummyToken = "imed-sport-token-mock";
    List<dynamic> trends = [];
    try {
      trends = await SyncService.getTrends(dummyToken);
    } catch (e) {
      print("📡 [TRENDS] Servidor inaccesible: $e");
    }

    // 2. Fallback: leer sesiones locales Isar
    if (trends.isEmpty) {
      final localSessions = await widget.isar.collection<PvtSession>()
          .where()
          .sortByTimestamp()
          .findAll();

      int idx = 1;
      for (final session in localSessions) {
        trends.add({'day': 'S$idx', 'pvt': session.meanLatency});
        idx++;
      }
    }

    // 3. Calcular análisis de baseline
    final analysis = _computeAnalysis(trends);

    if (mounted) {
      setState(() {
        _profile = profile;
        _serverTrends = trends;
        _analysis = analysis;
        _isLoading = false;
      });
    }
  }

  /// Calcula la línea base personal usando las primeras 7 sesiones,
  /// luego compara la sesión más reciente contra ese promedio.
  _BaselineAnalysis? _computeAnalysis(List<dynamic> trends) {
    if (trends.isEmpty) return null;

    final total = trends.length;

    // Baseline = promedio de las primeras 7 sesiones (o todas si hay menos)
    final baselineCount = total < 7 ? total : 7;
    final baselineValues = trends
        .take(baselineCount)
        .map((t) => (t['pvt'] as num).toDouble())
        .toList();
    final baselineMs = baselineValues.reduce((a, b) => a + b) / baselineValues.length;

    // Última sesión (más reciente)
    final latestMs = (trends.last['pvt'] as num).toDouble();

    // Desviación porcentual: ((latest - baseline) / baseline) * 100
    final deviationPct = ((latestMs - baselineMs) / baselineMs) * 100;

    return _BaselineAnalysis(
      baselineMs: baselineMs,
      latestMs: latestMs,
      deviationPct: deviationPct,
      totalSessions: total,
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // BUILD
  // ─────────────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: _accent))
          : Stack(
              children: [
                Positioned(
                  top: -50, right: -50,
                  child: Container(
                    width: 300, height: 300,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(colors: [_accent.withOpacity(0.05), Colors.transparent]),
                    ),
                  ),
                ),
                SafeArea(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 24),
                        _buildHUDHeader(),
                        const SizedBox(height: 32),
                        _buildProfileHeader(),
                        const SizedBox(height: 32),

                        // ── MÉTRICAS DE BASELINE ────────────────────────────
                        if (_analysis != null) ...[
                          _buildSectionHeader("LÍNEA BASE PERSONAL", "REFERENCIA SNC (${_analysis!.hasBaseline ? '7 SESIONES' : '${_analysis!.totalSessions}/7 SESIONES'})"),
                          const SizedBox(height: 16),
                          _buildBaselineMetricsRow(_analysis!),
                          const SizedBox(height: 40),
                        ],

                        // ── GRÁFICO ─────────────────────────────────────────
                        _buildSectionHeader("TELEMETRÍA DE FATIGA CENTRAL", "SNC READINESS (PVT)"),
                        const SizedBox(height: 24),
                        _buildChart(),
                        const SizedBox(height: 8),
                        _buildChartLegend(),
                        const SizedBox(height: 40),

                        // ── SEMÁFORO / INSIGHTS ──────────────────────────────
                        _buildSectionHeader("RENDIMIENTO SEMANAL", "EVOLUCIÓN DEPORTIVA (PVT)"),
                        const SizedBox(height: 24),
                        _buildInsightsCard(),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // WIDGETS INTERNOS
  // ─────────────────────────────────────────────────────────────────────────

  Widget _buildHUDHeader() {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("MÓDULO DE ANÁLISIS V3.0",
            style: TextStyle(color: _accent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 2)),
        SizedBox(height: 8),
        Text("DASHBOARD ELITE",
            style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900)),
      ],
    );
  }

  Widget _buildSectionHeader(String tag, String title) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(tag, style: const TextStyle(color: _accent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 2)),
        const SizedBox(height: 4),
        Text(title, style: const TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildProfileHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _surface,
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(2),
            decoration: BoxDecoration(border: Border.all(color: _accent)),
            child: const Icon(Icons.psychology_rounded, color: _accent, size: 32),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_profile?.firstName.toUpperCase() ?? "ATLETA",
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900)),
                const Text("MOTOR DE INFERENCIA ACTIVO",
                    style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Fila de 3 tiles: Baseline · Última sesión · Desviación con semáforo
  Widget _buildBaselineMetricsRow(_BaselineAnalysis a) {
    final devSign = a.deviationPct >= 0 ? '+' : '';
    return Row(
      children: [
        _metricTile(
          label: 'BASELINE\nPERSONAL',
          value: '${a.baselineMs.toStringAsFixed(0)} ms',
          color: _accent,
        ),
        const SizedBox(width: 8),
        _metricTile(
          label: 'ÚLTIMA\nSESIÓN',
          value: '${a.latestMs.toStringAsFixed(0)} ms',
          color: Colors.white,
        ),
        const SizedBox(width: 8),
        _metricTile(
          label: 'DESVIACIÓN\nBASELINE',
          value: '$devSign${a.deviationPct.toStringAsFixed(1)}%',
          color: a.semaphoreColor,
          highlighted: true,
        ),
      ],
    );
  }

  Widget _metricTile({required String label, required String value, required Color color, bool highlighted = false}) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
        decoration: BoxDecoration(
          color: highlighted ? color.withOpacity(0.08) : _bgDark,
          border: Border.all(color: highlighted ? color.withOpacity(0.4) : Colors.white.withOpacity(0.05)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: TextStyle(color: color.withOpacity(0.7), fontSize: 8, letterSpacing: 1.5, fontWeight: FontWeight.bold, height: 1.4)),
            const SizedBox(height: 8),
            Text(value,
                style: TextStyle(color: color, fontSize: 16, fontWeight: FontWeight.w900)),
          ],
        ),
      ),
    );
  }

  Widget _buildChart() {
    if (_serverTrends.isEmpty) {
      return Container(
        height: 280,
        width: double.infinity,
        decoration: BoxDecoration(color: _bgDark, border: Border.all(color: Colors.white.withOpacity(0.05))),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.hourglass_empty_rounded, color: _accent, size: 40),
            SizedBox(height: 16),
            Text("CALIBRACIÓN EN CURSO", style: TextStyle(color: _accent, fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 12)),
            SizedBox(height: 8),
            Text("RECOPILANDO LÍNEA BASE...", style: TextStyle(color: Colors.white38, fontSize: 10)),
          ],
        ),
      );
    }

    final pvtSpots = <FlSpot>[];
    for (int i = 0; i < _serverTrends.length; i++) {
      pvtSpots.add(FlSpot(i.toDouble(), (_serverTrends[i]['pvt'] as num).toDouble()));
    }

    // Línea horizontal de baseline (si existe)
    final baselineY = _analysis?.baselineMs;

    // Rango dinámico del eje Y con márgenes más amplios
    final allValues = pvtSpots.map((s) => s.y).toList();
    if (baselineY != null) allValues.add(baselineY);
    final minY = (allValues.reduce((a, b) => a < b ? a : b) - 100).clamp(0, 1000).toDouble();
    final maxY = (allValues.reduce((a, b) => a > b ? a : b) + 100).clamp(200, 1500).toDouble();

    return Container(
      height: 320,
      padding: const EdgeInsets.only(right: 20, left: 10, top: 40, bottom: 20),
      decoration: BoxDecoration(
        color: _bgDark,
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: LineChart(
        LineChartData(
          minY: minY,
          maxY: maxY,
          lineTouchData: LineTouchData(
            touchTooltipData: LineTouchTooltipData(
              tooltipBgColor: Colors.black,
              getTooltipItems: (spots) => spots.map((spot) {
                final isBaseline = spot.barIndex == 1;
                return LineTooltipItem(
                  isBaseline
                      ? 'BASE: ${spot.y.toInt()} ms'
                      : '${spot.y.toInt()} ms',
                  TextStyle(
                    color: isBaseline ? _accent.withOpacity(0.6) : _accent,
                    fontWeight: FontWeight.w900,
                    fontSize: 12,
                  ),
                );
              }).toList(),
            ),
          ),
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: 50,
            getDrawingHorizontalLine: (v) => FlLine(color: Colors.white.withOpacity(0.03)),
          ),
          titlesData: FlTitlesData(
            show: true,
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 30,
                getTitlesWidget: (v, m) {
                  final i = v.toInt();
                  if (i >= 0 && i < _serverTrends.length) {
                    return Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: Text(
                        _serverTrends[i]['day'] ?? '',
                        style: const TextStyle(color: Colors.white24, fontSize: 9, fontWeight: FontWeight.bold),
                      ),
                    );
                  }
                  return const SizedBox();
                },
              ),
            ),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 40,
                getTitlesWidget: (v, m) => Text(v.toInt().toString(), style: const TextStyle(color: Colors.white24, fontSize: 9)),
              ),
            ),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            // ── Curva de sesiones PVT ────────────────────────────────────────
            LineChartBarData(
              spots: pvtSpots,
              isCurved: true,
              color: _accent,
              barWidth: 3,
              isStrokeCapRound: true,
              dotData: FlDotData(
                show: true,
                getDotPainter: (spot, pct, bar, idx) => FlDotCirclePainter(
                  radius: 4,
                  color: _accent,
                  strokeWidth: 2,
                  strokeColor: Colors.white,
                ),
              ),
              belowBarData: BarAreaData(
                show: true,
                gradient: LinearGradient(
                  colors: [_accent.withOpacity(0.12), Colors.transparent],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
            ),

            // ── Línea de baseline (punteada horizontal) ──────────────────────
            if (baselineY != null)
              LineChartBarData(
                spots: [
                  FlSpot(0, baselineY),
                  FlSpot((_serverTrends.length - 1).toDouble(), baselineY),
                ],
                isCurved: false,
                color: _accent.withOpacity(0.35),
                barWidth: 1.5,
                isStrokeCapRound: false,
                dotData: const FlDotData(show: false),
                dashArray: [6, 4], // línea punteada
                belowBarData: BarAreaData(show: false),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildChartLegend() {
    return Row(
      children: [
        Container(width: 14, height: 3, color: _accent),
        const SizedBox(width: 6),
        const Text("SESIÓN PVT", style: TextStyle(color: Colors.white38, fontSize: 9, letterSpacing: 1)),
        const SizedBox(width: 20),
        Container(width: 14, height: 1.5, color: _accent.withOpacity(0.4)),
        const SizedBox(width: 6),
        const Text("BASELINE PERSONAL", style: TextStyle(color: Colors.white38, fontSize: 9, letterSpacing: 1)),
      ],
    );
  }

  Widget _buildInsightsCard() {
    if (_serverTrends.isEmpty || _analysis == null) return const SizedBox();

    final a = _analysis!;

    if (!a.hasBaseline) {
      // Todavía en calibración
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: _surface,
          border: Border(left: BorderSide(color: _accent.withOpacity(0.4), width: 4)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.hourglass_top_rounded, color: _accent.withOpacity(0.6), size: 20),
                const SizedBox(width: 12),
                const Text("FASE DE CALIBRACIÓN",
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              "El sistema está modelando tu línea base personal de latencia de reacción. "
              "Completa ${7 - a.totalSessions} sesión(es) más para activar el análisis de desviación.",
              style: const TextStyle(color: Colors.white54, fontSize: 13, height: 1.6),
            ),
            const SizedBox(height: 16),
            // Barra de progreso de calibración
            ClipRect(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("${a.totalSessions}/7 SESIONES",
                      style: TextStyle(color: _accent.withOpacity(0.7), fontSize: 9, letterSpacing: 1.5, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  LinearProgressIndicator(
                    value: a.totalSessions / 7,
                    backgroundColor: Colors.white.withOpacity(0.05),
                    color: _accent,
                    minHeight: 3,
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    // ── Baseline completo → mostrar semáforo de desviación ─────────────────
    final semColor = a.semaphoreColor;
    final devSign  = a.deviationPct >= 0 ? '+' : '';

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: _surface,
        border: Border(left: BorderSide(color: semColor, width: 4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header con semáforo
          Row(
            children: [
              Icon(Icons.analytics_outlined, color: semColor, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Text(a.semaphoreLabel,
                    style: TextStyle(color: semColor, fontWeight: FontWeight.w900, fontSize: 14, letterSpacing: 1)),
              ),
              // Badge desviación
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: semColor.withOpacity(0.12),
                  border: Border.all(color: semColor.withOpacity(0.4)),
                ),
                child: Text(
                  '$devSign${a.deviationPct.toStringAsFixed(1)}%',
                  style: TextStyle(color: semColor, fontSize: 13, fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            a.semaphoreNarrative,
            style: const TextStyle(color: Colors.white54, fontSize: 13, height: 1.6),
          ),
          const SizedBox(height: 20),
          // Resumen numérico
          Row(
            children: [
              _infoChip(label: 'BASELINE', value: '${a.baselineMs.toStringAsFixed(0)} ms', color: Colors.white38),
              const SizedBox(width: 12),
              _infoChip(label: 'HOY', value: '${a.latestMs.toStringAsFixed(0)} ms', color: Colors.white),
              const SizedBox(width: 12),
              _infoChip(label: 'SESIONES', value: '${a.totalSessions}', color: _accent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _infoChip({required String label, required String value, required Color color}) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: color.withOpacity(0.5), fontSize: 8, letterSpacing: 1.5, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
