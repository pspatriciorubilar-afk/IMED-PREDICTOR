import os

file_path = 'public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    const data = result.data;
    if (data.status === 'success') {
      showUploadResult('success', `
        <strong>Análisis Completado:</strong><br>
        Nivel de Riesgo: <span class="badge-${data.riskLevel.toLowerCase()}">${data.ivnLabel}</span><br>
        Documento guardado en <code>Daily_Performance</code>.
      `);
      showToast('success', '✓ Motor IVN', `Análisis finalizado: ${data.ivnLabel}`);'''

replacement = '''    const data = result.data;
    if (data.status === 'success') {
      let warningsHtml = '';
      if (data.warnings && data.warnings.length > 0) {
        warningsHtml = `<br><br><strong style="color:var(--yellow);">⚠️ Advertencias:</strong><br>` + 
                       data.warnings.map(w => `<span style="color:#ffcc00; font-size:12px;">- ${w}</span>`).join('<br>');
        showToast('warning', '⚠️ Métricas Faltantes', 'Revisa el reporte para más detalles');
      } else {
        showToast('success', '✓ Motor IVN', `Análisis finalizado: ${data.ivnLabel}`);
      }

      showUploadResult('success', `
        <strong>Análisis Completado:</strong><br>
        Nivel de Riesgo: <span class="badge-${data.riskLevel.toLowerCase()}">${data.ivnLabel}</span><br>
        Documento guardado en <code>Daily_Performance</code>.${warningsHtml}
      `);'''

# Because of the accents in the source code ("Anǭlisis Completado" shown in powershell), I will use a fallback block search if needed.

if "Análisis Completado" in content:
    content = content.replace(target, replacement)
    print("Replaced with exact accents")
else:
    # Try finding the substring
    target_fallback_1 = "    const data = result.data;"
    target_fallback_2 = "showToast('success'"
    
    # Let's do a simple replace on specific lines instead
    lines = content.split('\\n')
    for i, line in enumerate(lines):
        if "const data = result.data;" in line:
            # We found the block
            print("Found line. Replacing...")
            break

    # Actually, let's just do a clean regex replace
    import re
    pattern = r"const data = result\.data;\s+if \(data\.status === 'success'\) \{([\s\S]*?)showToast\('success'.*?\);"
    
    def replacer(match):
        return '''const data = result.data;
    if (data.status === 'success') {
      let warningsHtml = '';
      if (data.warnings && data.warnings.length > 0) {
        warningsHtml = `<br><br><strong style="color:var(--yellow);">⚠️ Advertencias:</strong><br>` + 
                       data.warnings.map(w => `<span style="color:#ffcc00; font-size:12px;">- ${w}</span>`).join('<br>');
        showToast('warning', '⚠️ Métricas Faltantes', 'Revisa el reporte para más detalles');
      } else {
        showToast('success', '✓ Motor IVN', `Análisis finalizado: ${data.ivnLabel}`);
      }

      showUploadResult('success', `
        <strong>Análisis Completado:</strong><br>
        Nivel de Riesgo: <span class="badge-${data.riskLevel.toLowerCase()}">${data.ivnLabel}</span><br>
        Documento guardado en <code>Daily_Performance</code>.${warningsHtml}
      `);'''

    content, num_subs = re.subn(pattern, replacer, content)
    print(f"Regex replacements made: {num_subs}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
