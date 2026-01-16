"""Clean fix for transfer narrative detection"""

with open('vonage_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line 4231 which has the duplicate "'uses transfer_call()' in text_lower):"
found_duplicate = False
for i, line in enumerate(lines):
    if i > 4220 and i < 4240 and "'uses transfer_call()' in text_lower):" in line:
        print(f"Found duplicate at line {i+1}: {line.strip()}")
        # Delete this line and the next line (the logger.info about TRANSFER FUNCTION)
        del lines[i:i+2]
        found_duplicate = True
        break

if found_duplicate:
    with open('vonage_agent.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Removed duplicate lines")
else:
    print("❌ Could not find duplicate")
