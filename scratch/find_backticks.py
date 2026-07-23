import re
with open('public/app_v411_final.js', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
    lines = content.split('\n')

print("Looking for escaped backticks (backslash + backtick):")
escaped_backtick = '\\\\'+'`'
for i, line in enumerate(lines, 1):
    if escaped_backtick in line:
        print(f"Line {i}: {line.rstrip()}")
