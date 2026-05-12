import os

file_path = 'public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        <div class="athlete-metrics">
          <div class="metric-mini">
            <div class="val ${p.iri < THRESH.iriCritical ? 'text-red' : p.iri > THRESH.iriOptimal ? 'text-green' : 'text-yellow'}">${Math.round(p.iri||0)}</div>
            <div class="lbl">IRI</div>
          </div>
          <div class="metric-mini">
            <div class="val ${(p.lapses||0) > THRESH.lapses ? 'text-red' : 'text-green'}">${p.lapses||0}</div>
            <div class="lbl">LAPSES</div>
          </div>
          <div class="metric-mini">
            <div class="val">${getLoad(p)}</div>
            <div class="lbl">Z5</div>
          </div>
        </div>
        <span class="risk-badge ${ivn.badgeClass}">${ivn.label}</span>
        <button class="action-btn ${ivn.btnClass}">${ivn.action}</button>
      </div>`;'''

replacement = '''        <div class="athlete-metrics">
          <div class="metric-mini">
            <div class="val ${p.iri < THRESH.iriCritical ? 'text-red' : p.iri > THRESH.iriOptimal ? 'text-green' : 'text-yellow'}">${Math.round(p.iri||0)}</div>
            <div class="lbl">IRI</div>
          </div>
          <div class="metric-mini">
            <div class="val ${(p.lapses||0) > THRESH.lapses ? 'text-red' : 'text-green'}">${p.lapses||0}</div>
            <div class="lbl">LAPSES</div>
          </div>
          <div class="metric-mini">
            <div class="val">${p.carga_mec ? p.carga_mec : getLoad(p)}</div>
            <div class="lbl">C.MEC</div>
          </div>
        </div>
        <div class="athlete-status-col">
          <span class="risk-badge ${ivn.badgeClass}" style="margin-bottom: 4px;">${ivn.label}</span>
          <div class="action-text text-${ivn.btnClass}" style="font-size: 10.5px; line-height: 1.2; text-align: right; max-width: 200px;">${ivn.action}</div>
        </div>
      </div>`;'''

# Fallback string if formatting differs
target_fallback = '''<div class="val">${getLoad(p)}</div>'''
replacement_fallback = '''<div class="val">${p.carga_mec ? p.carga_mec : getLoad(p)}</div>'''

if target in content:
    new_content = content.replace(target, replacement)
    print("Exact match replaced in app.js")
else:
    print("Trying fallback replacement...")
    new_content = content.replace(target_fallback, replacement_fallback)
    new_content = new_content.replace('lbl">Z5</div>', 'lbl">C.MEC</div>')
    new_content = new_content.replace('<button class="action-btn ${ivn.btnClass}">${ivn.action}</button>', '<div class="action-text text-${ivn.btnClass}" style="font-size: 10.5px; line-height: 1.2; text-align: right; max-width: 200px;">${ivn.action}</div>')
    print("Fallback replaced.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
    print("Successfully updated app.js")
