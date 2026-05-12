import 'package:cloud_firestore/cloud_firestore.dart';

class PerformanceModel {
  final String id;
  final String athleteId;
  final String athleteName;
  final String date;
  final double iri;
  final int lapses;
  final double decelZ5;
  final double ivnScore;
  final String riskLevel;
  final String ivnLabel;
  final String action;
  final DateTime timestamp;

  PerformanceModel({
    required this.id,
    required this.athleteId,
    required this.athleteName,
    required this.date,
    required this.iri,
    required this.lapses,
    required this.decelZ5,
    required this.ivnScore,
    required this.riskLevel,
    required this.ivnLabel,
    required this.action,
    required this.timestamp,
  });

  factory PerformanceModel.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final gps = data['gps'] as Map<String, dynamic>? ?? {};
    
    return PerformanceModel(
      id: doc.id,
      athleteId: data['athleteId'] ?? '',
      athleteName: data['athleteName'] ?? 'Atleta',
      date: data['date'] ?? '',
      iri: (data['iri'] ?? 75.0).toDouble(),
      lapses: data['lapses'] ?? 0,
      decelZ5: (gps['decel_z5'] ?? gps['decel_high'] ?? 0.0).toDouble(),
      ivnScore: (data['ivn_score'] ?? 0.0).toDouble(),
      riskLevel: data['risk_level'] ?? 'GREEN',
      ivnLabel: data['ivn_label'] ?? 'ESTABLE',
      action: data['action'] ?? 'Mantener',
      timestamp: (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
    );
  }
}
