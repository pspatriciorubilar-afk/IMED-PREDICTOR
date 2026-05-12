import os

file_path = r'c:\Users\Pato\Desktop\proyectos\Cognitive Load Tracker (PVT)\lib\core\network\sync_service.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''      // 2. Guardar la medición detallada
      await firestore.collection('athletes').doc(athleteId).collection('measurements').add({
        "timestamp": timestamp.toIso8601String(),
        "iri": iriScore,
        "status": statusSNC,
        "wellness": {
          "sleepHours": wellnessData['sleep_hours'],
          "sleepQuality": wellnessData['sleep_quality'],
          "stressLevel": wellnessData['stress_level'],
          "fatigueLevel": wellnessData['fatigue_level'],
        },
        "pvt": {
          "logs": pvtLog,
          "metrics": {
            "meanLatency": mean.round(),
            "lapses": lapses,
            "fastest": fastest,
            "slowest": slowest,
            "totalTrials": pvtLog.length,
          }
        },
        "deviceInfo": {
          "platform": Platform.isAndroid ? "Android" : "iOS",
          "version": "v3.0-Production"
        },
        "syncedAt": FieldValue.serverTimestamp(),
      });
      print("🔥 [FIREBASE] Datos guardados con éxito para $athleteId.");'''

replacement = '''      // 2. Guardar la medición detallada
      final String dateStr = "${timestamp.year}-${timestamp.month.toString().padLeft(2, '0')}-${timestamp.day.toString().padLeft(2, '0')}";
      
      await firestore.collection('athletes').doc(athleteId).collection('measurements').add({
        "timestamp": timestamp.toIso8601String(),
        "date": dateStr,
        "iri": iriScore,
        "status": statusSNC,
        "wellness": {
          "sleepHours": wellnessData['sleep_hours'],
          "sleepQuality": wellnessData['sleep_quality'],
          "stressLevel": wellnessData['stress_level'],
          "fatigueLevel": wellnessData['fatigue_level'],
        },
        "pvt": {
          "logs": pvtLog,
          "metrics": {
            "meanLatency": mean.round(),
            "lapses": lapses,
            "fastest": fastest,
            "slowest": slowest,
            "totalTrials": pvtLog.length,
          }
        },
        "deviceInfo": {
          "platform": Platform.isAndroid ? "Android" : "iOS",
          "version": "v3.0-Production"
        },
        "syncedAt": FieldValue.serverTimestamp(),
      });

      // 3. ACTUALIZAR DASHBOARD DE MANERA DIRECTA
      // Como el IMED Predictor Dashboard lee de Daily_Performance, debemos inyectar
      // el IRI y los Lapses aquí para que el frontend del coach se entere al instante,
      // incluso antes de que se suban los datos del GPS.
      await firestore.collection('Daily_Performance').doc('${athleteId}_$dateStr').set({
        "athleteId": athleteId,
        "date": dateStr,
        "iri": iriScore,
        "lapses": lapses,
        "timestamp": FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));

      print("🔥 [FIREBASE] Datos guardados con éxito para $athleteId.");'''

if target in content:
    content = content.replace(target, replacement)
    print("Replaced!")
else:
    print("Not replaced. Check the string.")
    
    # Let's try finding a smaller target string to be more flexible
    if "await firestore.collection('athletes').doc(athleteId).collection('measurements').add({" in content:
        print("Fallback replacement running...")
        
        fallback_target = '''      // 2. Guardar la medición detallada
      await firestore.collection('athletes').doc(athleteId).collection('measurements').add({
        "timestamp": timestamp.toIso8601String(),'''
        
        fallback_replace = '''      // 2. Guardar la medición detallada
      final String dateStr = "${timestamp.year}-${timestamp.month.toString().padLeft(2, '0')}-${timestamp.day.toString().padLeft(2, '0')}";
      
      await firestore.collection('athletes').doc(athleteId).collection('measurements').add({
        "timestamp": timestamp.toIso8601String(),
        "date": dateStr,'''
        
        content = content.replace(fallback_target, fallback_replace)
        
        fallback_target_2 = '''      print("🔥 [FIREBASE] Datos guardados con éxito para $athleteId.");'''
        
        fallback_replace_2 = '''      // 3. ACTUALIZAR DASHBOARD DIRECTAMENTE
      await firestore.collection('Daily_Performance').doc('${athleteId}_$dateStr').set({
        "athleteId": athleteId,
        "date": dateStr,
        "iri": iriScore,
        "lapses": lapses,
        "timestamp": FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));

      print("🔥 [FIREBASE] Datos guardados con éxito para $athleteId.");'''
        
        content = content.replace(fallback_target_2, fallback_replace_2)
        print("Fallback Replaced!")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
