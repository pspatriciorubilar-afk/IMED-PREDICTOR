import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:isar/isar.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../domain/pvt_session.dart';

/**
 * MOTOR DE SINCRONIZACIÓN ÉLITE (IMED PREDICTOR)
 * Dominio: cognitive.neuro.elitemindpro.com
 * Protocolo: HTTPS (SSL/TLS 1.3)
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
            "testType": "PVT_STANDARD"
          })
        ).timeout(const Duration(seconds: 10));
        
        if (response.statusCode == 201 || response.statusCode == 202) {
          // Sincronización exitosa con API propia
          await _markAsSynced(session);
          print("✅ [SYNC-SUCCESS] PVT ID ${session.id} sincronizado con API.");
        } else {
          print("❌ [SYNC-ERROR] Servidor API respondió con código ${response.statusCode}");
        }

        // --- NUEVO: Sincronización con Firebase Firestore ---
        await _syncToFirestore(session, athleteId);

      } catch (e) {
        print("❌ [SYNC-FAILURE] Error de conexión: $e");
      }
    }
  }

  Future<void> _syncToFirestore(PvtSession session, String athleteId) async {
    try {
      final firestore = FirebaseFirestore.instance;
      final dateStr = session.timestamp.toLocal().toString().split(' ')[0]; // YYYY-MM-DD

      // ── Estructura requerida por auto_sync_to_dashboard Cloud Function ──
      // Colección: athletes/{athleteId}/measurements/{auto-id}
      // El trigger de Firestore detecta la creación y sincroniza a Daily_Performance.
      await firestore
          .collection('athletes')
          .doc(athleteId)
          .collection('measurements')
          .add({
        // Identificación temporal
        "date":      dateStr,
        "timestamp": session.timestamp.toIso8601String(),

        // Resultado IRI (calculado localmente por SNCEngine)
        "iri":    0,    // TODO: pasar el IRI calculado por SNCEngine desde el notifier
        "status": "PENDING",

        // Objeto PVT — estructura que lee la Cloud Function y el worker Ex-Gaussiano
        "pvt": {
          "metrics": {
            "meanLatency": session.meanLatency,
            "lapses":      session.lapsesCount,
            "falseStarts": session.falseStarts,
            // ⭐ CAMPO CRÍTICO: array crudo requerido por pvt_exgauss_worker.py
            "trials":          session.rawReactionTimes,
            "rawReactionTimes": session.rawReactionTimes,
            "n_trials":        session.rawReactionTimes.length,
          }
        },

        // Wellness — se rellenará cuando se integre el flujo biométrico completo
        "wellness": null,

        // Metadatos
        "sync_method": "flutter_pvt_data_source_v2",
        "pvt_protocol": "PVT-B-30",
        "syncedAt": FieldValue.serverTimestamp(),
      });

      print("🔥 [FIREBASE] Sesión guardada en athletes/$athleteId/measurements/ (${session.rawReactionTimes.length} trials)");
    } catch (e) {
      print("🔥 [FIREBASE-ERROR] Error al guardar en Firestore: $e");
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
