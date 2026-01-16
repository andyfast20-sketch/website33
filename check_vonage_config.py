#!/usr/bin/env python3
"""Check Vonage webhook configuration"""
import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get tunnel URL
cursor.execute("SELECT public_url, tunnel_provider FROM global_settings WHERE id = 1")
row = cursor.fetchone()

if row:
    tunnel_url = row[0]
    provider = row[1]
    
    print("\n" + "="*80)
    print("  CURRENT VONAGE CONFIGURATION")
    print("="*80)
    print(f"\nTunnel Provider: {provider}")
    print(f"Tunnel URL: {tunnel_url}")
    print(f"\nVonage should be configured with these URLs:")
    print(f"\nAnswer URL (HTTP POST):")
    print(f"  {tunnel_url}/webhooks/answer")
    print(f"\nEvent URL (HTTP POST):")
    print(f"  {tunnel_url}/webhooks/events")
    print("\n" + "="*80)
    print("\nIf you're getting ENGAGED TONE:")
    print("  1. Go to Vonage Dashboard → Applications")
    print("  2. Find your Voice Application")
    print("  3. Check the Answer URL matches above")
    print("  4. Make sure it says 'POST' not 'GET'")
    print("="*80 + "\n")
else:
    print("No tunnel URL found")

conn.close()
