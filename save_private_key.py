import sqlite3
import sys
sys.path.insert(0, '.')
from vonage_agent import encrypt_value, get_db_connection

private_key = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC3fTZIzFbXN1q0
77yfGQTVauPLhulfB3aiMD3UL+f8ERF6t1Oj1E/LNiSp+xsDFd3beojippQFLZAw
xw1PF1k9oIM8WR4VfLP0GpSeWnI0wq5ZlyKnmwQsw8pm3HBWhINh1TBw0Fqt/L/Z
/r6O3ZuB0t8n0TTs3EndrnIOC6rAQVgl8wcwhGPUwC9X2HAzeqjgC5wIgl8FfXCz
NC1a+W14ReLGJB14d4MLxbRlVRn62bB17Vga+cnPHHFphiaLpdlXZEahchxel3vE
IwZECOwdHTm4jB2nZsG5DdISOEW3M4wWIocYIUO3NqkzlH2lFP1Sl/hoBDM4zNz4
ixp7i5g5AgMBAAECggEAApD8I4JFJCs0Z/Oy8Qw36La/IyN6y98WOhA/6yH05g4E
jzF1eGUBrTNPibeXAgDqKpXRCI+BIj3oBoCgN2cZks62Cy/pZ25IM420Hq9f6cw/
xUXDgLHeufQOlof2g8VEc6e4TtmhLQ4MDmPdXTDtCgCtqZhH29i8aT71fiwMWjZB
sbJxu0Nv+AV+hJkyxx0BQDBT7UX9u0qWI6kXd+dKd9uyVF7pO5tl4kRPHQzRHTcK
BD67B4He+7eRz2HxWogwK1MhZhFuripPHHv21bflkEPWsS3w6Sc8xNOi8pWE5zYU
2fx0y7NvRBpeWSsxgC88F+LMN4nTgVF4OzlbF27wIQKBgQDcj48NnfQVDqT4wCji
JIhTVizOqKRjUG1MP/KojTNOI+uAJvoX8f4PzQmcCuLimbPp87ulbviFOidftnrP
P+p/1tNXwaC5hWZ7GuWjXD2E1WRVI4vuFlKq9rwXLHZikHNDRHQKk9DUEQK1bp6+
ekiN38X2DUfQyLifLaVpvb9M4QKBgQDU+MPcDMYTOkyiwT0m/B7iGswpnXjzSOQI
3yKfKaf+0ij4FyeeZOOC6Kk0/AhAYKaiyRBIF81SzQJT3lUuUVc9SnDSnGrseVRl
BGfIlYzVqE//kBxnQf/T2jCO4iLNjBDyDBIusSUfB6u+jhqHumzXlpls18YcyRu7
uym/dneeWQKBgGM/Lg3gj56SEmXkggEQk098rXjopeASprvy4ow5zWZR/3yRDWSM
/de6WaKfu2xf4Xdat4s/nhDFFEabZDOx/SE9V6hbdqlEf9LRTZfuv7fwFc/ByQt/
e/92OzjqRvMfMN6KBPVlgkiKxv9BIalweQluMjP/0dr/FyR5c79bJKPBAoGAcr6t
WCwRtF5e1/nhZtXEFfJ2OZ28gues5RLD5pldCDBXHoPrNq4I3olYUVHRaE4qud42
xYD9gTUvodxSbKgqpr0q2G6qNUqRq/OZrzrULHGI2Jreksu+eHhAXVt9gN2Ma70R
NtL+ux8462xI4wQQjH95nmkLNossRBNtRNkhTdECgYAVAHAu/sTxoYayIsWHW62z
BAxWBaCzBUMRfehFhzM69msbu5XQtvxYcZMuJVtQOeKojwFw13N6+ni3u05mP9Lr
lTIGJVHlQ3+ntMWYm2cXHRxfz9sxAZJk3+Ww+uNJL77sSzfYIQCJtpPiVkJsOx6n
MrF9KBH01dUUjzK6qmeOGw==
-----END PRIVATE KEY-----"""

# Encrypt the private key
encrypted_key = encrypt_value(private_key)

# Save to database
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('UPDATE global_settings SET vonage_private_key_pem = ? WHERE id = 1', (encrypted_key,))
conn.commit()
conn.close()

print("✅ Private key saved successfully!")
print(f"Encrypted value starts with: {encrypted_key[:50]}...")
