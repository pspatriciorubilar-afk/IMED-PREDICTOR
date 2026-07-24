import 'dart:convert';
import 'dart:async';
import 'dart:io';
import 'package:hive/hive.dart';
import 'package:http/http.dart' as http;
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../features/biometrics/domain/biometric_models.dart';
import '../biometrics/snc_engine.dart';

class SyncService {
  static const String _baseUrl = 'http://92.112.179.19/api/v3';
  static const String _boxName = 'sync_queue';

  /// Inicializa Hive para la cola de sincronización
  static Future<void> init() async {
    if (!Hive.isBoxOpen(_boxName)) {
      await Hive.openBox(_boxName);
    }
  }

  /// Envía los datos biométricos y gestiona la cola local
  static Future<bool> sendBiometrics(
    BiometricPayload payload, 
    String token, 
    {Map<String, dynamic>? profileData}
  ) async {
    try {
      // 1. Intentar subir a Firebase primero (Datos enriquecidos para Dashboard)
      await _syncToFirestore(payload, profileData: profileData);

      // 2. Intentar subir a la API principal
      final response = await http.post(
        Uri.parse('$_baseUrl/metrics'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(payload.toJson()),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200 || response.statusCode == 201) {
        // Éxito: Procesar cola si hay algo pendiente
        await processQueue(token);
        return true;
      } else {
        // Falló API principal: Guardar en cola local
        await _saveToQueue(payload);
        return true; 
      }
    } catch (e) {
      print("📡 [SYNC] Error de red, encolando localmente: $e");
      await _saveToQueue(payload);
      return true;
    }
  }

  /// Obtiene el diagnóstico de Readiness en tiempo real
  static Future<Map<String, dynamic>> getReadiness(String token) async {
    final url = Uri.parse('$_baseUrl/readiness');
    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("📡 Error fetching readiness: $e");
    }
    return {'status': 'OFFLINE', 'readinessScore': 0, 'message': 'Sin conexión con el servidor.'};
  }

  /// Obtiene las tendencias de los últimos 7 días para gráficas
  static Future<List<dynamic>> getTrends(String token) async {
    final url = Uri.parse('$_baseUrl/trends');
    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("📡 Error fetching trends: $e");
    }
    return [];
  }

  /// Guarda una medición en la cola local de Hive
  static Future<void> _saveToQueue(BiometricPayload payload) async {
    final box = Hive.box(_boxName);
    final jsonBody = jsonEncode(payload.toJson());
    
    await box.add({
      'body': jsonBody,
      'timestamp': DateTime.now().toIso8601String(),
      'pending_sync': true,
    });
    print("📦 [QUEUE] Medición guardada localmente.");
  }

  /// Procesa la cola de pendientes
  static Future<void> processQueue(String token) async {
    final box = Hive.box(_boxName);
    if (box.isEmpty) return;

    print("🔄 [SYNC] Procesando cola (${box.length})...");
    
    final keysToDelete = [];
    for (var key in box.keys) {
      final item = box.get(key);
      try {
        final decodedBody = jsonDecode(item['body']) as Map<String, dynamic>;
        
        // 1. Intentar enviar a la API principal
        final response = await http.post(
          Uri.parse('$_baseUrl/metrics'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $token',
          },
          body: item['body'],
        ).timeout(const Duration(seconds: 10));

        // 2. Intentar enviar a Firebase (siempre, para asegurar consistencia)
        await _syncFromRawData(decodedBody);

        if (response.statusCode == 200 || response.statusCode == 201 || response.statusCode == 404) {
          keysToDelete.add(key);
        }
      } catch (e) {
        print("📡 [SYNC-ERROR] Falló procesamiento de item: $e");
        break; 
      }
    }

    for (var key in keysToDelete) {
      await box.delete(key);
    }
    print("✅ [SYNC] Cola procesada.");
  }

  /// Helper para sincronizar datos crudos desde la cola a Firestore
  static Future<void> _syncFromRawData(Map<String, dynamic> data) async {
    try {
      final List<int> pvtLog = List<int>.from(data['pvt_logs'] ?? []);
      final athleteId = data['athleteId'] ?? 'unknown_athlete';
      
      await _executeFirestoreSync(athleteId, pvtLog, data, DateTime.parse(data['timestamp']));
    } catch (e) {
      print("🔥 [FIREBASE-QUEUE-ERROR] $e");
    }
  }

  /// Envía los datos biométricos a Firebase Firestore con métricas enriquecidas
  static Future<void> _syncToFirestore(
    BiometricPayload payload, 
    {Map<String, dynamic>? profileData}
  ) async {
    final Map<String, dynamic> wellnessData = payload.wellness.toJson();
    await _executeFirestoreSync(
      payload.athleteId, 
      payload.pvtLog, 
      wellnessData, 
      payload.timestamp,
      extraProfileData: profileData
    );
  }

  /// Ejecución real de la subida a Firestore con cálculo de métricas
  static Future<void> _executeFirestoreSync(
    String athleteId, 
    List<int> pvtLog, 
    Map<String, dynamic> wellnessData,
    DateTime timestamp,
    {Map<String, dynamic>? extraProfileData}
  ) async {
    try {
      final firestore = FirebaseFirestore.instance;
      
      final validLogs = pvtLog.where((t) => t > 100).toList();
      final int lapses = validLogs.where((t) => t > 500).length;
      final double mean = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a + b) / validLogs.length;
      final int fastest = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a < b ? a : b);
      final int slowest = validLogs.isEmpty ? 0 : validLogs.reduce((a, b) => a > b ? a : b);

      // Algoritmo SNC Engine
      final wellness = WellnessSurvey(
        sleepHours: (wellnessData['sleep_hours'] ?? 0).toDouble(),
        sleepQuality: wellnessData['sleep_quality'] ?? 0,
        stressLevel: wellnessData['stress_level'] ?? 0,
        fatigueLevel: wellnessData['fatigue_level'] ?? 0,
      );
      final int iriScore = SNCEngine.calculateIRIWithContext(0.0, pvtLog, wellness);
      final String statusSNC = SNCEngine.getStatus(iriScore);

      // Usar un WriteBatch para asegurar atomicidad y evitar condiciones de carrera (Race Conditions) en los Dashboards
      final WriteBatch batch = firestore.batch();

      // 1. Referencia al Atleta
      final athleteRef = firestore.collection('athletes').doc(athleteId);
      batch.set(athleteRef, {
        'lastActive': timestamp,
        'id': athleteId,
        'lastIRI': iriScore,
        'lastStatus': statusSNC,
        if (extraProfileData != null) ...extraProfileData,
      }, SetOptions(merge: true));

      // 2. Referencia a la Medición (usamos .doc() para autogenerar ID)
      // CRÍTICO: Usar .toLocal() para que la fecha refleje el día calendario
      // del atleta y no la fecha UTC (que puede ser diferente en zonas -4 o más).
      final localTimestamp = timestamp.toLocal();
      final String dateStr = "${localTimestamp.year}-${localTimestamp.month.toString().padLeft(2, '0')}-${localTimestamp.day.toString().padLeft(2, '0')}";
      final measurementRef = firestore.collection('athletes').doc(athleteId).collection('measurements').doc();
      batch.set(measurementRef, {
        "timestamp": localTimestamp.toIso8601String(),
        "date": dateStr,
        "iri": iriScore,
        "status": statusSNC,
        "wellness": {
          "sleepHours": wellnessData['sleep_hours'],
          "sleepQuality": wellnessData['sleep_quality'],
          "stressLevel": wellnessData['stress_level'],
          "fatigueLevel": wellnessData['fatigue_level'],
        },
        "pvt": {
          "logs": pvtLog,
          "metrics": {
            "meanLatency": mean.round(),
            "lapses": lapses,
            "fastest": fastest,
            "slowest": slowest,
            "totalTrials": pvtLog.length,
            // CRÍTICO: Arrays de trials crudos requeridos por el worker Ex-Gaussiano
            // y por pvt_data_source. Ambas claves se incluyen para compatibilidad.
            "trials": pvtLog,
            "rawReactionTimes": pvtLog,
          }
        },
        "deviceInfo": {
          "platform": Platform.isAndroid ? "Android" : "iOS",
          "version": "v3.0-Production"
        },
        "syncedAt": FieldValue.serverTimestamp(),
      });

      // 3. Referencia a Daily_Performance (incluir wellness + pvt para el dashboard)
      // El ID del documento usa dateStr local para que coincida con el filtro 'today'
      // del dashboard que también usa la fecha local del navegador.
      final dailyRef = firestore.collection('Daily_Performance').doc('${athleteId}_$dateStr');
      batch.set(dailyRef, {
        "athleteId": athleteId,
        "athleteName": extraProfileData?['firstName'] != null
            ? '${extraProfileData!['firstName']} ${extraProfileData['lastName'] ?? ''}'.trim()
            : athleteId,
        "date": dateStr,
        "iri": iriScore,
        "status": statusSNC,
        "lapses": lapses,
        if (extraProfileData?['tenantId'] != null) "tenantId": extraProfileData?['tenantId'],
        "wellness": {
          "sleepHours":   wellnessData['sleep_hours'],
          "sleepQuality": wellnessData['sleep_quality'],
          "stressLevel":  wellnessData['stress_level'],
          "fatigueLevel": wellnessData['fatigue_level'],
        },
        "pvt": {
          "metrics": {
            "meanLatency": mean.round(),
            "lapses":      lapses,
            "fastest":     fastest,
            "slowest":     slowest,
            "totalTrials": pvtLog.length,
            // CRÍTICO: Arrays de trials crudos para el trigger auto_sync_to_dashboard
            "trials": pvtLog,
            "rawReactionTimes": pvtLog,
          }
        },
        "timestamp": FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));

      // Ejecutar todo el lote de forma atómica
      await batch.commit();

      print("🔥 [FIREBASE] Datos guardados con éxito en batch para $athleteId.");
    } catch (e) {
      print("🔥 [FIREBASE-ERROR] $e");
    }
  }
}
