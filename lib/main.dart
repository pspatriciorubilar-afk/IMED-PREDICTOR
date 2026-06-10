import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:isar/isar.dart';
import 'package:path_provider/path_provider.dart';

import 'features/cognitive_load/domain/pvt_session.dart';
import 'features/auth/domain/user_profile.dart'; // Nuevo
import 'features/auth/presentation/onboarding_screen.dart'; // Nuevo
import 'features/cognitive_load/application/pvt_notifier.dart';
import 'features/cognitive_load/presentation/widgets/pvt_test_widget.dart';
import 'features/cognitive_load/presentation/trends_screen.dart';
import 'features/cognitive_load/presentation/daily_readiness_screen.dart';
import 'features/biometrics/presentation/biometric_flow_coordinator.dart';
import 'features/education/presentation/education_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  // Inicializar Hive ANTES que cualquier otra operación
  await Hive.initFlutter();
  if (!Hive.isBoxOpen('sync_queue'))      await Hive.openBox('sync_queue');
  if (!Hive.isBoxOpen('daily_readiness')) await Hive.openBox('daily_readiness');

  final dir = await getApplicationDocumentsDirectory();
  final isar = await Isar.open(
    [PvtSessionSchema, UserProfileSchema], // Agregado esquema de Usuario
    directory: dir.path,
  );

  final userProfile = await isar.collection<UserProfile>().where().findFirst();

  runApp(
    ProviderScope(
      overrides: [
        pvtProvider.overrideWith((ref) => PvtNotifier(isar)),
      ],
      child: ImedSportApp(isar: isar, hasUser: userProfile != null),
    ),
  );
}

class ImedSportApp extends StatefulWidget {
  final Isar isar;
  final bool hasUser;
  const ImedSportApp({super.key, required this.isar, required this.hasUser});

  @override
  State<ImedSportApp> createState() => _ImedSportAppState();
}

class _ImedSportAppState extends State<ImedSportApp> {
  late bool _showOnboarding;

  @override
  void initState() {
    super.initState();
    _showOnboarding = !widget.hasUser;
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'IMED PREDICTOR',
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.black,
        useMaterial3: true,
      ),
      home: _showOnboarding 
        ? OnboardingScreen(
            isar: widget.isar, 
            onComplete: () => setState(() => _showOnboarding = false)
          )
        : MainModuleSelector(isar: widget.isar),
    );
  }
}

class MainModuleSelector extends StatefulWidget {
  final Isar isar;
  const MainModuleSelector({super.key, required this.isar});

  @override
  State<MainModuleSelector> createState() => _MainModuleSelectorState();
}

class _MainModuleSelectorState extends State<MainModuleSelector> {
  int _currentIndex = 0;
  
  late final List<Widget> _workBlocks = [
    // Orden: Prueba PVT → Registro Diario → Historial → Educación
    BiometricFlowCoordinator(isar: widget.isar),

    const DailyReadinessScreen(),
    TrendsScreen(isar: widget.isar),
    const EducationScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        transitionBuilder: (child, animation) => FadeTransition(
          opacity: animation,
          child: child,
        ),
        child: KeyedSubtree(
          key: ValueKey(_currentIndex),
          child: _workBlocks[_currentIndex],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: const Color(0xFF0F0F0F),
        currentIndex: _currentIndex,
        selectedItemColor: Colors.cyanAccent,
        unselectedItemColor: Colors.white38,
        type: BottomNavigationBarType.fixed,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.psychology_rounded),
            label: 'Prueba PVT',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.monitor_heart_outlined),
            label: 'Registro Diario',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics_rounded),
            label: 'Historial',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.school_rounded),
            label: 'Educación',
          ),
        ],
      ),
    );
  }
}
