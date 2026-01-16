#!/usr/bin/env python3
"""Show the Vapi webhook URLs that need to be configured in Vapi dashboard"""
import sqlite3

def get_tunnel_url():
    """Get the current tunnel URL from database"""
    try:
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT public_url, tunnel_provider FROM global_settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return row[0].rstrip('/'), row[1]
        return None, None
    except Exception as e:
        print(f"Error getting tunnel URL: {e}")
        return None, None

tunnel_url, provider = get_tunnel_url()

if tunnel_url:
    print("\n" + "="*80)
    print("  VAPI WEBHOOK CONFIGURATION")
    print("="*80)
    print(f"\nCurrent Tunnel Provider: {provider}")
    print(f"Current Tunnel URL: {tunnel_url}\n")
    print("Configure these URLs in your Vapi Dashboard:")
    print("-" * 80)
    print(f"\n1. SERVER URL (End-of-Call Webhook):")
    print(f"   {tunnel_url}/webhooks/vapi-end-of-call")
    print(f"\n2. STATUS CALLBACK URL (Real-time updates - optional):")
    print(f"   {tunnel_url}/webhooks/vapi-status")
    print("\n" + "="*80)
    print("\nWithout these webhooks configured:")
    print("  ✗ Transcripts will show: '(Transcript pending from Vapi webhook)'")
    print("  ✗ Recording URLs won't be saved")
    print("  ✗ Summary will show: 'Waiting for Vapi transcript...'")
    print("  ✗ Listen button will be disabled/faded")
    print("\nAfter configuring the webhooks:")
    print("  ✓ Vapi will send transcripts after each call")
    print("  ✓ Recording URLs will be saved automatically")
    print("  ✓ AI summaries will be generated")
    print("  ✓ Listen button will be enabled")
    print("="*80 + "\n")
else:
    print("\n❌ No tunnel URL found in database!")
    print("Make sure the server is running and a tunnel (ngrok/cloudflare) is active.\n")
