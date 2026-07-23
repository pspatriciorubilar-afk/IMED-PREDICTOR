
# Fix all \` (backslash+backtick) and \${...} (backslash+$) patterns in app_v411_final.js
# These should be proper template literal backticks

with open('public/app_v411_final.js', 'rb') as f:
    content = f.read()

original = content

# Replace \` with ` (backslash+backtick -> backtick)
# 0x5c = backslash, 0x60 = backtick
fixed = content.replace(b'\x5c\x60', b'\x60')

# Report what was changed
count = content.count(b'\x5c\x60')
print(f"Found and fixed {count} occurrences of backslash+backtick")

if fixed != original:
    # Back up original
    with open('public/app_v411_final.js.bak', 'wb') as f:
        f.write(original)
    # Write fixed version
    with open('public/app_v411_final.js', 'wb') as f:
        f.write(fixed)
    print("File fixed and backed up to app_v411_final.js.bak")
else:
    print("No changes made")
