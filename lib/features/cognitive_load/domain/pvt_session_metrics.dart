// lib/features/cognitive_load/domain/pvt_session_metrics.dart
import 'package:flutter/foundation.dart';

/// Entidad inmutable que representa las métricas de una sesión PVT.
/// Diseñada para ser fácilmente serializable hacia JSON o una base local sólida.
@immutable
class PvtSessionMetrics {
  final List<int> reactionTimesMs;
  final int falseStarts;
  final double meanReactionTime;
  final int lapsesCount; // > 500ms
  final DateTime sessionDate;

  const PvtSessionMetrics({
    required this.reactionTimesMs,
    required this.falseStarts,
    required this.meanReactionTime,
    required this.lapsesCount,
    required this.sessionDate,
  });

  /// Crea las métricas calculadas puras basadas en Raw Data recolectada.
  factory PvtSessionMetrics.fromRawData(List<int> rawTimes, int falseStartsAmount) {
    int lapseCounter = 0;
    int totalTime = 0;
    
    for (int time in rawTimes) {
      if (time > 500) {
        lapseCounter++;
      }
      totalTime += time;
    }

    final double mean = rawTimes.isEmpty ? 0.0 : (totalTime / rawTimes.length);

    return PvtSessionMetrics(
      reactionTimesMs: List.unmodifiable(rawTimes),
      falseStarts: falseStartsAmount,
      meanReactionTime: mean,
      lapsesCount: lapseCounter,
      sessionDate: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'reactionTimesMs': reactionTimesMs,
      'falseStarts': falseStarts,
      'meanReactionTime': meanReactionTime,
      'lapsesCount': lapsesCount,
      'sessionDate': sessionDate.toIso8601String(),
    };
  }
}
