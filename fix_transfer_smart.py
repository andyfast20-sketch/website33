"""Fix transfer narrative detection to catch natural language like '*transferring call to*'"""

with open('vonage_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line containing "Check for various ways AI might mention the function"
target_line_idx = None
for i, line in enumerate(lines):
    if 'Check for various ways AI might mention the function' in line:
        target_line_idx = i
        break

if target_line_idx is None:
    print("❌ Could not find target line")
    exit(1)

print(f"✅ Found target at line {target_line_idx + 1}")

# The new code block to insert after "text_lower = text.lower()"
new_code_lines = [
    "                transfer_narrative_detected = False\n",
    "                \n",
    "                # Check for explicit function mentions\n",
    "                if ('*transfer_call()' in text_lower or \n",
    "                    'transfer_call()' in text_lower or\n",
    "                    '*uses transfer_call()' in text_lower or\n",
    "                    'uses transfer_call()' in text_lower):\n",
    "                    transfer_narrative_detected = True\n",
    "                \n",
    "                # Check for natural language transfer narration (common with Claude/DeepSeek)\n",
    "                transfer_narratives = ['*transferring', '*transfer you', '*connecting you', '*putting you through', '*patching you through']\n",
    "                if any(pattern in text_lower for pattern in transfer_narratives):\n",
    "                    transfer_narrative_detected = True\n",
    "                \n",
    "                if transfer_narrative_detected:\n",
    "                    logger.info(f\"[{self.call_uuid}] 🔥 TRANSFER NARRATIVE detected (model narrating instead of calling function): '{text}'\")\n",
]

# Find the old if statement that checks for '*transfer_call()'
old_if_idx = None
for i in range(target_line_idx + 1, min(target_line_idx + 10, len(lines))):
    if "'*transfer_call()' in text_lower" in lines[i]:
        old_if_idx = i
        break

if old_if_idx is None:
    print("❌ Could not find old if statement")
    exit(1)

print(f"✅ Found old if statement at line {old_if_idx + 1}")

# Find the end of the old if block (looking for the line with 'uses transfer_call()'):
old_if_end_idx = old_if_idx
for i in range(old_if_idx, min(old_if_idx + 5, len(lines))):
    if 'uses transfer_call()' in lines[i] and ')' in lines[i]:
        old_if_end_idx = i
        break

print(f"✅ Old if block ends at line {old_if_end_idx + 1}")

# Replace: delete lines from old_if_idx to old_if_end_idx (inclusive), insert new code
new_lines = lines[:old_if_idx] + new_code_lines + lines[old_if_end_idx + 1:]

# Update the log messages that follow
for i in range(len(new_lines)):
    if 'TRANSFER FUNCTION mentioned in text' in new_lines[i]:
        # Already handled above
        pass
    elif 'Ignoring narrated transfer request' in new_lines[i]:
        new_lines[i] = new_lines[i].replace('Ignoring narrated', 'Blocking narrated')
    elif 'Transfer requested; asking caller for confirmation' in new_lines[i]:
        new_lines[i] = new_lines[i].replace('Transfer requested; asking caller for confirmation', 'Transfer narrative allowed (caller name check passed); executing real transfer')

with open('vonage_agent.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Successfully updated transfer narrative detection!")
print(f"   Replaced {old_if_end_idx - old_if_idx + 1} lines with {len(new_code_lines)} new lines")
