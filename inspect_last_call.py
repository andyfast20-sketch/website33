import json
import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path("call_logs.db")
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path.resolve()}")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print("tables:", tables)

    if "global_settings" in tables:
        try:
            cur.execute("PRAGMA table_info(global_settings)")
            gs_cols = [r[1] for r in cur.fetchall()]

            to_show = ["ai_brain_provider", "speechmatics_api_key", "openai_api_key", "openrouter_api_key"]
            present = [c for c in to_show if c in gs_cols]
            print("global_settings.cols_present:", present)

            cur.execute(
                "SELECT ai_brain_provider, speechmatics_api_key, openai_api_key, openrouter_api_key FROM global_settings WHERE id = 1"
            )
            row = cur.fetchone()
            if row:
                ai_brain_provider, speechmatics_raw, openai_raw, openrouter_raw = row
                print("global_settings.ai_brain_provider:", ai_brain_provider)

                def _mask_secret(v):
                    s = "" if v is None else str(v)
                    s = s.strip()
                    if not s:
                        return {"present": False}
                    prefix = s[:8]
                    return {
                        "present": True,
                        "len": len(s),
                        "prefix": prefix,
                        "looks_encrypted": (s.startswith("enc:") or s.startswith("ENC:")),
                    }

                print("global_settings.speechmatics_api_key:", _mask_secret(speechmatics_raw))
                print("global_settings.openai_api_key:", _mask_secret(openai_raw))
                print("global_settings.openrouter_api_key:", _mask_secret(openrouter_raw))
        except Exception as e:
            print("global_settings.ai_brain_provider: error", e)

    call_table = None
    for candidate in ("calls", "call_logs", "recent_calls", "call_records"):
        if candidate in tables:
            call_table = candidate
            break

    print("call_table:", call_table)
    if not call_table:
        return

    cur.execute(f"PRAGMA table_info({call_table})")
    cols = [r[1] for r in cur.fetchall()]
    print("columns:", cols)

    cur.execute(f"SELECT * FROM {call_table} ORDER BY 1 DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("no rows")
        return

    last = dict(zip(cols, row))
    brainish = {k: last.get(k) for k in cols if any(s in k.lower() for s in ("brain", "provider", "model", "voice"))}

    print("last_call_brainish:", json.dumps(brainish, default=str))
    print("last_call_full:", json.dumps(last, default=str)[:2000])

    # Helpful per-user settings (voice provider + response latency can explain long pauses)
    user_id = last.get("user_id")
    if user_id and "account_settings" in tables:
        try:
            cur.execute("PRAGMA table_info(account_settings)")
            acols = [r[1] for r in cur.fetchall()]
            wanted = [c for c in ("user_id", "voice_provider", "response_latency", "use_elevenlabs") if c in acols]
            if wanted:
                cur.execute(f"SELECT {', '.join(wanted)} FROM account_settings WHERE user_id = ?", (user_id,))
                arow = cur.fetchone()
                if arow:
                    print("account_settings:", dict(zip(wanted, arow)))
        except Exception as e:
            print("account_settings: error", e)

    call_uuid = str(last.get("call_uuid") or "").strip()
    if not call_uuid:
        return

    if "call_brain_usage" in tables:
        cur.execute("PRAGMA table_info(call_brain_usage)")
        bcols = [r[1] for r in cur.fetchall()]
        cur.execute("SELECT * FROM call_brain_usage WHERE call_uuid = ? ORDER BY updated_at DESC LIMIT 1", (call_uuid,))
        brow = cur.fetchone()
        if brow:
            b = dict(zip(bcols, brow))
            print("call_brain_usage:", json.dumps(b, default=str))
        else:
            print("call_brain_usage: none for call_uuid", call_uuid)


if __name__ == "__main__":
    main()
