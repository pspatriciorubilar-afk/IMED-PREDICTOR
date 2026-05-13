import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../theme/app_theme.dart';
import '../models/performance_model.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          _buildSidebar(),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  const SizedBox(height: 32),
                  _buildRiskAlertPanel(),
                  const SizedBox(height: 32),
                  _buildNeuroEvaluationSection(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebar() {
    return Container(
      width: 250,
      decoration: const BoxDecoration(
        color: AppTheme.background,
        border: Border(right: BorderSide(color: AppTheme.glassBorder)),
      ),
      child: Column(
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 48),
            child: Text(
              "IMED PREDICTOR",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, letterSpacing: 2),
            ),
          ),
          _sidebarItem(Icons.dashboard_rounded, "Dashboard", active: true),
          _sidebarItem(Icons.group_rounded, "Atletas"),
          _sidebarItem(Icons.analytics_rounded, "Neuro-Reports"),
          _sidebarItem(Icons.settings_rounded, "Ajustes"),
        ],
      ),
    );
  }

  Widget _sidebarItem(IconData icon, String label, {bool active = false}) {
    return ListTile(
      leading: Icon(icon, color: active ? AppTheme.accentGreen : AppTheme.textSecondary),
      title: Text(label, style: TextStyle(color: active ? AppTheme.accentGreen : AppTheme.textSecondary)),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Centro de Mando de Rendimiento", style: TextStyle(fontSize: 14, color: AppTheme.textSecondary, letterSpacing: 1.5)),
        const SizedBox(height: 8),
        const Text("Análisis de Riesgo de Lesiones", style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildRiskAlertPanel() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("PANEL DE ALERTAS CRÍTICAS", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2)),
        const SizedBox(height: 16),
        SizedBox(
          height: 180,
          child: StreamBuilder<QuerySnapshot>(
            stream: FirebaseFirestore.instance
                .collection('Daily_Performance')
                .orderBy('timestamp', descending: true)
                .limit(10)
                .snapshots(),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator(color: AppTheme.accentGreen));
              }
              if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
                return const Center(child: Text("Esperando sincronización de datos GPS...", style: TextStyle(color: AppTheme.textSecondary)));
              }

              final records = snapshot.data!.docs
                  .map((doc) => PerformanceModel.fromFirestore(doc))
                  .toList();

              return ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: records.length,
                itemBuilder: (context, index) {
                  final p = records[index];
                  Color color = AppTheme.accentGreen;
                  if (p.riskLevel == 'RED') color = AppTheme.accentRed;
                  if (p.riskLevel == 'YELLOW') color = AppTheme.accentYellow;

                  return _riskCard(p.athleteName, p.ivnLabel, color, p.action, p.iri, p.decelZ5);
                },
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _riskCard(String name, String status, Color color, String action, double iri, double decels) {
    return Container(
      width: 280,
      margin: const EdgeInsets.only(right: 16),
      decoration: AppTheme.glassDecoration(),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: color.withOpacity(0.2), borderRadius: BorderRadius.circular(4)),
                child: Text(status, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const Spacer(),
          Row(
            children: [
              _metricSmall("IRI", iri.toString()),
              const SizedBox(width: 24),
              _metricSmall("DESACEL.", "${decels}m/s²"),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: color, foregroundColor: Colors.black),
              onPressed: () {},
              child: Text(action, style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _metricSmall(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 10)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
      ],
    );
  }

  Widget _buildNeuroEvaluationSection() {
    return StreamBuilder<QuerySnapshot>(
      stream: FirebaseFirestore.instance
          .collection('Daily_Performance')
          .orderBy('timestamp', descending: true)
          .limit(20)
          .snapshots(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const SizedBox();
        
        final records = snapshot.data!.docs
            .map((doc) => PerformanceModel.fromFirestore(doc))
            .toList()
            .reversed
            .toList();

        if (records.isEmpty) return const SizedBox();

        return Column(
          children: [
            _buildChartCard(
              "EVOLUCIÓN IRI (SNC)",
              records.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value.iri)).toList(),
              AppTheme.accentGreen,
              0, 100,
            ),
            const SizedBox(height: 24),
            _buildChartCard(
              "LATENCIA SNC (MS)",
              records.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value.latency)).toList(),
              AppTheme.accentBlue,
              150, 550,
            ),
            const SizedBox(height: 24),
            _buildChartCard(
              "DESACELERACIONES (Z5)",
              records.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value.decelZ5)).toList(),
              AppTheme.accentRed,
              0, (records.map((e) => e.decelZ5).reduce((a, b) => a > b ? a : b) + 5).clamp(20, 100),
            ),
          ],
        );
      },
    );
  }

  Widget _buildChartCard(String title, List<FlSpot> spots, Color color, double minY, double maxY) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: AppTheme.glassDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2)),
          const SizedBox(height: 32),
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                minY: minY,
                maxY: maxY,
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (value) => FlLine(color: AppTheme.glassBorder, strokeWidth: 1),
                ),
                titlesData: FlTitlesData(
                  show: true,
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 40,
                      getTitlesWidget: (value, meta) => Text(value.toInt().toString(), style: TextStyle(color: AppTheme.textSecondary, fontSize: 10)),
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    color: color,
                    barWidth: 3,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
                        radius: 4,
                        color: color,
                        strokeWidth: 2,
                        strokeColor: Colors.white,
                      ),
                    ),
                    belowBarData: BarAreaData(show: true, color: color.withOpacity(0.1)),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
