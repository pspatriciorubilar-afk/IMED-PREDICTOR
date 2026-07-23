import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:isar/isar.dart';
import '../domain/pvt_session.dart';

/**
 * MOTOR DE SINCRONIZACIÓN ÉLITE (IMED PREDICTOR)
 * Dominio: cognitive.neuro.elitemindpro.com
 * Protocolo: HTTPS (SSL/TLS 1.3)
 *
 * NOTA ARQUITECTURAL:
 * Este DataSource se encarga EXCLUSIVAMENTE de sincronizar con la API VPS propia.
 * La escritura a Firebase Firestore (measurements + Daily_Performance) la maneja
 * SyncService._executeFirestoreSync() llamado desde BiometricFlowCoordinator.
 * Tener dos escrituras a measurements/ generaba un doble registro porque el trigger
 * Cloud Function 'auto_sync_to_dashboard' se disparaba dos veces por sesión.
 */
class PvtDataSource {
  final Isar isar;
  
  // CAMBIO CRÍTICO: Producción VPS Hostinger (Puerto 3000)
  static const String baseUrl = "http://92.112.179.19:3000/api/v1";

  PvtDataSource(this.isar);

  Future<void> syncPendingSessions(
    String jwtToken, String athleteId, int age, String firstName, String lastName) async {
    final pending = await isar.collection<PvtSession>().filter().isSyncedEqualTo(false).findAll();

    if (pending.isEmpty) return;

    for (final session in pending) {
      try {
        String sessionTag = "STANDARD";
        final hour = session.timestamp.hour;
        if (hour >= 5 && hour < 11) sessionTag = "MORNING";
        if (hour >= 15) sessionTag = "PERFORMANCE";

        // ── SINCRONIZACIÓN CON API VPS PROPIA ────────────────────────────────
        // Esta es la única responsabilidad de PvtDataSource.
        // Firestore es manejado por SyncService para evitar duplicados.
        final response = await http.post(
          Uri.parse("$baseUrl/pvt/sync"),
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer $jwtToken"
          },
          body: jsonEncode({
            "athleteId": int.tryParse(athleteId) ?? 0,
            "reactionTime": session.meanLatency,
            "meanLatency": session.meanLatency,
            "lapsesCount": session.lapsesCount,
            "falseStarts": session.falseStarts,
            "testType": "PVT_STANDARD",
            "sessionTag": sessionTag,
          })
        ).timeout(const Duration(seconds: 10));
        
        if (response.statusCode == 201 || response.statusCode == 202) {
          await _markAsSynced(session);
          print("✅ [SYNC-SUCCESS] PVT ID ${session.id} sincronizado con API VPS.");
        } else {
          print("❌ [SYNC-ERROR] Servidor API respondió con código ${response.statusCode}");
        }

      } catch (e) {
        print("❌ [SYNC-FAILURE] Error de conexión con API VPS: $e");
        // No se re-lanza: el dato ya está en Firestore gracias a SyncService.
      }
    }
  }

  Future<void> _markAsSynced(PvtSession session) async {
    await isar.writeTxn(() async {
      session.isSynced = true;
      await isar.collection<PvtSession>().put(session);
    });
  }

  Future<String?> fetchLatestStatus(String jwtToken, String athleteId) async {
    try {
      final response = await http.get(
        Uri.parse("$baseUrl/v1/pvt/latest/$athleteId"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $jwtToken"
        },
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print("✅ [SYNC-LATEST] Status del servidor obtenido: ${data['status']}");
        return data['status'];
      }
      return null;
    } catch (e) {
      print("❌ [SYNC-ERROR] Fallo al consultar status: $e");
      return null;
    }
  }
}
