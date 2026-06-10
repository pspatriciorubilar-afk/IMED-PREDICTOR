class WellnessSurvey {
  final double sleepHours;
  final int sleepQuality; // 1-5
  final int stressLevel;  // 1-5
  final int fatigueLevel; // 1-5

  WellnessSurvey({
    required this.sleepHours,
    required this.sleepQuality,
    required this.stressLevel,
    required this.fatigueLevel,
  });

  Map<String, dynamic> toJson() => {
    'sleep_hours': sleepHours,
    'sleep_quality': sleepQuality,
    'stress_level': stressLevel,
    'fatigue_level': fatigueLevel,
  };
}

class BiometricPayload {
  final String athleteId;
  final DateTime timestamp;
  final WellnessSurvey wellness;
  final List<int> pvtLog;

  BiometricPayload({
    required this.athleteId,
    required this.timestamp,
    required this.wellness,
    required this.pvtLog,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'athleteId': athleteId,
      'timestamp': timestamp.toIso8601String(),
    };
    
    // Unir todos los datos en el objeto raíz según requiere el backend v2.1
    data.addAll(wellness.toJson());
    data['pvt_logs'] = pvtLog;
    
    return data;
  }
}
