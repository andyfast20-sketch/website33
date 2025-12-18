"""
Verify API keys are properly configured
"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=" * 60)
print("Global API Keys Status")
print("=" * 60)

cursor.execute('SELECT speechmatics_api_key, openai_api_key, last_updated, updated_by FROM global_settings WHERE id = 1')
result = cursor.fetchone()

if result:
    speechmatics_key, openai_key, last_updated, updated_by = result
    
    print("\n✅ Global Settings Found")
    print(f"   Last Updated: {last_updated}")
    print(f"   Updated By: {updated_by}")
    
    print("\n🎤 Speechmatics API Key:")
    if speechmatics_key:
        print(f"   Status: ✅ Configured")
        print(f"   Key: {speechmatics_key[:10]}...{speechmatics_key[-4:]}")
    else:
        print(f"   Status: ❌ Not configured")
    
    print("\n🤖 OpenAI API Key:")
    if openai_key:
        print(f"   Status: ✅ Configured")
        print(f"   Key: {openai_key[:10]}...{openai_key[-4:]}")
    else:
        print(f"   Status: ⚠️ Not configured (using hardcoded key)")
else:
    print("\n❌ No global settings found in database")

print("\n" + "=" * 60)
print("\nTo start the server with these keys:")
print("  python vonage_agent.py")
print("\nThen visit: http://localhost:5004/super-admin")
print("=" * 60)

conn.close()
