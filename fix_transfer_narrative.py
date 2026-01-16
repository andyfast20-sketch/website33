import re

with open('vonage_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the transfer narrative detection code
old_code = """                # Check for various ways AI might mention the function
                text_lower = text.lower()
                if ('*transfer_call()' in text_lower or 
                    'transfer_call()' in text_lower or
                    '*uses transfer_call()' in text_lower or
                    'uses transfer_call()' in text_lower):
                    logger.info(f"[{self.call_uuid}] 🔥 TRANSFER FUNCTION mentioned in text (model doesn't support tool calling): '{text}'")
                    allowed, deny_reason = self._is_transfer_allowed_now()
                    if not allowed:
                        logger.warning(f"[{self.call_uuid}] 🚫 Ignoring narrated transfer request due to transfer_instructions: {deny_reason}")
                        safe_text = "I can take a message. What's your name and the best number to call you back on?"
                        # Update transcript with what we will actually say.
                        try:
                            if self.transcript_parts and self.transcript_parts[-1].startswith(f"{CONFIG['AGENT_NAME']}: "):
                                self.transcript_parts[-1] = f"{CONFIG['AGENT_NAME']}: {safe_text}"
                        except Exception:
                            pass
                        text = safe_text
                    else:
                        logger.info(f"[{self.call_uuid}] 🔥 Transfer requested; asking caller for confirmation")"""

new_code = """                # Check for various ways AI might mention the function or narrate a transfer action
                text_lower = text.lower()
                transfer_narrative_detected = False
                
                # Check for explicit function mentions
                if ('*transfer_call()' in text_lower or 
                    'transfer_call()' in text_lower or
                    '*uses transfer_call()' in text_lower or
                    'uses transfer_call()' in text_lower):
                    transfer_narrative_detected = True
                
                # Check for natural language transfer narration (common with Claude/DeepSeek/OpenRouter)
                transfer_narratives = [
                    '*transferring',
                    '*transfer you',
                    '*connecting you',
                    '*putting you through',
                    '*patching you through'
                ]
                if any(pattern in text_lower for pattern in transfer_narratives):
                    transfer_narrative_detected = True
                
                if transfer_narrative_detected:
                    logger.info(f"[{self.call_uuid}] 🔥 TRANSFER NARRATIVE detected in text (model narrating instead of calling function): '{text}'")
                    allowed, deny_reason = self._is_transfer_allowed_now()
                    if not allowed:
                        logger.warning(f"[{self.call_uuid}] 🚫 Blocking narrated transfer due to transfer_instructions: {deny_reason}")
                        safe_text = "I can take a message. What's your name and the best number to call you back on?"
                        # Update transcript with what we will actually say.
                        try:
                            if self.transcript_parts and self.transcript_parts[-1].startswith(f"{CONFIG['AGENT_NAME']}: "):
                                self.transcript_parts[-1] = f"{CONFIG['AGENT_NAME']}: {safe_text}"
                        except Exception:
                            pass
                        text = safe_text
                    else:
                        logger.info(f"[{self.call_uuid}] 🔥 Transfer narrative allowed (caller name check passed); executing real transfer")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('vonage_agent.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Transfer narrative detection updated successfully!")
else:
    print("❌ Could not find the exact code to replace")
    print("Searching for approximate match...")
    if "Check for various ways AI might mention the function" in content:
        print("Found the section but exact match failed - manual edit may be needed")
