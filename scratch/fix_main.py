import sys

with open('functions/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 408:  # Line 409 in 1-indexed is index 408
        break
    new_lines.append(line)

new_lines.append('                "sync_method": "manual_sync_repair_v4"\n')
new_lines.append('            }, merge=True)\n')
new_lines.append('            synced += 1\n')
new_lines.append('            \n')
new_lines.append('        return {"success": True, "synced_records": synced}\n')
new_lines.append('    except Exception as e:\n')
new_lines.append('        return {"success": False, "error": str(e)}\n')

with open('functions/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix completed.")
