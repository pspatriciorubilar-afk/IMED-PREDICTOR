import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:isar/isar.dart';
import '../domain/pvt_session.dart';


enum PvtTestStatus { idle, ready, stimulus, falseStart, completed }

class PvtTestState {
  final PvtTestStatus status;
  final List<int> currentReactionTimes;
  final int falseStarts;
  final Duration? lastReaction;
  final String? serverStatus;
  final bool isFetchingServerStatus;
  final String? blockReason;

  PvtTestState({
    this.status = PvtTestStatus.idle,
    this.currentReactionTimes = const [],
    this.falseStarts = 0,
    this.lastReaction,
    this.serverStatus,
    this.isFetchingServerStatus = false,
    this.blockReason,
  });

  PvtTestState copyWith({
    PvtTestStatus? status,
    List<int>? currentReactionTimes,
    int? falseStarts,
    Duration? lastReaction,
    String? serverStatus,
    bool? isFetchingServerStatus,
    String? blockReason,
  }) {
    return PvtTestState(
      status: status ?? this.status,
      currentReactionTimes: currentReactionTimes ?? this.currentReactionTimes,
      falseStarts: falseStarts ?? this.falseStarts,
      lastReaction: lastReaction ?? this.lastReaction,
      serverStatus: serverStatus ?? this.serverStatus,
      isFetchingServerStatus: isFetchingServerStatus ?? this.isFetchingServerStatus,
      blockReason: blockReason != null ? (blockReason.isEmpty ? null : blockReason) : this.blockReason,
    );
  }
}

class PvtNotifier extends StateNotifier<PvtTestState> {
  final Isar isar;
  final Stopwatch _stopwatch = Stopwatch();
  Timer? _stimulusTimer;

  PvtNotifier(this.isar) : super(PvtTestState());

  void resetTest() {
    _stimulusTimer?.cancel();
    state = PvtTestState();
  }

  Future<void> startTest() async {
    final now = DateTime.now();

    // Sin restricciones: múltiples sesiones por día habilitadas para fase de prueba (7 días)
    state = state.copyWith(
      status: PvtTestStatus.ready,
      currentReactionTimes: [],
      falseStarts: 0,
      lastReaction: null,
      blockReason: "", // Resetea bloqueo
    );
    _scheduleNextStimulus();

  }

  void _scheduleNextStimulus() {
    _stimulusTimer?.cancel();
    // ISI Aleatorio Científico (1.5 a 4 segundos) para mantener alta carga cognitiva
    final delay = 1500 + (DateTime.now().microsecondsSinceEpoch % 2500);
    
    _stimulusTimer = Timer(Duration(milliseconds: delay), () {
      if (state.status == PvtTestStatus.ready) {
        state = state.copyWith(status: PvtTestStatus.stimulus);
        _stopwatch.reset();
        _stopwatch.start();
      }
    });
  }

  void handleTap() {
    if (state.status == PvtTestStatus.ready) {
      // Intento de trampa o anticipación (False Start preventivo)
      _stimulusTimer?.cancel();
      state = state.copyWith(
        status: PvtTestStatus.falseStart,
        falseStarts: state.falseStarts + 1,
      );
      Future.delayed(const Duration(seconds: 2), () {
        state = state.copyWith(status: PvtTestStatus.ready);
        _scheduleNextStimulus();
      });
    } else if (state.status == PvtTestStatus.stimulus) {
      _stopwatch.stop();
      final reaction = _stopwatch.elapsedMilliseconds;
      
      // Filtros de Ingeniería de Sensores (SNC v2.0)
      if (reaction < 120) {
        // Falso arranque por reflejo espinal no consciente
        _stimulusTimer?.cancel();
        state = state.copyWith(
          status: PvtTestStatus.falseStart,
          falseStarts: state.falseStarts + 1,
        );
        Future.delayed(const Duration(seconds: 2), () {
          state = state.copyWith(status: PvtTestStatus.ready);
          _scheduleNextStimulus();
        });
        return;
      }

      final updatedTimes = [...state.currentReactionTimes, reaction];
      
      state = state.copyWith(
        status: PvtTestStatus.ready,
        currentReactionTimes: updatedTimes,
        lastReaction: Duration(milliseconds: reaction),
      );
      
      // Protocolo de 30 intentos (PVT-B — Validación Ex-Gaussiana)
      // Basner & Dinges (2011): mínimo para ajuste MLE confiable de μ, σ, τ
      if (updatedTimes.length >= 30) {
        completeSession();
      } else {
        _scheduleNextStimulus();
      }
    }
  }

  Future<void> completeSession() async {
    _stimulusTimer?.cancel();
    final mean = state.currentReactionTimes.isEmpty 
        ? 0.0 
        : state.currentReactionTimes.reduce((a, b) => a + b) / state.currentReactionTimes.length;

    final session = PvtSession(
      timestamp: DateTime.now(),
      meanLatency: mean,
      lapsesCount: state.currentReactionTimes.where((t) => t > 500).length,
      falseStarts: state.falseStarts,
      rawReactionTimes: state.currentReactionTimes,
      isSynced: false, // Aseguramos que se marque para sincronizar
    );

    await isar.writeTxn(() => isar.collection<PvtSession>().put(session));
    state = state.copyWith(status: PvtTestStatus.completed);

    // al recopilar toda la biometría (Wellness + PVT). Aquí termina la sesión PVT instantáneamente.
    state = state.copyWith(isFetchingServerStatus: false);
  }

  @override
  void dispose() {
    _stimulusTimer?.cancel();
    super.dispose();
  }
}

final pvtProvider = StateNotifierProvider<PvtNotifier, PvtTestState>((ref) {
  // Se debe sobreescribir en el ProviderScope del main.dart
  throw UnimplementedError();
});
