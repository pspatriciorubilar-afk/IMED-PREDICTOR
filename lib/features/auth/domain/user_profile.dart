import 'package:isar/isar.dart';

part 'user_profile.g.dart';

enum Chronotype { morning, intermediate, evening }

@collection
class UserProfile {
  Id id = Isar.autoIncrement;

  late String athleteId;    // "patricio_rubilar_35" — ID humano y legible
  late String firstName;    // NUEVO: Nombre
  late String lastName;     // NUEVO: Apellido
  late int age;             // Vital para análisis neuro-circadiano
  late String sport;

  @enumerated
  late Chronotype chronotype;
  
  late int preferredTrainingHour;
  late int preferredWakeMinute; // NUEVO: Minutos para precisión
  late DateTime registeredAt;

  String? associationCode;  // Código maestro de asociación (ej. COLO26)
  String? tenantId;         // ID de inquilino resuelto

  UserProfile({
    required this.athleteId,
    required this.firstName,
    required this.lastName,
    required this.age,
    this.sport = 'General',
    this.chronotype = Chronotype.intermediate,
    this.preferredTrainingHour = 10,
    this.preferredWakeMinute = 0,
    required this.registeredAt,
    this.associationCode,
    this.tenantId,
  });

  /// Retorna el nombre completo para mostrar en la UI
  String get fullName => '$firstName $lastName';
}
