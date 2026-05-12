import os

file_path = 'functions/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        # 5. Algoritmo IVN (Índice de Vulnerabilidad Neuro-Mecánica)
        iri_norm = max(imed_snc["iri"], 1.0)
        ivn_score = round((acwr * gps_data["decel_z5"]) / (iri_norm / 100), 2)

        # 6. Lógica de Riesgo y Prescripción Técnica
        risk_level = "GREEN"
        ivn_label = "ADAPTACIÓN ÓPTIMA"
        action = "mantener"
        
        if imed_snc["iri"] < 60 and gps_data["decel_z5"] > 15:
            risk_level, ivn_label, action = "RED", "RIESGO CRÍTICO", "optimizar"
        elif imed_snc["lapses"] > 2:
            risk_level, ivn_label, action = "YELLOW", "RIESGO COORDINACIÓN", "reprogramar"
        elif imed_snc["iri"] < 75 or acwr > 1.5:
            risk_level, ivn_label, action = "YELLOW", "RIESGO DE CARGA", "monitorear"

        # 7. Persistencia en Daily_Performance
        doc_id = f"{athlete_id}_{date_str}"
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        athlete_name = athlete_id
        if athlete_snap.exists:
            ad = athlete_snap.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip()

        payload = {
            "athleteId": athlete_id,
            "athleteName": athlete_name,
            "date": date_str,
            "gps": gps_data,
            "acwr": acwr,
            "iri": imed_snc["iri"],
            "lapses": imed_snc["lapses"],
            "ivn_score": ivn_score,
            "risk_level": risk_level,
            "ivn_label": ivn_label,
            "action": action,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "processed_at": firestore.SERVER_TIMESTAMP,
            "metadata": {
                "version": "2.0",
                "formula": "(ACWR * Z5) / (IRI/100)",
                "adapter": "semantic-v2"
            }
        }'''

replacement = '''        # 5. Algoritmo IVN Perfeccionado (Índice de Vulnerabilidad Neuro-Mecánica)
        iri_norm = max(imed_snc["iri"], 1.0)
        iri_factor = iri_norm / 100.0  # Disponibilidad biológica
        
        # Carga Mecánica (60/40)
        decel_raw = gps_data.get("decel_z5", 0.0)
        sprint_raw = gps_data.get("sprint_distance", 0.0)
        sprint_norm = sprint_raw / 10.0  # Normalización
        
        load_decel = 0.6 * decel_raw
        load_sprint = 0.4 * sprint_norm
        carga_mec = load_decel + load_sprint
        
        # IVN = Carga_Mec * (ACWR / IRI)
        ivn_score = round(carga_mec * (acwr / iri_factor), 2)

        # 6. Lógica de Riesgo, Safety Override y Prescripción Táctica
        risk_level = "GREEN"
        ivn_label = "ADAPTACIÓN ÓPTIMA"
        action = "Mantener planificación actual."
        
        # Determinar el driver principal de la carga
        risk_driver = "SPRINT" if load_sprint > load_decel else "DECEL"
        
        # Safety Override (Control Motor)
        if imed_snc["lapses"] > 2:
            risk_level = "RED"
            ivn_label = "CRÍTICO (FALLA SNC)"
            action = "Alerta: Falla de control motor detectada. Riesgo de lesión no traumática (ligamentos). Cese inmediato de carga de alta precisión."
        else:
            # Lógica IVN Normal
            if ivn_score > 30.0 or (iri_norm < 60 and carga_mec > 15):
                risk_level = "RED"
                ivn_label = "RIESGO CRÍTICO"
                if risk_driver == "SPRINT":
                    action = "Alerta: Riesgo de lesión por estiramiento. Limitar esfuerzos lineales de alta velocidad."
                else:
                    action = "Alerta: Riesgo de ruptura excéntrica. Evitar frenados bruscos y cambios de dirección."
            elif ivn_score > 20.0 or acwr > 1.5 or iri_norm < 75:
                risk_level = "YELLOW"
                ivn_label = "ADVERTENCIA"
                if risk_driver == "SPRINT":
                    action = "Precaución: Sobrecarga lineal. Monitorear HSR."
                else:
                    action = "Precaución: Sobrecarga excéntrica. Monitorear aceleraciones/desaceleraciones."

        # 7. Persistencia en Daily_Performance
        doc_id = f"{athlete_id}_{date_str}"
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        athlete_name = athlete_id
        if athlete_snap.exists:
            ad = athlete_snap.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip()

        payload = {
            "athleteId": athlete_id,
            "athleteName": athlete_name,
            "date": date_str,
            "gps": gps_data,
            "acwr": acwr,
            "iri": imed_snc["iri"],
            "lapses": imed_snc["lapses"],
            "ivn_score": ivn_score,
            "carga_mec": round(carga_mec, 2),
            "risk_driver": risk_driver,
            "risk_level": risk_level,
            "ivn_label": ivn_label,
            "action": action,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "processed_at": firestore.SERVER_TIMESTAMP,
            "metadata": {
                "version": "3.0",
                "formula": "Carga_Mec * (ACWR / (IRI/100))",
                "adapter": "semantic-v2"
            }
        }'''

if target in content:
    print("Exact match found.")
    new_content = content.replace(target, replacement)
else:
    print("Exact match not found. Trying flexible match...")
    import re
    # We find the start and end of the block
    start_str = "# 5. Algoritmo IVN (Índice de Vulnerabilidad Neuro-Mecánica)"
    end_str = '''            "adapter": "semantic-v2"\n            }\n        }'''
    
    start_idx = content.find(start_str)
    end_idx = content.find(end_str)
    
    if start_idx != -1 and end_idx != -1:
        # Find the true start (8 spaces before)
        start_idx = content.rfind('        ', 0, start_idx)
        # Find the true end
        end_idx = end_idx + len(end_str)
        
        new_content = content[:start_idx] + replacement + content[end_idx:]
        print("Flexible match replaced.")
    else:
        print("Could not find blocks!")
        exit(1)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
    print("Successfully updated main.py")
