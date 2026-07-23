
# Read in binary to find exact byte sequence at line 1587
with open('public/app_v411_final.js', 'rb') as f:
    content = f.read()

lines = content.split(b'\n')
line = lines[1586]  # 0-indexed, so 1587 = index 1586
print(f"Line 1587 bytes: {line}")
print(f"Line 1587 hex: {line.hex()}")

# Check for backslash + backtick: 0x5c 0x60
bs_bt = b'\x5c\x60'
if bs_bt in line:
    print("Found backslash+backtick!")
else:
    print("No backslash+backtick found. Checking for other issues...")
    # Find any byte > 0x7e (non-ASCII)
    for i, b in enumerate(line):
        if b > 127:
            print(f"  Non-ASCII byte at position {i}: 0x{b:02x} ({chr(b)})")
