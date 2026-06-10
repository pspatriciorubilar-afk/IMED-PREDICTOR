import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../core/network/sync_service.dart';

class ReadinessDashboardScreen extends StatefulWidget {
  final Map<String, dynamic> readinessData;
  final String token;
  final VoidCallback? onRetake;

  const ReadinessDashboardScreen({
    super.key, 
    required this.readinessData,
    required this.token,
    this.onRetake,
  });

  @override
  State<ReadinessDashboardScreen> createState() => _ReadinessDashboardScreenState();
}

class _ReadinessDashboardScreenState extends State<ReadinessDashboardScreen> {
  // Colores Premium HUD (StitchMCP)
  static const Color cianElectric = Color(0xFF00E5FF);
  static const Color voltGreen = Color(0xFF39FF14);
  static const Color bgDark = Color(0xFF0A0A0A);
  static const Color surfaceElevated = Color(0xFF131313);
  static const Color errorRed = Color(0xFFFF3131);
  static const Color textHigh = Colors.white;
  static const Color textMuted = Color(0xFFADAAAA);

  late int score;
  late String status;
  List<FlSpot> pvtSpots = [];
  bool isLoadingTrends = true;

  @override
  void initState() {
    super.initState();
    score = widget.readinessData['readinessScore'] ?? 0;
    status = widget.readinessData['status'] ?? 'CALIBRATING';
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final trends = await SyncService.getTrends(widget.token);
      if (mounted && trends.isNotEmpty) {
        setState(() {
          pvtSpots = [];
          for (int i = 0; i < trends.length; i++) {
            final m = trends[i];
            pvtSpots.add(FlSpot(i.toDouble(), m['pvtMeanLatency'].toDouble()));
          }
          isLoadingTrends = false;
        });
      } else {
        setState(() => isLoadingTrends = false);
      }
    } catch (e) {
      if (mounted) setState(() => isLoadingTrends = false);
    }
  }

  Color _getStatusColor() {
    if (status == 'VERDE') return voltGreen;
    if (status == 'AMARILLO') return Colors.amberAccent;
    if (status == 'ROJO') return errorRed;
    return cianElectric; // Calibrating
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor();
    final snrWarning = widget.readinessData['snrWarning'];

    return Scaffold(
      backgroundColor: bgDark,
      appBar: AppBar(
        title: const Text('TELEMETRÍA DE RENDIMIENTO SNC', style: TextStyle(color: cianElectric, fontSize: 14, letterSpacing: 2, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: const IconThemeData(color: cianElectric),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // BANNER DE CALIDAD DE SEÑAL (Higiene del Dato)
              if (snrWarning != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 20),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: errorRed.withOpacity(0.1),
                    border: Border.all(color: errorRed.withOpacity(0.5)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: errorRed, size: 20),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          snrWarning,
                          style: const TextStyle(color: errorRed, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),



              // 1. ZONA DEL RINGER
              _buildKineticRing(statusColor),
              const SizedBox(height: 32),

              // 2. MÉTRICAS DE LA SESIÓN PVT (única en esta pantalla)
              _buildPvtSessionCard(statusColor),
              const SizedBox(height: 32),

              // 3. GRÁFICO COMPARATIVO DUAL-AXIS
              if (isLoadingTrends)
                const Center(child: CircularProgressIndicator(color: cianElectric))
              else
                _buildDualAxisChart(),
              const SizedBox(height: 40),

              // 4. BOTÓN DE NUEVA PRUEBA
              if (widget.onRetake != null) ...[
                GestureDetector(
                  onTap: widget.onRetake,
                  child: Container(
                    width: double.infinity,
                    height: 56,
                    decoration: BoxDecoration(
                      border: Border.all(color: cianElectric.withOpacity(0.6)),
                    ),
                    child: const Center(
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.refresh_rounded, color: cianElectric, size: 18),
                          SizedBox(width: 10),
                          Text(
                            'REALIZAR NUEVA PRUEBA',
                            style: TextStyle(
                              color: cianElectric,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 5. INDICADOR HACIA REGISTRO DIARIO
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  border: Border.all(color: cianElectric.withOpacity(0.2)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.arrow_forward_ios_rounded, color: cianElectric, size: 14),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Consulta tu REGISTRO DIARIO para el resumen narrativo y sugerencias de entrenamiento.',
                        style: TextStyle(color: textMuted, fontSize: 11, height: 1.5),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildKineticRing(Color glowColor) {
    return Center(
      child: Container(
        width: 260,
        height: 260,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: bgDark,
          boxShadow: [
            BoxShadow(
              color: glowColor.withOpacity(0.15),
              blurRadius: 40,
              spreadRadius: 10,
            )
          ],
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            // Anillo de progreso en SizedBox separado del contenido central
            SizedBox(
              width: 240,
              height: 240,
              child: CircularProgressIndicator(
                value: score / 100,
                strokeWidth: 8,
                backgroundColor: Colors.white10,
                valueColor: AlwaysStoppedAnimation<Color>(glowColor),
                strokeCap: StrokeCap.square,
              ),
            ),
            // Contenido interior — acotado a 180px (240 - 2×8 - margen)
            SizedBox(
              width: 180,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    "READINESS",
                    style: TextStyle(color: textMuted, fontSize: 10, letterSpacing: 3, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Text(
                      "$score",
                      style: const TextStyle(
                        color: textHigh,
                        fontSize: 64,
                        fontWeight: FontWeight.w900,
                        height: 1.0,
                      ),
                    ),
                  ),
                  Text(
                    status == 'CALIBRATING' ? 'CALIBRANDO' : status,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: glowColor, fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1.5),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPvtSessionCard(Color statusColor) {
    final isOffline = widget.readinessData['isOfflineMode'] as bool? ?? true;
    final contextDetail = widget.readinessData['contextDetail'] as String? ?? '';

    return Container(
      decoration: BoxDecoration(
        color: surfaceElevated,
        border: Border(left: BorderSide(color: statusColor, width: 4)),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.speed_rounded, color: statusColor, size: 18),
              const SizedBox(width: 8),
              Text(
                'MÉTRICAS DE SESIÓN PVT',
                style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.5),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isOffline ? Colors.orange.withOpacity(0.15) : cianElectric.withOpacity(0.1),
                  border: Border.all(color: isOffline ? Colors.orange.withOpacity(0.5) : cianElectric.withOpacity(0.4)),
                ),
                child: Text(
                  isOffline ? 'OFFLINE' : 'ONLINE',
                  style: TextStyle(
                    color: isOffline ? Colors.orange : cianElectric,
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _metricTile('SCORE IRI', '$score / 100', statusColor),
              const SizedBox(width: 12),
              _metricTile('ESTADO SNC', status == 'CALIBRATING' ? 'CALIBRANDO' : status, statusColor),
            ],
          ),
          if (contextDetail.isNotEmpty) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.03),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white.withOpacity(0.08)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.insights_rounded, color: statusColor, size: 14),
                      const SizedBox(width: 8),
                      Text(
                        'ANÁLISIS DE HÁBITOS',
                        style: TextStyle(color: statusColor.withOpacity(0.8), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1.5),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    contextDetail,
                    style: const TextStyle(color: textMuted, fontSize: 11.5, height: 1.5),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _metricTile(String label, String value, Color valueColor) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.3),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(color: textMuted, fontSize: 8, letterSpacing: 1.5, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(value, style: TextStyle(color: valueColor, fontSize: 13, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildDualAxisChart() {
    if (pvtSpots.isEmpty) {
      return const Center(child: Text("Datos insuficientes para la gráfica.", style: TextStyle(color: textMuted)));
    }

    // Calcular escala dinámica
    final allY = pvtSpots.map((s) => s.y).toList();
    final minY = (allY.reduce((a, b) => a < b ? a : b) - 50).clamp(0.0, 1000.0);
    final maxY = (allY.reduce((a, b) => a > b ? a : b) + 50).clamp(200.0, 1500.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("TELEMETRÍA DE FATIGA CENTRAL (PVT)", style: TextStyle(color: textMuted, fontSize: 10, letterSpacing: 2, fontWeight: FontWeight.bold)),
        const SizedBox(height: 20),
        SizedBox(
          height: 220,
          child: LineChart(
            LineChartData(
              minY: minY,
              maxY: maxY,
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: 50,
                getDrawingHorizontalLine: (v) => FlLine(color: Colors.white.withOpacity(0.03)),
              ),
              titlesData: FlTitlesData(
                show: true,
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (val, meta) => Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Text('D${val.toInt() + 1}', style: const TextStyle(color: textMuted, fontSize: 9)),
                    ),
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true, 
                    reservedSize: 40,
                    getTitlesWidget: (v, m) => Text(v.toInt().toString(), style: const TextStyle(color: textMuted, fontSize: 9)),
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: pvtSpots,
                  isCurved: true,
                  color: cianElectric,
                  barWidth: 3,
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, pct, bar, idx) => FlDotCirclePainter(
                      radius: 4,
                      color: cianElectric,
                      strokeWidth: 2,
                      strokeColor: Colors.white,
                    ),
                  ),
                  belowBarData: BarAreaData(show: true, color: cianElectric.withOpacity(0.1)),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 10),
            const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.horizontal_rule, color: cianElectric, size: 14),
            SizedBox(width: 4),
            Text("PVT Latency", style: TextStyle(color: textMuted, fontSize: 10)),
          ],
        )
      ],
    );
  }
}
