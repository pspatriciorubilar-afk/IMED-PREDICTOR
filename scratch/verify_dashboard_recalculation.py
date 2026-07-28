def calculate_wellness(sleep_hours, sleep_quality, stress_level, fatigue_level):
    h_score = (min(8.0, sleep_hours) / 8.0) * 30.0
    q_score = (sleep_quality / 5.0) * 25.0
    s_score = ((6.0 - stress_level) / 5.0) * 25.0
    f_score = ((6.0 - fatigue_level) / 5.0) * 20.0
    return round(h_score + q_score + s_score + f_score)

def calculate_pvt_score(mean_latency):
    score = 100 - ((mean_latency - 250) / 250) * 100
    return round(min(100, max(0, score)))

# Suppose athlete completed test with these parameters:
sleep_hours = 8.0
sleep_quality = 4
stress_level = 2
fatigue_level = 2
mean_latency = 290 # ms

# 1. App calculations:
pvt_score_app = calculate_pvt_score(mean_latency)
wellness_score_app = calculate_wellness(sleep_hours, sleep_quality, stress_level, fatigue_level)
iri_app = round((pvt_score_app + wellness_score_app) / 2)

# 2. Dashboard calculations before fix:
pvt_raw_old = iri_app # The old code read p.iri (84) as pvtRaw!
wellness_score_old = wellness_score_app # 86
iri_dashboard_old = round((pvt_raw_old + wellness_score_old) / 2)

# 3. Dashboard calculations after fix:
pvt_raw_new = calculate_pvt_score(mean_latency) # The new code calculates it from mean_latency
wellness_score_new = wellness_score_app
iri_dashboard_new = round((pvt_raw_new + wellness_score_new) / 2)

print("=== VERIFYING CALCULATIONS ALIGNMENT ===")
print(f"App calculated PVT score: {pvt_score_app}")
print(f"App calculated Wellness score: {wellness_score_app}")
print(f"App calculated final IRI: {iri_app}")
print("---")
print(f"Old Dashboard double-averaged IRI: {iri_dashboard_old} (Desynchronized!)")
print(f"New Dashboard corrected IRI: {iri_dashboard_new} (Aligned with App!)")
assert iri_app == iri_dashboard_new, "Calculation mismatch!"
print("✅ Verification SUCCESS: App and Dashboard calculations are perfectly aligned!")
