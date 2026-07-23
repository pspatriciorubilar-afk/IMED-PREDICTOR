
# Find all lines with \\` pattern (literal backslash + backtick in the file)
with open('public/app_v411_final.js', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

bad_pattern = '\\\\`'  # in file: \`
for i, line in enumerate(lines, 1):
    if bad_pattern in line:
        print(f"Line {i}: {repr(line.rstrip())}")

print(f"\nTotal bad lines: {sum(1 for l in lines if bad_pattern in l)}")
