import sys
sys.path.insert(0, '.')
from vonage_agent import _encrypt_secret
import sqlite3

private_key = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDjCIEZ0RbV9/6+
ZU+UTzmSH5BDN5xFiHpo9BtIDRSYQApm0/RJjNR/aDjo9cXzrEZJpKiwU+U/AP70
OUPfdTygqMCj0gsTc4mRI6XESq9Nt6Xc0q1SczPcMFSPpT9Jkm7i7psCAFgq9jwt
Xd37qy1rBzudx+JFN6o0LoWq7V/RoH/0sqg3PmCX+W6RYsxkSAt+tA32i2+htQem
zj3K20Kt1Ed7od6UH4Y5IVxh9ed4Zk8tdwZ5K3vIsDCJpGy+GCVhlfL5TNwCX55Z
NJ88w4BJnUUI69uI0P3zFLAgkQzf9pXWp368UbPCQhv2ByF9u8NfHZi0TzSEHWDL
8kd31q5fAgMBAAECggEACXd0NqWrmTFvKFsK5e+MKLLAB7JJn40EABAjR3sjWQCp
zl7Xju314F6LdowYL6oG/922gPlTYK/dPnhZNnfQSg/igUVqKJ35/8wBbTCccOLc
lVtQvQeu6ZpqtD10nAM+NDoByz2rb3zD+c1+5GMSkKXR3ELjUijyvZx6mCvjGz3N
Ay5xoakSoByQpOmEwz+9VXtJWV/ei0vGiPYr10FCBnpQ/D+Wsvy6E7UTcd5BEzAl
nEAk29i/9l8OYdKBzueYl7zG7tTmMhgU+UFmHCU5/zimFd/buEsYJbaXHbOU6sSX
iZ6qTeLUJ/m8JRdbSU3ETSZfT+tRWsv9aRjk5SWBJQKBgQD6P/qAkPklfjdtoCaH
E5aclHEtyVFFmehKMB7C4HN59nQGUEvW6AW2tE7SNjTGY8sUhtgxbzrYP5pZbKNl
phj0mOWWX1rj+HL7VGrxyBO828ERe4nuywGXCvn0sgykQVzttiNCs2saDpPGpMrb
OdZ2XZ/XkMnLrhuUNuDgP/R3qwKBgQDoP/XcYIQGq1QVW321cbJJkBLHAikhoW77
ZGOeHkRT8y10iZcWIR+tqNszRNxeDZGlUL9/Y0qZXoPo2Vb8YCiIKm2noQilddPO
IHkPQPsk174euZhye+Bt4peuHHQbSCa4TfOBcnAXR6PxNUpdt5OS3JMF/plUENC4
KUUKW89gHQKBgCo0kh4O1UZChDyj7vuHDTa5PmFXe7J+Y5Pni7iYPEGMlELgVfoX
xabrwANqCvqOqBh9KYck2ErSZ0i/rssc+UZ/ZvE2gdDC/TlwIl1GvjVy5pv5Nukk
Kc98lW10ffdR4sdgmY/NTLnnTXsKHgBdP9NUtPmZPL9yTMpxevm3L5bjAoGBAKRB
SBL6N6W32hnYwQloRd19Baq1vn1IfQNStpmHcm+lFsrK3I4MEylwuMaDtw7VreIr
P6RKhuH9VHGD9N886q2SxEa/vyu2L3wivzuoi3Y9FvsH6+db8RgGH5xGB1+cIbZL
eyJb2ya7xhi7xcKOKNK/KUQeEjbARb1ZgriWwg2JAoGBAJ2OdcRyfIwgikgHNOVU
zPR6/egT13qJ/S4Y23Offk8Xbs5mWwDy9BoukFy8pVC9oUZhnZt0BuH1xghd18fh
DXml97zbIZCMY5haPIMOInmKryowqYmyxupWWY793MRiEAUp/R7jo2+zHWckmEZY
5zcLIwmonHCCzgqbhVk/Pfcs
-----END PRIVATE KEY-----"""

encrypted = _encrypt_secret(private_key)
conn = sqlite3.connect('call_logs.db')
c = conn.cursor()
c.execute('UPDATE global_settings SET vonage_private_key_pem = ? WHERE id = 1', (encrypted,))
conn.commit()
conn.close()

print('✅ Saved private key to database')
print(f'✅ Key length: {len(private_key)} chars')
print(f'✅ Encrypted length: {len(encrypted)} chars')
