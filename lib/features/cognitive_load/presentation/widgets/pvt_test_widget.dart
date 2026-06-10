import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../application/pvt_notifier.dart';
import '../../domain/neuro_recommendations.dart'; // Nuevo

class PvtTestWidget extends ConsumerStatefulWidget {
  final Function(List<int>)? onComplete;
  const PvtTestWidget({super.key, this.onComplete});

  @override
  ConsumerState<PvtTestWidget> createState() => _PvtTestWidgetState();
}

class _PvtTestWidgetState extends ConsumerState<PvtTestWidget> {
  bool _showBriefing = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(pvtProvider.notifier).resetTest();
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_showBriefing) return _buildBriefing();

    final pvtState = ref.watch(pvtProvider);
    final pvtNotifier = ref.read(pvtProvider.notifier);

    final backgroundColor = pvtState.status == PvtTestStatus.stimulus 
        ? Colors.redAccent 
        : Colors.black;

    return Listener(
      onPointerDown: (event) => pvtNotifier.handleTap(),
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: double.infinity,
        height: double.infinity,
        color: backgroundColor,
        child: SafeArea(
          child: Stack(
            children: [
              // Barra de progreso interactiva (framing anti-aburrimiento)
              if (pvtState.status != PvtTestStatus.idle && pvtState.status != PvtTestStatus.completed)
                Positioned(
                  top: 20,
                  left: 20,
                  right: 20,
                  child: _buildProgressBar(pvtState.currentReactionTimes.length),
                ),
              Center(
                child: _buildUiLayer(pvtState, pvtNotifier),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressBar(int currentStep) {
    const int totalSteps = 30; // 30 estímulos del nuevo protocolo clínico
    final double progress = (currentStep / totalSteps).clamp(0.0, 1.0);
    
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text("PROGRESO PVT-B", style: TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
            Text("$currentStep / $totalSteps", style: const TextStyle(color: Colors.cyanAccent, fontSize: 14, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 8,
            backgroundColor: Colors.white10,
            valueColor: AlwaysStoppedAnimation<Color>(
              progress > 0.8 ? Colors.greenAccent : Colors.cyanAccent
            ),
          ),
        ),
        const SizedBox(height: 6),
        if (currentStep > 20)
          const Text("¡ÚLTIMO ESFUERZO! MANTÉN EL FOCO", style: TextStyle(color: Colors.greenAccent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
      ],
    );
  }

  Widget _buildBriefing() {
    return Container(
      color: Colors.black,
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.psychology_rounded, color: Colors.cyanAccent, size: 60),
          const SizedBox(height: 20),
          const Text("Prueba PVT", 
            style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          const Text(
            "Mide tu tiempo de reacción y fatiga neuro-cognitiva. Para mejores resultados, realiza la prueba al menos 30 minutos después de despertar.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white60, fontSize: 16, height: 1.5)),
          const SizedBox(height: 40),
          ElevatedButton(
            onPressed: () => setState(() => _showBriefing = false),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white10,
              padding: const EdgeInsets.symmetric(horizontal: 50, vertical: 20),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))
            ),
            child: const Text("ENTENDIDO", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildUiLayer(PvtTestState state, PvtNotifier notifier) {
    if (state.status == PvtTestStatus.completed) {
      // Navegación automática inmediata sin intervención del usuario
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (widget.onComplete != null) {
          widget.onComplete!(state.currentReactionTimes);
        }
      });
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.cyanAccent),
            SizedBox(height: 20),
            Text("PROCESANDO TEST...", style: TextStyle(color: Colors.cyanAccent, letterSpacing: 2)),
          ],
        ),
      );
    }

    switch (state.status) {
      case PvtTestStatus.idle:
        return _buildStartView(state, notifier);
      case PvtTestStatus.ready:
        return const Icon(Icons.add, color: Colors.white10, size: 40);
      case PvtTestStatus.stimulus:
        return const _PvtStimulusTimer();
      case PvtTestStatus.falseStart:
        return const Text("¡FALSO ARRANQUE!", style: TextStyle(color: Colors.yellow, fontSize: 24, fontWeight: FontWeight.bold));
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildStartView(PvtTestState state, PvtNotifier notifier) {
    if (state.blockReason != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.block_rounded, color: Colors.redAccent, size: 60),
            const SizedBox(height: 20),
            Text(state.blockReason!,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70, fontSize: 16, height: 1.5)),
          ],
        ),
      );
    }

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text("Presiona la pantalla en cuanto aparezca el color ROJO", 
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white70, fontSize: 16)),
        const SizedBox(height: 40),
        ElevatedButton(
          onPressed: () => notifier.startTest(),
          child: const Text("INICIAR"),
        )
      ],
    );
  }

  Widget _buildResultsView(PvtTestState state, PvtNotifier notifier) {
    final mean = state.currentReactionTimes.isEmpty 
        ? 0.0 
        : (state.currentReactionTimes.reduce((a, b) => a + b) / state.currentReactionTimes.length).toDouble();
    
    // Lógica local para recomendación inmediata como fallback
    const double baseline = 240.0; // Valor de referencia estandarizado
    String clinicalStatus = 'green';
    if (mean > (baseline * 1.15)) {
      clinicalStatus = 'red';
    } else if (mean > (baseline * 1.10)) {
      clinicalStatus = 'yellow';
    }
    
    // Priorizamos el status calculado por el servidor (baseline personal real)
    final finalStatus = state.serverStatus ?? clinicalStatus;
    final recommendation = NeuroRecommendation.getByStatus(finalStatus);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text("RENDIMIENTO NEURO-COGNITIVO", 
            style: TextStyle(color: Colors.white38, fontSize: 12, letterSpacing: 1.2)),
          const SizedBox(height: 10),
          Text("${mean.toStringAsFixed(1)} ms", 
            style: const TextStyle(color: Colors.white, fontSize: 56, fontWeight: FontWeight.w900)),
          const SizedBox(height: 10),
          if (state.isFetchingServerStatus)
             const Row(
               mainAxisAlignment: MainAxisAlignment.center,
               children: [
                 SizedBox(width: 12, height: 12, child: CircularProgressIndicator(color: Colors.cyanAccent, strokeWidth: 2)),
                 SizedBox(width: 8),
                 Text("Calculando baseline personal...", style: TextStyle(color: Colors.cyanAccent, fontSize: 12)),
               ],
             )
          else if (state.serverStatus != null)
             Container(
               padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
               decoration: BoxDecoration(color: Colors.cyanAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
               child: const Text("BASELINE PERSONAL APLICADO", style: TextStyle(color: Colors.cyanAccent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
             ),

          const SizedBox(height: 30),
          
          // TARJETA DE DIAGNÓSTICO NEURO-PSICOLÓGICO DE ALTO RENDIMIENTO
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: recommendation.color.withOpacity(0.05),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: recommendation.color.withOpacity(0.2)),
            ),
            child: Column(
              children: [
                Icon(recommendation.icon, color: recommendation.color, size: 32),
                const SizedBox(height: 15),
                Text(recommendation.title, 
                  textAlign: TextAlign.center,
                  style: TextStyle(color: recommendation.color, fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 10),
                Text(recommendation.body, 
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.5)),
              ],
            ),
          ),
          
          const SizedBox(height: 50),
          SizedBox(
            width: double.infinity,
            height: 60,
            child: ElevatedButton(
              onPressed: () {
                if (widget.onComplete != null) {
                  widget.onComplete!(state.currentReactionTimes);
                } else {
                  setState(() => _showBriefing = true);
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white.withOpacity(0.05),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))
              ), 
              child: const Text("LISTO PARA ENTRENAR", 
                style: TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold))),
          ),
        ],
      ),
    );
  }
}

class _PvtStimulusTimer extends StatefulWidget {
  const _PvtStimulusTimer();

  @override
  State<_PvtStimulusTimer> createState() => _PvtStimulusTimerState();
}

class _PvtStimulusTimerState extends State<_PvtStimulusTimer> {
  final Stopwatch _sw = Stopwatch()..start();
  late Timer _t;

  @override
  void initState() {
    super.initState();
    _t = Timer.periodic(const Duration(milliseconds: 1), (timer) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _t.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Text(
      '${_sw.elapsedMilliseconds}',
      style: const TextStyle(
        color: Colors.white,
        fontSize: 80,
        fontWeight: FontWeight.w900,
        fontFamily: 'Courier', // Estilo cronómetro clásico
      ),
    );
  }
}
