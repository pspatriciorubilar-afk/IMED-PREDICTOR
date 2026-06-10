import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Pantalla de Registro Diario — SNC Readiness del día actual.
///
/// Usa ValueListenableBuilder sobre la caja Hive 'daily_readiness':
/// - Se actualiza AUTOMÁTICAMENTE cuando BiometricFlowCoordinator
///   escribe el resultado del día, sin necesidad de recargar la pantalla.
/// - Funciona correctamente al cambiar de pestaña y volver.
class DailyReadinessScreen extends StatelessWidget {
  const DailyReadinessScreen({super.key});

  static const Color _cyan    = Color(0xFF00E5FF);
  static const Color _green   = Color(0xFF39FF14);
  static const Color _amber   = Color(0xFFFFC107);
  static const Color _red     = Color(0xFFFF3131);
  static const Color _bg      = Color(0xFF0A0A0A);
  static const Color _surface = Color(0xFF131313);

  @override
  Widget build(BuildContext context) {
    // La caja ya está abierta desde main.dart — acceso directo sin async
    final box = Hive.box('daily_readiness');

    return Scaffold(
      backgroundColor: _bg,
      body: SafeArea(
        child: ValueListenableBuilder(
          // Escucha únicamente la clave 'today' para evitar rebuilds innecesarios
          valueListenable: box.listenable(keys: const ['today']),
          builder: (context, Box liveBox, _) {
            final record = liveBox.get('today');
            if (record == null) return _buildEmptyState();
            return _buildReadinessView(record);
          },
        ),
      ),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // ESTADO VACÍO
  // ─────────────────────────────────────────────────────────────────────────
  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: _cyan.withOpacity(0.3), width: 1.5),
              ),
              child: const Icon(Icons.sensors, color: _cyan, size: 48),
            ),
            const SizedBox(height: 28),
            const Text(
              'SIN REGISTRO HOY',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w900,
                letterSpacing: 2,
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Completa el flujo biométrico\n(Wellness → PVT)\npara ver tu Readiness del día.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white38, fontSize: 13, height: 1.6),
            ),
            const SizedBox(height: 32),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                border: Border.all(color: _cyan.withOpacity(0.4)),
              ),
              child: const Text(
                'Inicia desde la pestaña "Prueba PVT"',
                style: TextStyle(color: _cyan, fontSize: 11, letterSpacing: 1),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // VISTA CON DATOS
  // ─────────────────────────────────────────────────────────────────────────
  Widget _buildReadinessView(dynamic record) {
    final int score          = record['iriScore'] as int? ?? 0;
    final String status      = record['status'] as String? ?? '';
    final String narrative   = record['message'] as String? ?? '';
    final String ctxDetail   = record['contextDetail'] as String? ?? '';
    final bool isOffline     = record['isOfflineMode'] as bool? ?? false;
    final String timestamp   = _fmt(record['timestamp'] as String? ?? '');
    final Color color        = _statusColor(status);

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── Header ──────────────────────────────────────────────────────
          const SizedBox(height: 12),
          const Text('SNC READINESS',
            style: TextStyle(color: _cyan, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 3)),
          const SizedBox(height: 4),
          const Text('REGISTRO DIARIO',
            style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900)),
          Text(timestamp,
            style: const TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 36),

          // ── Ring animado ────────────────────────────────────────────────
          Center(
            child: SizedBox(
              width: 240,
              height: 240,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Glow de fondo
                  Container(
                    width: 240,
                    height: 240,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: color.withOpacity(0.04),
                    ),
                  ),
                  // Anillo de progreso — usa SizedBox para no solapar el contenido central
                  SizedBox(
                    width: 220,
                    height: 220,
                    child: CircularProgressIndicator(
                      value: score / 100,
                      strokeWidth: 10,
                      backgroundColor: Colors.white.withOpacity(0.06),
                      valueColor: AlwaysStoppedAnimation<Color>(color),
                      strokeCap: StrokeCap.round,
                    ),
                  ),
                  // Contenido central — garantizamos que cabe dentro del anillo (220 - 2*10 = 200)
                  SizedBox(
                    width: 180,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'IRI HOY',
                          style: const TextStyle(
                            color: Colors.white38,
                            fontSize: 9,
                            letterSpacing: 3,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 6),
                        FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            '$score',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 72,
                              fontWeight: FontWeight.w900,
                              height: 1.0,
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          _statusLabel(status),
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: color,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.0,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 48),


          // ── Narrativa ────────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: _surface,
              border: Border(left: BorderSide(color: color, width: 4)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Icon(Icons.lightbulb_outline_rounded, color: color, size: 16),
                  const SizedBox(width: 8),
                  Text('SUGERENCIAS PRÁCTICAS DIARIAS',
                    style: TextStyle(color: color, fontSize: 10,
                        fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                ]),
                const SizedBox(height: 14),
                Text(narrative,
                  style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.6, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Análisis de Hábitos ──────────────────────────────────────────
          if (ctxDetail.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(16),
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
                      Icon(Icons.insights_rounded, color: color, size: 14),
                      const SizedBox(width: 8),
                      Text(
                        'ANÁLISIS DE HÁBITOS',
                        style: TextStyle(color: color.withOpacity(0.8), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1.5),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    ctxDetail,
                    style: const TextStyle(color: Colors.white70, fontSize: 12, height: 1.5),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],

          // ── Mini cards ───────────────────────────────────────────────────
          Row(children: [
            _miniCard('ESTADO SNC', status, color),
            const SizedBox(width: 12),
            _miniCard('MOTOR', 'IRI v2.1', _cyan),
          ]),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // HELPERS
  // ─────────────────────────────────────────────────────────────────────────
  Widget _miniCard(String label, String value, Color valueColor) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
        decoration: BoxDecoration(
          color: _surface,
          border: Border.all(color: Colors.white.withOpacity(0.05)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(
                color: Colors.white38, fontSize: 8,
                letterSpacing: 1.5, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(
                color: valueColor, fontSize: 12, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Color _statusColor(String s) {
    if (s == 'VERDE')    return _green;
    if (s == 'AMARILLO') return _amber;
    if (s == 'ROJO')     return _red;
    return _cyan;
  }

  String _statusLabel(String s) {
    if (s == 'VERDE')    return 'ESTADO PRIME';
    if (s == 'AMARILLO') return 'MANTENIMIENTO';
    if (s == 'ROJO')     return 'RECUPERACIÓN';
    return 'SIN DATOS';
  }

  String _fmt(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return 'Hoy ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return '';
    }
  }
}
