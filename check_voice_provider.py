import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get account settings for the user from that call
c.execute("SELECT call_uuid, caller_number FROM calls ORDER BY created_at DESC LIMIT 1")
call = c.fetchone()

if call:
    uuid, phone = call
    print(f"Call: {uuid}")
    print(f"Phone: {phone}\n")
    
    # Find the user/account for this phone number
    c.execute("SELECT id, email, voice_provider FROM users WHERE phone_number = ?", (phone,))
    user = c.fetchone()
    
    if user:
        user_id, email, voice = user
        print(f"User: {email}")
        print(f"Voice Provider: {voice}\n")
        
        # Get account settings
        c.execute("SELECT ai_brain_provider, voice_provider FROM account_settings WHERE user_id = ?", (user_id,))
        settings = c.fetchone()
        
        if settings:
            brain, voice_prov = settings
            print(f"Account Settings:")
            print(f"  Brain: {brain}")
            print(f"  Voice: {voice_prov}")
    else:
        print("User not found - checking global settings")
        c.execute("SELECT ai_brain_provider FROM global_settings WHERE id = 1")
        global_brain = c.fetchone()
        if global_brain:
            print(f"Global Brain Provider: {global_brain[0]}")

conn.close()
