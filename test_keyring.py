import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

print("Testing keyring and Fernet...")
print("="*60)

try:
    import keyring
    print("✅ keyring module imported")
except Exception as e:
    print(f"❌ keyring import failed: {e}")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
    print("✅ Fernet imported")
except Exception as e:
    print(f"❌ Fernet import failed: {e}")
    sys.exit(1)

# Test creating a key
try:
    new_key = Fernet.generate_key()
    print(f"✅ Generated Fernet key: {new_key[:20]}...")
except Exception as e:
    print(f"❌ Failed to generate key: {e}")
    sys.exit(1)

# Test keyring storage
service = "website33"
key_name = "MASTER_FERNET_KEY"

try:
    # Try to get existing key
    existing = keyring.get_password(service, key_name)
    print(f"Existing key in keyring: {existing[:20] if existing else 'None'}...")
except Exception as e:
    print(f"❌ Failed to get key from keyring: {e}")
    existing = None

if not existing:
    try:
        # Store a new key
        test_key = Fernet.generate_key().decode("utf-8")
        keyring.set_password(service, key_name, test_key)
        print(f"✅ Stored new key in keyring")
        
        # Retrieve it
        retrieved = keyring.get_password(service, key_name)
        print(f"✅ Retrieved key from keyring: {retrieved[:20]}...")
    except Exception as e:
        print(f"❌ Failed to store/retrieve key: {e}")
        import traceback
        traceback.print_exc()
