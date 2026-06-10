// lib/core/services/notification_service.dart
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz;
import 'package:flutter_timezone/flutter_timezone.dart';
import '../../features/circadian_optimizer/domain/circadian_models.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    // 1. Inicializar bases de datos de Timezones (Esencial para atletas que viajan)
    tz.initializeTimeZones();
    final String currentTimeZone = await FlutterTimezone.getLocalTimezone();
    tz.setLocalLocation(tz.getLocation(currentTimeZone));

    // 2. Configuración para Android
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    // 3. Configuración para iOS
    const DarwinInitializationSettings initializationSettingsDarwin =
        DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsDarwin,
    );

    await _notificationsPlugin.initialize(initializationSettings);
  }

  /// Programa las 6 alarmas biológicas del día basadas en el Despertar
  Future<void> scheduleCircadianNotifications(List<CircadianEvent> agenda) async {
    // Cancelamos alarmas previas para reprogramar el nuevo ciclo del día
    await _notificationsPlugin.cancelAll();

    for (int i = 0; i < agenda.length; i++) {
      final event = agenda[i];
      
      // Solo programar si la hora del evento es futura
      if (event.plannedTime.isAfter(DateTime.now())) {
        await _notificationsPlugin.zonedSchedule(
          i,
          "IMED PREDICTOR: ${event.title}",
          event.scientificDescription,
          tz.TZDateTime.from(event.plannedTime, tz.local),
          _getNotificationDetails(event.phaseColor),
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        );
      }
    }
  }

  NotificationDetails _getNotificationDetails(dynamic color) {
    return const NotificationDetails(
      android: AndroidNotificationDetails(
        'circadian_channel',
        'Ritmos Circadianos',
        channelDescription: 'Alertas para optimización biológica y hormonal',
        importance: Importance.max,
        priority: Priority.high,
        ticker: 'ticker',
        colorized: true,
      ),
      iOS: DarwinNotificationDetails(),
    );
  }
}
