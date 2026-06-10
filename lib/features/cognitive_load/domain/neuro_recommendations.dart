import 'package:flutter/material.dart';

class NeuroRecommendation {
  final String title;
  final String body;
  final IconData icon;
  final Color color;

  NeuroRecommendation({
    required this.title, 
    required this.body, 
    required this.icon, 
    required this.color
  });

  static NeuroRecommendation getByStatus(String status) {
    status = status.toLowerCase();
    if (status == 'red') {
      return NeuroRecommendation(
        title: "SATURACIÓN NEURO-COGNITIVA CRÍTICA",
        body: "Déficit severo en velocidad de procesamiento. Se recomienda desactivación sensorial y descanso profundo. Riesgo de sobre-esfuerzo neural moderado.",
        icon: Icons.error_outline_rounded,
        color: Colors.redAccent,
      );
    } else if (status == 'yellow') {
      return NeuroRecommendation(
        title: "FATIGA NEURAL MODERADA",
        body: "Velocidad de procesamiento bajo el promedio esperado. Se recomienda visualización guiada y tareas tácticas de baja complejidad ejecutiva.",
        icon: Icons.hourglass_empty_rounded,
        color: Colors.orangeAccent,
      );
    } else {
      return NeuroRecommendation(
        title: "PICO DE RENDIMIENTO NEURO-COGNITIVO",
        body: "Capacidad de respuesta óptima. Estado de 'Flow' accesible. Momento ideal para entrenamiento táctico de alta complejidad y competencia.",
        icon: Icons.bolt_rounded,
        color: Colors.greenAccent,
      );
    }
  }
}
