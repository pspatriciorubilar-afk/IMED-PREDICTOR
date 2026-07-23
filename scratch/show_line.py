
# Read the file in binary mode to find the actual bytes around line 1587
with open('public/app_v411_final.js', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Show lines 1585-1590 with repr to see exact characters
for i in range(1584, 1590):
    print(f"Line {i+1}: {repr(lines[i])}")
