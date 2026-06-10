import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class WellnessScreen extends StatefulWidget {
  final Function(double hours, int quality, int stress, int fatigue) onComplete;

  const WellnessScreen({super.key, required this.onComplete});

  @override
  State<WellnessScreen> createState() => _WellnessScreenState();
}

class _WellnessScreenState extends State<WellnessScreen> {
  double _sleepHours = 7.0;
  int _sleepQuality = 3;
  int _stressLevel = 2;
  int _fatigueLevel = 2;

  void _provideHapticFeedback() {
    HapticFeedback.mediumImpact();
  }

  @override
  Widget build(BuildContext context) {
    const Color accent = Color(0xFF00E5FF);
    const Color surface = Color(0xFF131313);

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 48),
              const Text(
                'TELEMETRÍA DE ESTADO (WELLNESS)',
                style: TextStyle(
                  color: accent,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'CONTEXTO DIARIO',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.w900,
                  fontFamily: 'SpaceGrotesk',
                ),
              ),
              const SizedBox(height: 8),
              Container(height: 2, width: 40, color: accent),
              const SizedBox(height: 40),
              Expanded(
                child: ListView(
                  physics: const BouncingScrollPhysics(),
                  children: [
                    _buildSliderBlock(
                      'HORAS DE SUEÑO',
                      _sleepHours,
                      '${_sleepHours.toStringAsFixed(1)} H',
                      (val) => setState(() => _sleepHours = val),
                    ),
                    const SizedBox(height: 32),
                    _buildLikertBlock(
                      'CALIDAD DEL SUEÑO',
                      _sleepQuality,
                      (val) => setState(() => _sleepQuality = val),
                    ),
                    const SizedBox(height: 32),
                    _buildLikertBlock(
                      'CARGA DE ESTRÉS',
                      _stressLevel,
                      (val) => setState(() => _stressLevel = val),
                    ),
                    const SizedBox(height: 32),
                    _buildLikertBlock(
                      'FATIGA PERCIBIDA',
                      _fatigueLevel,
                      (val) => setState(() => _fatigueLevel = val),
                    ),
                    const SizedBox(height: 40),
                  ],
                ),
              ),
              _buildHUDButton(accent),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHUDButton(Color accent) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24.0, top: 12),
      child: GestureDetector(
        onTap: () {
          _provideHapticFeedback();
          widget.onComplete(_sleepHours, _sleepQuality, _stressLevel, _fatigueLevel);
        },
        child: Container(
          width: double.infinity,
          height: 64,
          decoration: BoxDecoration(
            color: accent,
            // Brutalist precision: 0px radius
            boxShadow: [
              BoxShadow(color: accent.withOpacity(0.3), blurRadius: 15, spreadRadius: -5),
            ],
          ),
          child: const Center(
            child: Text(
              'CONTINUAR AL SENSOR PVT',
              style: TextStyle(color: Colors.black, fontWeight: FontWeight.w900, letterSpacing: 1.5, fontSize: 13),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSliderBlock(String title, double value, String label, Function(double) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1, fontWeight: FontWeight.bold)),
            Text(label, style: const TextStyle(color: Color(0xFF00E5FF), fontWeight: FontWeight.w900, fontFamily: 'SpaceGrotesk')),
          ],
        ),
        const SizedBox(height: 8),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            activeTrackColor: const Color(0xFF00E5FF),
            inactiveTrackColor: Colors.white10,
            thumbColor: Colors.white,
            trackHeight: 2,
            overlayColor: const Color(0xFF00E5FF).withOpacity(0.1),
            thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
          ),
          child: Slider(
            value: value,
            min: 0,
            max: 12,
            divisions: 24,
            onChanged: (val) {
              _provideHapticFeedback();
              onChanged(val);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildLikertBlock(String title, int currentValue, Function(int) onSelected) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(5, (index) {
            final level = index + 1;
            final isSelected = level == currentValue;
            return GestureDetector(
              onTap: () {
                _provideHapticFeedback();
                onSelected(level);
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 58,
                height: 52,
                decoration: BoxDecoration(
                  color: isSelected ? const Color(0xFF00E5FF) : const Color(0xFF131313),
                  // Zero radius for Premium HUD Brutalism
                  border: isSelected ? null : Border.all(color: Colors.white.withOpacity(0.05)),
                ),
                child: Center(
                  child: Text(
                    '$level',
                    style: TextStyle(
                      color: isSelected ? Colors.black : Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                      fontFamily: 'SpaceGrotesk',
                    ),
                  ),
                ),
              ),
            );
          }),
        ),
      ],
    );
  }
}
