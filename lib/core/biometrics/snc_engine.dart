import 'dart:math';
import '../../features/biometrics/domain/biometric_models.dart';

/// Motor local de Inteligencia de Rendimiento para el Sistema Nervioso Central.
///
/// FÓRMULA COMPLETA (v2.2):
///   IRIFinal = (PVTScore + WellnessScore) / 2   — Algoritmo Fiel 50/50
///
/// IRIBase (señales objetivas):
///   100% PVT  — Velocidad de reacción neural (latencia cognitiva)
///
/// WellnessScore (señales subjetivas — 4 factores con pesos evidence-based):
///   sleepHours   30 pts — mayor predictor cognitivo (Watson et al., 2015)
///   sleepQuality 25 pts — calidad del sueño (Lastella et al., 2020)
///   stressLevel  25 pts — predictor primario de bienestar (Hooper & Mackinnon, 1995)
///   fatigueLevel 20 pts — marcador complementario (Saw et al., 2016)
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
  // ───────────────────────────────────────────────────────────────────────────
  // CÁLCULO COMPLETO CON WELLNESS (ALGORITMO FIEL 50/50)
  // ───────────────────────────────────────────────────────────────────────────

  /// Calcula el IRI incorporando el cuestionario de bienestar diario.
  /// Se ha unificado con la plataforma Web (Algoritmo Fiel), dando 50% de peso
  /// al rendimiento cognitivo (PVT) y 50% al estado subjetivo (Wellness).
  static int calculateIRIWithContext(double _, List<int> pvtLatencies, WellnessSurvey wellness) {
    final pvtScore = _computeBase(pvtLatencies);
    final wellnessScore = _computeWellnessScore(wellness);
    
    // Algoritmo Fiel: Promedio exacto entre PVT y Wellness (50/50)
    final iriFinal = (pvtScore + wellnessScore) / 2.0;
    return iriFinal.clamp(0.0, 100.0).round();
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

  /// Calcula el puntaje de Wellness (0-100) compatible con la Plataforma Web.
  /// Pesos basados en literatura de ciencias del deporte:
  ///   sleepHours   30 pts — mayor predictor de consolidación cognitiva (Watson et al., 2015)
  ///   sleepQuality 25 pts — calidad del sueño (Lastella et al., 2020)
  ///   stressLevel  25 pts — predictor primario de bienestar (Hooper & Mackinnon, 1995)
  ///   fatigueLevel 20 pts — marcador complementario (Saw et al., 2016)
  /// DEBE SER IDÉNTICA a pvt_exgauss_worker.py y app_v411_final.js
  static double _computeWellnessScore(WellnessSurvey w) {
    final hScore = (min(8.0, w.sleepHours) / 8.0) * 30.0;  // 30 pts
    final qScore = (w.sleepQuality / 5.0) * 25.0;           // 25 pts
    final sScore = ((6.0 - w.stressLevel) / 5.0) * 25.0;   // 25 pts (inv.)
    final fScore = ((6.0 - w.fatigueLevel) / 5.0) * 20.0;  // 20 pts (inv.)

    return hScore + qScore + sScore + fScore;
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
  /// Integra la "Hard-Rule de Lapses" para consistencia clínica con el backend web:
  /// - 1 lapse: Sobrescribe GREEN a AMARILLO (Fatiga Incipiente)
  /// - >= 2 lapses: Sobrescribe a NARANJA (Fatiga en Proceso)
  static String getStatus(int iri, {int lapses = 0}) {
    // ── HARD-RULE DE LAPSES (Consistencia con Ex-Gaussian Worker) ───────────
    if (lapses >= 2) {
      return 'NARANJA'; // Fatiga en proceso por múltiples bloqueos
    } else if (lapses == 1) {
      if (iri >= 85) {
        return 'AMARILLO'; // Fatiga incipiente por lapso atencional
      }
    }

    if (iri >= 85) return 'VERDE';    // ÓPTIMO: Disponible para alta carga
    if (iri >= 70) return 'AMARILLO'; // PRECAUCIÓN: Carga moderada
    if (iri >= 50) return 'NARANJA';  // FATIGA: Reducir carga
    return 'ROJO';                    // CRÍTICO: Priorizar recuperación
  }

  /// Retorna la etiqueta amigable del estado clínico según semáforo y lapsos.
  static String getStatusLabel(String status, {int lapses = 0}) {
    if (status == 'VERDE') return 'ESTADO PRIME';
    if (status == 'AMARILLO') {
      return lapses > 0 ? 'FATIGA INCIPIENTE' : 'MANTENIMIENTO';
    }
    if (status == 'NARANJA') {
      return lapses >= 2 ? 'FATIGA EN PROCESO' : 'CARGA REDUCIDA';
    }
    if (status == 'ROJO') return 'RECUPERACIÓN';
    return status;
  }

  /// Genera feedback narrativo deportivo según el IRI final y lapsos de atención.
  static String getNarrativeFeedback(int iri, {int lapses = 0, int? slowestMs}) {
    if (lapses >= 2) {
      return 'Fatiga central detectada: Se registraron $lapses lapsos de atención (>500ms). Tu sistema nervioso requiere descanso y recuperación activa antes de cargas intensas.';
    } else if (lapses == 1) {
      final msText = slowestMs != null && slowestMs > 0 ? ' ($slowestMs ms)' : '';
      if (iri >= 85) {
        return 'Fatiga incipiente detectada: Se registró 1 lapso de atención$msText. Aunque tu resiliencia global es alta ($iri pts), modera la exigencia táctica y monitorea tu concentración.';
      } else {
        return 'Precaución atencional: Se detectó 1 lapso de atención$msText con resiliencia moderada ($iri pts). Prioriza la recuperación hoy.';
      }
    }

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
  /// rendimiento (PVT), incorporando advertencias atencionales.
  static String getContextualNarrative(
    int iriBase, 
    int iriFinal, 
    WellnessSurvey wellness, 
    {int lapses = 0, int? slowestMs}
  ) {
    List<String> insights = [];

    // Análisis de Lapsos Atencionales (Prioridad Neuro-funcional)
    if (lapses > 0) {
      final msText = slowestMs != null && slowestMs > 0 ? ' con latencia máxima de ${slowestMs}ms' : '';
      insights.add("Se registró $lapses lapso${lapses > 1 ? 's' : ''} de atención (>500ms)$msText, indicando micro-desconexión cortical transitoria.");
    }

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
