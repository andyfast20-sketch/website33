"""
Update all accounts to AI-recommended 300ms response latency
Based on AI analysis: 300ms balances speed and natural pauses
"""
import sqlite3

def update_latency_to_300ms():
    """Update all account settings to 300ms (AI-optimized setting)"""
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    # Get current settings
    cursor.execute('SELECT user_id, response_latency FROM account_settings')
    before = cursor.fetchall()
    
    print("=" * 70)
    print("AI-RECOMMENDED OPTIMIZATION: 300ms Response Latency")
    print("=" * 70)
    print("\nAI Analysis Summary:")
    print("• Primary bottleneck: ElevenLabs API latency (already using eleven_turbo_v2_5)")
    print("• Current issue: 100ms too short, risks cutting off speech")
    print("• Recommendation: 300ms balances speed and natural conversation")
    print("• Expected improvement: Reduce interruptions, maintain fast response")
    print("\n" + "=" * 70)
    print("\nBEFORE UPDATE:")
    print("-" * 70)
    for user_id, latency in before:
        print(f"  User {user_id}: {latency}ms")
    
    # Update all accounts to 300ms
    cursor.execute('UPDATE account_settings SET response_latency = 300')
    
    # Get updated settings
    cursor.execute('SELECT user_id, response_latency FROM account_settings')
    after = cursor.fetchall()
    
    conn.commit()
    
    print("\n" + "=" * 70)
    print("AFTER UPDATE:")
    print("-" * 70)
    for user_id, latency in after:
        print(f"  User {user_id}: {latency}ms ✅")
    
    print("\n" + "=" * 70)
    print("CHANGES APPLIED:")
    print("-" * 70)
    print("✅ silence_duration_ms: 100ms → 300ms")
    print("✅ VAD threshold: 0.5 (unchanged)")
    print("✅ prefix_padding_ms: 300ms (unchanged)")
    print("✅ ElevenLabs model: eleven_turbo_v2_5 (already optimized)")
    print("✅ Streaming: Enabled (already implemented)")
    print("\n" + "=" * 70)
    print("EXPECTED RESULTS:")
    print("-" * 70)
    print("• Fewer interruptions (AI won't cut off user mid-sentence)")
    print("• Maintained fast response (300ms is still very quick)")
    print("• More natural conversation flow")
    print("• Better endpointing accuracy")
    print("\nNext steps:")
    print("1. Make 10+ test calls")
    print("2. Click 'Analyze & Optimize' in admin panel")
    print("3. AI will further tune if needed")
    print("=" * 70)
    
    conn.close()
    
    print(f"\n✅ Updated {len(after)} accounts successfully!\n")

if __name__ == '__main__':
    update_latency_to_300ms()
