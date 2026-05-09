import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme/app_theme.dart';

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
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [
              _riskCard("Sergio Ramos", "CRÍTICO", AppTheme.accentRed, "Optimizar", 58, 18.5),
              _riskCard("Kevin De Bruyne", "ADVERTENCIA", AppTheme.accentYellow, "Reprogramar", 72, 12.2),
              _riskCard("Marco Reus", "ÓPTIMO", AppTheme.accentGreen, "Mantenimiento", 91, 8.4),
            ],
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
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: AppTheme.glassDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("CORRELACIÓN NEURO-MECÁNICA (IRI vs DESACELERACIONES)", style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 32),
          SizedBox(
            height: 300,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(show: true, drawVerticalLine: false, getDrawingHorizontalLine: (value) => FlLine(color: AppTheme.glassBorder, strokeWidth: 1)),
                titlesData: FlTitlesData(show: true, rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)), topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false))),
                borderData: FlBorderData(show: false),
                lineBarsData: [
                  LineChartBarData(
                    spots: const [FlSpot(0, 85), FlSpot(2, 80), FlSpot(4, 75), FlSpot(6, 60), FlSpot(8, 55), FlSpot(10, 50)],
                    isCurved: true,
                    color: AppTheme.accentGreen,
                    barWidth: 3,
                    dotData: FlDotData(show: false),
                    belowBarData: BarAreaData(show: true, color: AppTheme.accentGreen.withOpacity(0.1)),
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
