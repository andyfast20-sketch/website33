# Security Notes (API Keys)

## Current protections
- **No hardcoded API keys**: runtime keys are loaded from environment variables or the Super Admin UI.
- **Encrypted at rest (SQLite)**: keys stored in `call_logs.db` (`global_settings` table) are saved as `enc:v1:<token>`.
- **Master key storage**: the Fernet master key is stored in **Windows Credential Manager** (via Python `keyring`) unless you set `WEBSITE33_MASTER_KEY`.
- **No plaintext key echo**: the Super Admin API no longer returns full keys to the browser; it only returns a masked preview.

## Important: rotate keys
This repo previously contained plaintext secrets (API keys and a Google service account private key). Even though they are now removed from git going forward, **assume they are compromised**.

Rotate/revoke and replace these credentials:
- OpenAI API key
- DeepSeek API key(s)
- Speechmatics API key
- Vonage API secret
- PlayHT / ElevenLabs / Cartesia keys (if used)
- Google service account key (create a new key, revoke the old key)

## Recommended setup
- Prefer setting keys in the **Super Admin UI** so they get encrypted in `call_logs.db`.
- Keep `.env` minimal (or empty) and never commit it.
- Keep `google-credentials.json` **outside** the repo and point `GOOGLE_CREDENTIALS_PATH` to it.

## Recovery
If voice behavior breaks, revert to the known-good voice baseline tag:
- `git checkout v100`
