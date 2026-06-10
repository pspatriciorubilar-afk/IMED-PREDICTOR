// lib/features/cognitive_load/application/pvt_api_client.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../domain/pvt_session_metrics.dart';

class PvtApiClient {
  // Configuración de Hostinger (Ajustar a tu dominio real)
  static const String _baseUrl = "http://92.112.179.19:3000/api/v1"; 

  /// Sincroniza la sesión PVT con el backend Node.js.
  static Future<bool> syncSession(PvtSessionMetrics metrics, String jwt) async {
    const String endpoint = "$_baseUrl/v1/pvt/sync";

    try {
      final response = await http.post(
        Uri.parse(endpoint),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $jwt',
        },
        body: jsonEncode({
          'athleteId': 'patri-01', // TODO: Obtener del perfil real del usuario
          'meanLatency': metrics.meanReactionTime,
          'lapsesCount': metrics.lapsesCount,
          'falseStarts': metrics.falseStarts,
          'rawData': metrics.reactionTimesMs,
        }),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print("Sincronización Exitosa. Estado Atleta: ${data['status']}");
        return true;
      } else {
        print("Error en Sincronización: Cod ${response.statusCode}");
        return false;
      }
    } catch (e) {
      print("Falla de Network Crítica: $e");
      // TODO: Implementar guardado en Local Storage para reintento offline
      return false;
    }
  }
}
