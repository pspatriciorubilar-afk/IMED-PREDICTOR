import 'dart:math';
import '../../features/biometrics/domain/biometric_models.dart';

/// Motor local de Inteligencia de Rendimiento para el Sistema Nervioso Central.
/// 
/// FÓRMULA COMPLETA (v2.1):
///   IRIFinal = IRIBase × contextModifier
///
/// IRIBase (señales objetivas):
///   100% PVT  — Velocidad de reacción neural (latencia cognitiva)
///
/// contextModifier (señales subjetivas del cuestionario diario):
///   Sueño   — Horas + Calidad percibida (mayor impacto)
///   Estrés  — Penaliza la capacidad de adaptación
///   Fatiga  — Penaliza la disponibilidad muscular
///   DOMS    — Ajuste por carga mecánica periférica (menor impacto)
class SNCEngine {

  // ───────────────────────────────────────────────────────────────────────────
  // CÁLCULO DEL IRI BASE (solo datos objetivos: PVT)
  // ───────────────────────────────────────────────────────────────────────────

  /// Calcula el Índice de Resiliencia Neural (IRI) base.
  /// Usar [calculateIRIWithContext] cuando se disponga del cuestionario diario.
  static int calculateIRI(double _, List<int> pvtLatencies) {
    return _computeBase(pvtLatencies).round();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // CÁLCULO COMPLETO CON MODIFICADOR CONTEXTUAL (Wellness Survey)
  // ───────────────────────────────────────────────────────────────────────────

  /// Calcula el IRI incorporando el cuestionario de bienestar diario como
  /// modificador contextual. Este es el método preferido cuando el flujo
  /// completo Wellness → PVT está disponible.
  ///
  /// El modificador puede reducir el IRI hasta un 20% (fatiga/estrés extremos)
  /// o aumentarlo hasta un 8% (sueño óptimo con recuperación completa).
  static int calculateIRIWithContext(double _, List<int> pvtLatencies, WellnessSurvey wellness) {
    final base = _computeBase(pvtLatencies);
    final modifier = _computeContextModifier(wellness);
    final adjusted = (base * modifier).clamp(0.0, 100.0);
    return adjusted.round();
  }

  /// Calcula el IRI completo directamente desde un [BiometricPayload].
  static int calculateIRIFromPayload(BiometricPayload payload) {
    return calculateIRIWithContext(
      0.0,
      payload.pvtLog,
      payload.wellness,
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // MOTOR INTERNO
  // ───────────────────────────────────────────────────────────────────────────

  static double _computeBase(List<int> pvtLatencies) {
    if (pvtLatencies.isEmpty) return 0;

    // 1. Normalizar PVT
    // 250ms = élite (100 pts) → 500ms = fatiga extrema (0 pts) — inverso
    final meanPvt = pvtLatencies.reduce((a, b) => a + b) / pvtLatencies.length;
    final pvtScore = (100 - ((meanPvt - 250) / (500 - 250)) * 100).clamp(0.0, 100.0);

    // 3. Fusión (Neural Resilience Index base - Solo PVT)
    return pvtScore;
  }

  /// Calcula el modificador contextual del cuestionario de bienestar.
  /// Retorna un factor entre 0.80 y 1.08 que ajusta el IRI base.
  ///
  /// Pesos clínicos asignados según impacto en rendimiento deportivo:
  ///   Sueño (horas)    35% — Factor más determinante en recuperación SNC
  ///   Calidad sueño    25% — Calidad subjetiva percibida
  ///   Estrés percibido 20% — Eje HPA: cortisol / fatiga cognitiva
  ///   Fatiga general   20% — Estado de preparación neuromuscular
  static double _computeContextModifier(WellnessSurvey w) {
    // Sueño — horas (óptimo: 8h, mínimo deportivo: 5h)
    // Por debajo de 5h: penalización severa; 8-9h: bonus leve
    final sleepHoursFactor = _normalizeSleepHours(w.sleepHours);

    // Calidad de sueño (escala 1-5, 5 = perfecta)
    final sleepQualityFactor = _normalizeScale5(w.sleepQuality);

    // Estrés (escala 1-5, 1 = sin estrés = mejor)
    final stressFactor = _normalizeScale5Inverse(w.stressLevel);

    // Fatiga general percibida (1-5, 1 = sin fatiga = mejor)
    final fatigueFactor = _normalizeScale5Inverse(w.fatigueLevel);

    // Promedio ponderado de factores contextuales (resultado: 0.0 → 1.0)
    final contextScore =
        (sleepHoursFactor  * 0.35) +
        (sleepQualityFactor * 0.25) +
        (stressFactor       * 0.20) +
        (fatigueFactor      * 0.20);

    // Convertir a modificador multiplicativo: rango 0.80 → 1.08
    // contextScore 0.0 → factor 0.80 (penalización -20%)
    // contextScore 1.0 → factor 1.08 (bonus +8%)
    return 0.80 + (contextScore * 0.28);
  }

  /// Normaliza horas de sueño a factor entre 0.0 y 1.0.
  /// Óptimo 8h = 1.0, mínimo 5h = 0.0, penalización severa < 5h.
  static double _normalizeSleepHours(double hours) {
    if (hours >= 8.0) return 1.0;
    if (hours >= 5.0) return (hours - 5.0) / (8.0 - 5.0);
    // Menos de 5h: degradación acelerada
    return max(0.0, hours / 5.0 * 0.5);
  }

  /// Normaliza escala 1-5 donde 5 = óptimo → 1.0
  static double _normalizeScale5(int value) {
    return ((value.clamp(1, 5) - 1) / 4).toDouble();
  }

  /// Normaliza escala 1-5 inversa donde 1 = óptimo → 1.0 (estrés, fatiga, DOMS)
  static double _normalizeScale5Inverse(int value) {
    return ((5 - value.clamp(1, 5)) / 4).toDouble();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // SEMÁFORO Y NARRATIVAS DE RENDIMIENTO
  // ───────────────────────────────────────────────────────────────────────────

  /// Retorna el estado del semáforo de disponibilidad deportiva (v4.11).
  static String getStatus(int iri) {
    if (iri >= 85) return 'VERDE';    // ÓPTIMO: Disponible para alta carga
    if (iri >= 70) return 'AMARILLO'; // PRECAUCIÓN: Carga moderada
    if (iri >= 50) return 'NARANJA';  // FATIGA: Reducir carga
    return 'ROJO';                    // CRÍTICO: Priorizar recuperación
  }

  /// Genera feedback narrativo deportivo (frase motivadora) según el IRI final.
  static String getNarrativeFeedback(int iri) {
    if (iri >= 85) {
      return 'Tu sistema nervioso está en estado óptimo. ¡Hoy es un buen día para dar el máximo!';
    } else if (iri >= 70) {
      return 'Tu sistema nervioso está en equilibrio, pero requiere una carga controlada hoy.';
    } else if (iri >= 50) {
      return 'Fatiga central detectada. Prioriza el descanso y la recuperación activa.';
    } else {
      return 'Estado crítico de agotamiento. Se recomienda cese de actividad de alta demanda.';
    }
  }

  /// Genera un "Insight Cualitativo" conectando los hábitos (Wellness) con el 
  /// rendimiento (PVT), usando lenguaje amigable para el deportista.
  static String getContextualNarrative(int iriBase, int iriFinal, WellnessSurvey wellness) {
    List<String> insights = [];

    // Análisis de Sueño (Factor más crítico)
    if (wellness.sleepHours < 6) {
      insights.add("La restricción de sueño (${wellness.sleepHours}h) está penalizando tu capacidad de recuperación neural.");
    } else if (wellness.sleepHours >= 8 && wellness.sleepQuality >= 4) {
      insights.add("Excelente descanso. Tus hábitos de sueño están potenciando tu estado cognitivo hoy.");
    }

    // Análisis de Estrés
    if (wellness.stressLevel >= 4) {
      insights.add("El alto nivel de estrés reportado está consumiendo energía vital de tu sistema nervioso.");
    }

    // Análisis de Fatiga (Periférico vs Central)
    if (wellness.fatigueLevel >= 4) {
      if (iriBase >= 80) {
        insights.add("Sientes fatiga física, pero tus reflejos (SNC) siguen intactos. Buen momento para trabajo técnico.");
      } else {
        insights.add("La carga periférica (fatiga) ya está afectando tu tiempo de reacción central.");
      }
    }

    if (insights.isEmpty) {
      if (iriFinal >= 85) {
        return "Tus métricas de bienestar están en perfecta sintonía con tu tiempo de reacción.";
      } else {
        return "Tus hábitos reportados son normales. Presta atención a la calidad de tu descanso para mejorar este score.";
      }
    }

    return insights.join(" ");
  }
}
