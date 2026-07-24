import 'package:flutter/material.dart';
import 'package:isar/isar.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../domain/user_profile.dart';

class OnboardingScreen extends StatefulWidget {
  final Isar isar;
  final VoidCallback onComplete;

  const OnboardingScreen({super.key, required this.isar, required this.onComplete});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _ageController = TextEditingController();
  final _associationCodeController = TextEditingController();

  bool _isLoading = false;

  String _buildAthleteId(String first, String last, String age) {
    final f = first.trim().toLowerCase().replaceAll(' ', '_');
    final l = last.trim().toLowerCase().replaceAll(' ', '_');
    return '${f}_${l}_${age.trim()}';
  }

  Future<void> _finishOnboardingFast() async {
    final first = _firstNameController.text.trim();
    final last = _lastNameController.text.trim();
    final ageStr = _ageController.text.trim();
    final code = _associationCodeController.text.trim().toUpperCase();

    if (first.isEmpty || last.isEmpty || ageStr.isEmpty || code.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Completa todos los campos, incluyendo el código maestro.")),
      );
      return;
    }

    setState(() => _isLoading = true);

    String? tenantId;

    try {
      // Intentar validar en Firestore si está conectado
      final querySnap = await FirebaseFirestore.instance
          .collection('tenants')
          .where('associationCode', isEqualTo: code)
          .limit(1)
          .get()
          .timeout(const Duration(seconds: 6));

      if (querySnap.docs.isEmpty) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Código maestro inválido o inexistente. Verifica con tu psicólogo o coach.")),
        );
        return;
      }

      tenantId = querySnap.docs[0].id;
    } catch (e) {
      // Si falla por red/tiempo (offline), permitimos el paso guardando solo el código
      // y resolveremos el tenantId después cuando recupere la conexión.
      print("📡 [ONBOARDING] Error al validar código maestro (offline): $e");
    }

    final athleteId = _buildAthleteId(first, last, ageStr);

    final user = UserProfile(
      athleteId: athleteId,
      firstName: first,
      lastName: last,
      age: int.tryParse(ageStr) ?? 25,
      chronotype: Chronotype.intermediate, // Default
      preferredTrainingHour: 7, // Default
      registeredAt: DateTime.now(),
      associationCode: code,
      tenantId: tenantId,
    );

    await widget.isar.writeTxn(() => widget.isar.collection<UserProfile>().put(user));
    
    if (mounted) {
      setState(() => _isLoading = false);
      widget.onComplete();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(40.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.badge_rounded, color: Colors.cyanAccent, size: 50),
              const SizedBox(height: 20),
              const Text("Identificación",
                style: TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
              const Text("Tu perfil de atleta profesional",
                style: TextStyle(color: Colors.white38)),
              const SizedBox(height: 40),
              _buildTextField("Nombre", _firstNameController, TextInputType.name),
              const SizedBox(height: 16),
              _buildTextField("Apellido", _lastNameController, TextInputType.name),
              const SizedBox(height: 16),
              _buildTextField("Edad", _ageController, TextInputType.number),
              const SizedBox(height: 16),
              _buildTextField("Código Maestro (Coach/Psicólogo)", _associationCodeController, TextInputType.text),
              const SizedBox(height: 40),
              _buildActionBtn("GUARDAR Y PASAR AL HUB", () {
                _finishOnboardingFast();
              }),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, TextInputType keyboardType) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.white30),
        enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white10)),
        focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.cyanAccent)),
      ),
    );
  }

  Widget _buildActionBtn(String label, VoidCallback? onAction) {
    return SizedBox(
      width: double.infinity,
      height: 60,
      child: ElevatedButton(
        onPressed: _isLoading ? null : onAction,
        style: ElevatedButton.styleFrom(
          backgroundColor: onAction == null ? Colors.white10 : Colors.cyanAccent.withOpacity(0.15),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: _isLoading
            ? const CircularProgressIndicator(color: Colors.cyanAccent)
            : Text(label,
                style: TextStyle(
                  color: onAction == null ? Colors.white24 : Colors.cyanAccent,
                  fontWeight: FontWeight.bold)),
      ),
    );
  }
}
