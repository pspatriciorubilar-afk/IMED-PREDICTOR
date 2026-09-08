import 'dart:async';
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'wellness_screen.dart';
import '../../cognitive_load/presentation/widgets/pvt_test_widget.dart';
import 'readiness_dashboard_screen.dart';
import 'package:isar/isar.dart';
import '../../auth/domain/user_profile.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../domain/biometric_models.dart';
import '../../../core/network/sync_service.dart';
import '../../../core/biometrics/snc_engine.dart';


class BiometricFlowCoordinator extends StatefulWidget {
  final Isar isar;
  const BiometricFlowCoordinator({super.key, required this.isar});

  @override
  State<BiometricFlowCoordinator> createState() => _BiometricFlowCoordinatorState();
}


class _BiometricFlowCoordinatorState extends State<BiometricFlowCoordinator> {
  int _currentStep = 0;
  bool _isRestricted = false;
  bool _isChecking = true; // Nuevo: Shield de verificación inicial
  DateTime? _lastTestTime;

  WellnessSurvey? _wellnessData;
  List<int>? _pvtLog;
  Map<String, dynamic>? _readinessData;

  int _pvtRetakeCount = 0; // Fuerza reconstrucción del widget en cada retake
  UserProfile? _userProfile;

  @override
  void initState() {
    super.initState();
    _checkStatus();
  }

  Future<void> _checkStatus() async {
    try {
      await _loadProfile();
      await _checkRestriction();
    } finally {
      if (mounted) setState(() => _isChecking = false);
    }
  }

  Future<void> _loadProfile() async {
    try {
      final profile = await widget.isar.collection<UserProfile>().where().findFirst();
      if (mounted) {
        setState(() => _userProfile = profile);
      }
    } catch (e) {
      debugPrint("⚠️ Error cargando perfil: $e");
    }
  }

  /// Verifica si ya se realizó una prueba en el día calendario actual
  Future<void> _checkRestriction() async {
    try {
      final box = Hive.isBoxOpen('daily_readiness')
          ? Hive.box('daily_readiness')
          : await Hive.openBox('daily_readiness');

      final lastData = box.get('today');
      if (lastData != null && lastData['timestamp'] != null) {
        final lastTimestamp = DateTime.parse(lastData['timestamp']);
        final now = DateTime.now();

        // Restricción activa si el año, mes y día coinciden con 'hoy'
        if (lastTimestamp.year == now.year &&
            lastTimestamp.month == now.month &&
            lastTimestamp.day == now.day) {
          setState(() {
            _isRestricted = true;
            _lastTestTime = lastTimestamp;
          });
        }
      }
    } catch (e) {
      debugPrint("⚠️ Error verificando restricción: $e");
    }
  }

  void _nextStep() {
    setState(() => _currentStep++);
  }

  void _finishProcessing(Map<String, dynamic> data) {
    if (mounted) {
      setState(() {
        _readinessData = data;
        _currentStep = 4;
        _isRestricted = true; // Bloqueo inmediato tras éxito
      });
    }
  }

  void _retakePvt() {
    // Si ya hay restricción activa, impedimos el re-test
    if (_isRestricted) return;

    setState(() {
      _pvtLog = null;
      _readinessData = null;
      _pvtRetakeCount++;
      _currentStep = 1;
    });
  }

  @override
  Widget build(BuildContext context) {
    // 1. Shield de verificación inicial
    if (_isChecking) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF))),
      );
    }

    // 2. BLOQUEO ABSOLUTO: Si hay restricción y no estamos viendo el Dashboard final (paso 4), 
    // mostramos SÍ O SÍ la pantalla de restricción.
    if (_isRestricted && _currentStep < 4) {
      return _RestrictedScreen(
        onBack: () {
          // Intentar salir del flujo modal si existe
          if (Navigator.canPop(context)) {
            Navigator.pop(context);
          } else {
            // Si es una pestaña, simplemente forzamos la vista al Dashboard si hay datos
            // o nos quedamos aquí. No reseteamos _isRestricted.
            if (_readinessData != null) {
              setState(() => _currentStep = 4);
            }
          }
        },
      );
    }

    switch (_currentStep) {
      case 0:
        return WellnessScreen(
          onComplete: (hours, quality, stress, fatigue) {
            _wellnessData = WellnessSurvey(
              sleepHours: hours,
              sleepQuality: quality,
              stressLevel: stress,
              fatigueLevel: fatigue,
            );
            _nextStep();
          },
        );
      case 1:
        // UniqueKey basado en _pvtRetakeCount: fuerza reconstrucción total
        // del PvtTestWidget y su provider en cada nueva prueba.
        return Scaffold(
          body: PvtTestWidget(
            key: ValueKey('pvt_$_pvtRetakeCount'),
            onComplete: (logs) {
              _pvtLog = logs;
              setState(() => _currentStep = 3);
            },
          ),
        );
      case 2:
        return const SizedBox.shrink();
      case 3:
        // CRÍTICO: Verificar que el athleteId real esté disponible.
        // Si el perfil no cargó, mostrar error en lugar de usar un ID basura
        // que haría el dato invisible en el Dashboard.
        if (_userProfile == null || (_userProfile!.athleteId?.isEmpty ?? true)) {
          return Scaffold(
            backgroundColor: Colors.black,
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline, color: Color(0xFFFF4D4D), size: 64),
                    const SizedBox(height: 24),
                    const Text(
                      'PERFIL NO ENCONTRADO',
                      style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 1.5),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'No se pudo encontrar tu perfil de deportista. Cierra la app y vuelve a abrirla. Si el problema persiste, contacta a tu entrenador.',
                      style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13, height: 1.5),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: () => setState(() => _currentStep = 0),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00E5FF).withOpacity(0.15),
                        foregroundColor: const Color(0xFF00E5FF),
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text('REINTENTAR'),
                    ),
                  ],
                ),
              ),
            ),
          );
        }
        
        return _ProcessingScreen(
          payload: BiometricPayload(
            athleteId: _userProfile!.athleteId!,
            timestamp: DateTime.now(),
            wellness: _wellnessData!,
            pvtLog: _pvtLog!,
          ),
          onResult: _finishProcessing,
          isar: widget.isar,
        );

      case 4:
        return ReadinessDashboardScreen(
          readinessData: _readinessData!,
          token: "imed-sport-token-mock",
          onRetake: _retakePvt,
        );
      default:
        return const Center(child: CircularProgressIndicator());
    }
  }

}

/// Pantalla informativa de restricción temporal (Protección de Integridad de Datos)
class _RestrictedScreen extends StatelessWidget {
  final VoidCallback onBack;

  const _RestrictedScreen({required this.onBack});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Padding(
        padding: const EdgeInsets.all(40.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.history_toggle_off_rounded, color: Color(0xFF00E5FF), size: 80),
            const SizedBox(height: 32),
            const Text(
              "EVALUACIÓN COMPLETADA",
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white, 
                fontSize: 22, 
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              "Para garantizar la precisión de tu línea base, solo se permite una evaluación diaria. Tu sistema ya ha registrado la telemetría correspondiente al día de hoy.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14, height: 1.5),
            ),
            const SizedBox(height: 48),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 24),
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF111111),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withOpacity(0.05)),
              ),
              child: const Column(
                children: [
                  Icon(Icons.check_circle_outline, color: Color(0xFF00E5FF), size: 32),
                  SizedBox(height: 16),
                  Text(
                    "INTEGRIDAD DE DATOS ACTIVA",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 64),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onBack,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white.withOpacity(0.05),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 0,
                ),
                child: const Text("ENTENDIDO", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PANTALLA DE PROCESAMIENTO AUTÓNOMA
// Separada del coordinador para aislar completamente el ciclo de red de la UI.
// Ejecuta toda la lógica de red en initState() con Deadman Switch de 12s.
// ─────────────────────────────────────────────────────────────────────────────
class _ProcessingScreen extends StatefulWidget {
  final BiometricPayload payload;
  final Function(Map<String, dynamic>) onResult;
  final Isar isar;

  const _ProcessingScreen({
    required this.payload, 
    required this.onResult,
    required this.isar,
  });

  @override
  State<_ProcessingScreen> createState() => _ProcessingScreenState();
}


class _ProcessingScreenState extends State<_ProcessingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  String _statusMessage = "Estableciendo conexión segura...";

  @override
  void initState() {
    super.initState();

    // Animación de pulso del logo
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    // Inicia el proceso de red en el siguiente frame,
    // garantizando que el widget tree anterior ya fue destruido.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _runSyncWithDeadmanSwitch();
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _runSyncWithDeadmanSwitch() async {
    Map<String, dynamic> readiness;

    try {
      _setStatus("Enviando telemetría biométrica...");

      // DEADMAN SWITCH GLOBAL: 12s para todo el proceso
      readiness = await Future.any([
        _performCompleteSync(widget.payload),
        Future.delayed(
          const Duration(seconds: 12),
          () => throw TimeoutException("Tiempo de espera agotado"),
        ),
      ]);

    } catch (e) {
      // FALLBACK INMEDIATO: IRI con contexto del cuestionario diario y regla de lapsos
      _setStatus("Calculando rendimiento local...");
      final localScore = SNCEngine.calculateIRIFromPayload(widget.payload);
      final baseScore = SNCEngine.calculateIRI(
        0.0, // Ya no se usa HRV
        widget.payload.pvtLog,
      );
      final validLogs = widget.payload.pvtLog.where((t) => t > 100).toList();
      final int lapses = validLogs.where((t) => t > 500).length;
      final int slowest = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a > b ? a : b);
      final int fastest = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a < b ? a : b);
      final int meanLatency = validLogs.isEmpty ? 0 : (validLogs.reduce((a, b) => a + b) / validLogs.length).round();
      final String localStatus = SNCEngine.getStatus(localScore, lapses: lapses);
      final String localNarrative = SNCEngine.getNarrativeFeedback(localScore, lapses: lapses, slowestMs: slowest);
      final String localContext = SNCEngine.getContextualNarrative(
        baseScore, localScore, widget.payload.wellness,
        lapses: lapses, slowestMs: slowest,
      );
      readiness = {
        'status': localStatus,
        'readinessScore': localScore,
        'message': localNarrative,
        'contextDetail': localContext,
        'lapses': lapses,
        'slowest': slowest,
        'fastest': fastest,
        'meanLatency': meanLatency,
        'totalTrials': validLogs.length,
        'isOfflineMode': true,
      };
    }

    // PERSISTENCIA SIEMPRE: Guardar el resultado del día en caja dedicada
    // Esto permite que el módulo 'Registro Diario' acceda al dato
    // independientemente de si hubo conexión o no.
    await _saveDailyReadiness(readiness);

    // Notificar al coordinador en lugar de usar Navigator directo
    if (mounted) {
      widget.onResult(readiness);
    }
  }

  /// Persiste el resultado del día en la caja Hive 'daily_readiness'.
  /// Sobrescribe el registro anterior con la clave fija 'today'.
  static Future<void> _saveDailyReadiness(Map<String, dynamic> readiness) async {
    try {
      final box = Hive.isBoxOpen('daily_readiness')
          ? Hive.box('daily_readiness')
          : await Hive.openBox('daily_readiness');

      await box.put('today', {
        'iriScore':      readiness['readinessScore'] ?? 0,
        'status':        readiness['status'] ?? '',
        'message':       readiness['message'] ?? '',
        'contextDetail': readiness['contextDetail'] ?? '',
        'lapses':        readiness['lapses'] ?? 0,
        'slowest':       readiness['slowest'] ?? 0,
        'fastest':       readiness['fastest'] ?? 0,
        'meanLatency':   readiness['meanLatency'] ?? 0,
        'totalTrials':   readiness['totalTrials'] ?? 0,
        'isOfflineMode': readiness['isOfflineMode'] ?? false,
        'timestamp':     DateTime.now().toIso8601String(),
      });
    } catch (e) {
      // No bloquear la navegación si falla el guardado local
      print('⚠️ [DailyReadiness] Error guardando registro: $e');
    }
  }

  Future<Map<String, dynamic>> _performCompleteSync(BiometricPayload payload) async {
    const token = "imed-sport-token-mock";

    final validLogs = payload.pvtLog.where((t) => t > 100).toList();
    final int lapses = validLogs.where((t) => t > 500).length;
    final int slowest = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a > b ? a : b);
    final int fastest = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a < b ? a : b);
    final int meanLatency = validLogs.isEmpty ? 0 : (validLogs.reduce((a, b) => a + b) / validLogs.length).round();

    // Siempre calculamos el contexto localmente con soporte de lapses
    final localScore = SNCEngine.calculateIRIFromPayload(payload);
    final baseScore = SNCEngine.calculateIRI(0.0, payload.pvtLog);
    final localStatus = SNCEngine.getStatus(localScore, lapses: lapses);
    final localNarrative = SNCEngine.getNarrativeFeedback(localScore, lapses: lapses, slowestMs: slowest);
    final localContext = SNCEngine.getContextualNarrative(
      baseScore, localScore, payload.wellness,
      lapses: lapses, slowestMs: slowest,
    );

    // Recuperar perfil real del deportista
    final userProfile = await widget.isar.collection<UserProfile>().where().findFirst();
    if (userProfile != null && userProfile.tenantId == null && userProfile.associationCode != null) {
      try {
        var querySnap = await FirebaseFirestore.instance
            .collection('tenants')
            .where('associationCode', isEqualTo: userProfile.associationCode)
            .limit(1)
            .get()
            .timeout(const Duration(seconds: 4));
        if (querySnap.docs.isEmpty) {
          final c = userProfile.associationCode!;
          final List<String> variations = [];
          if (c.contains('0')) variations.add(c.replaceAll('0', 'O'));
          if (c.contains('O')) variations.add(c.replaceAll('O', '0'));
          for (final alt in variations) {
            try {
              final altSnap = await FirebaseFirestore.instance
                  .collection('tenants')
                  .where('associationCode', isEqualTo: alt)
                  .limit(1)
                  .get()
                  .timeout(const Duration(seconds: 3));
              if (altSnap.docs.isNotEmpty) {
                querySnap = altSnap;
                break;
              }
            } catch (_) {}
          }
        }
        if (querySnap.docs.isNotEmpty) {
          userProfile.tenantId = querySnap.docs[0].id;
          final actualCode = querySnap.docs[0].data()['associationCode'] as String?;
          if (actualCode != null) userProfile.associationCode = actualCode;
          await widget.isar.writeTxn(() => widget.isar.collection<UserProfile>().put(userProfile));
        }
      } catch (e) {
        print("📡 [SYNC] Error al resolver tenantId online: $e");
      }
    }

    final profileData = userProfile != null ? {
      'firstName': userProfile.firstName,
      'lastName': userProfile.lastName,
      'age': userProfile.age,
      'tenantId': userProfile.tenantId,
      'associationCode': userProfile.associationCode,
    } : null;

    final syncSuccess = await SyncService.sendBiometrics(payload, token, profileData: profileData);


    if (syncSuccess) {
      _setStatus("Analizando readiness SNC...");
      final readiness = await SyncService.getReadiness(token);
      if (readiness['status'] != 'OFFLINE') {
        readiness['isOfflineMode'] = false;
        // Inyectar el contexto local en la respuesta del servidor
        readiness['contextDetail'] = localContext;
        readiness['lapses'] = lapses;
        readiness['slowest'] = slowest;
        readiness['fastest'] = fastest;
        readiness['meanLatency'] = meanLatency;
        readiness['totalTrials'] = validLogs.length;
        return readiness;
      }
    }

    // Servidor offline: IRI con contexto del cuestionario como fuente de verdad
    return {
      'status': localStatus,
      'readinessScore': localScore,
      'message': localNarrative,
      'contextDetail': localContext,
      'lapses': lapses,
      'slowest': slowest,
      'fastest': fastest,
      'meanLatency': meanLatency,
      'totalTrials': validLogs.length,
      'isOfflineMode': true,
    };
  }

  void _setStatus(String message) {
    if (mounted) setState(() => _statusMessage = message);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Ring de pulso animado
            AnimatedBuilder(
              animation: _pulseController,
              builder: (_, __) => Container(
                width: 100 + (_pulseController.value * 20),
                height: 100 + (_pulseController.value * 20),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: const Color(0xFF00E5FF).withOpacity(0.15 + _pulseController.value * 0.2),
                    width: 1.5,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 32),
            const CircularProgressIndicator(
              color: Color(0xFF00E5FF),
              strokeWidth: 2,
            ),
            const SizedBox(height: 32),
            const Text(
              "ANALIZANDO SNC",
              style: TextStyle(
                color: Color(0xFF00E5FF),
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 3,
              ),
            ),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 48),
              child: Text(
                _statusMessage,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white38, fontSize: 12),
              ),
            ),
            const SizedBox(height: 48),
            const Text(
              "Máx. 12 segundos",
              style: TextStyle(color: Colors.white12, fontSize: 10, letterSpacing: 1),
            ),
          ],
        ),
      ),
    );
  }
}
