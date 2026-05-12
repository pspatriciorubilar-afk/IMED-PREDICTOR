import os

file_path = 'functions/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        # Aplicar detección inteligente a cada métrica
        gps_data = {"decel_z5": 0.0, "accel_high": 0.0, "max_speed": 0.0, "distance": 0.0, "sprint_distance": 0.0}
        
        for metric, rules in semantic_rules.items():
            col = find_best_column(metric, rules)
            if col:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                gps_data[metric] = round(float(vals.mean()), 2) if not vals.empty else 0.0
                print(f"[GPS Adapter] ✓ '{metric}' → '{col}' = {gps_data[metric]}")
            else:
                print(f"[GPS Adapter] ✗ '{metric}' no detectado.")'''

replacement = '''        # Aplicar detección inteligente a cada métrica
        gps_data = {"decel_z5": 0.0, "accel_high": 0.0, "max_speed": 0.0, "distance": 0.0, "sprint_distance": 0.0}
        warnings = []
        
        for metric, rules in semantic_rules.items():
            col = find_best_column(metric, rules)
            if col:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                gps_data[metric] = round(float(vals.mean()), 2) if not vals.empty else 0.0
                print(f"[GPS Adapter] ✓ '{metric}' → '{col}' = {gps_data[metric]}")
            else:
                print(f"[GPS Adapter] ✗ '{metric}' no detectado.")
                warnings.append(f"No se detectó '{metric}'")
                
        if warnings:
            gps_data["warnings"] = warnings'''

if target in content:
    content = content.replace(target, replacement)
    print("Main logic replaced.")
else:
    print("Main logic target not found!")

rules_target = '''            "sprint_distance": {
                "must_any": ["sprint", "esprint"],'''

rules_replacement = '''            "sprint_distance": {
                "must_any": ["sprint", "esprint", "hsr", "alta vel", "high speed", "zona 5", "z5", "distancia sprint"],'''

if rules_target in content:
    content = content.replace(rules_target, rules_replacement)
    print("Rules replaced.")
else:
    print("Rules target not found!")

# Also update the response object in main.py to pass warnings back to the frontend
response_target = '''        return {
            "status": "success",
            "ivnScore": ivn_score,
            "riskLevel": risk_level,
            "ivnLabel": ivn_label,
            "action": action
        }'''

response_replacement = '''        return {
            "status": "success",
            "ivnScore": ivn_score,
            "riskLevel": risk_level,
            "ivnLabel": ivn_label,
            "action": action,
            "warnings": warnings
        }'''

if response_target in content:
    content = content.replace(response_target, response_replacement)
    print("Response replaced.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
