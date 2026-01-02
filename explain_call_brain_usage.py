import argparse
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)
    )
    return cur.fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> List[str]:
    if not _table_exists(conn, table):
        return []
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(r[1]) for r in rows]


def _safe_json_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value if str(x)]
    s = str(value).strip()
    if not s:
        return []
    try:
        data = json.loads(s)
        if isinstance(data, list):
            return [str(x) for x in data if str(x)]
    except Exception:
        pass
    return [s]


def _pick_last_ended_call(conn: sqlite3.Connection) -> Optional[str]:
    if not _table_exists(conn, "calls"):
        return None
    cols = set(_columns(conn, "calls"))
    if "end_time" not in cols:
        return None
    # Prefer start_time if present.
    order_col = "start_time" if "start_time" in cols else "end_time"
    row = conn.execute(
        f"SELECT call_uuid FROM calls WHERE end_time IS NOT NULL ORDER BY {order_col} DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return str(row[0])


def _get_call_row(conn: sqlite3.Connection, call_uuid: str) -> Dict[str, Any]:
    cols = set(_columns(conn, "calls"))
    if not cols:
        return {}

    wanted = [
        "call_uuid",
        "user_id",
        "caller_number",
        "called_number",
        "start_time",
        "end_time",
        "duration",
        "call_mode",
        "selected_brain_provider",
        "effective_brain_provider",
        "brain_gating_reasons",
        "openai_fallback_turns",
        "openai_fallback_reasons",
    ]
    select_cols = [c for c in wanted if c in cols]
    if "call_uuid" not in select_cols:
        select_cols.insert(0, "call_uuid")

    row = conn.execute(
        f"SELECT {', '.join(select_cols)} FROM calls WHERE call_uuid = ? LIMIT 1",
        (call_uuid,),
    ).fetchone()
    if not row:
        return {}

    out: Dict[str, Any] = {k: row[k] for k in row.keys()}
    return out


def _get_usage_row(conn: sqlite3.Connection, call_uuid: str) -> Dict[str, Any]:
    if not _table_exists(conn, "call_brain_usage"):
        return {}
    cols = set(_columns(conn, "call_brain_usage"))
    wanted = [
        "openai_turns",
        "deepseek_turns",
        "groq_turns",
        "grok_turns",
        "openrouter_turns",
        "openai_chars",
        "deepseek_chars",
        "groq_chars",
        "grok_chars",
        "openrouter_chars",
        "updated_at",
    ]
    select_cols = [c for c in wanted if c in cols]
    if not select_cols:
        return {}

    row = conn.execute(
        f"SELECT {', '.join(select_cols)} FROM call_brain_usage WHERE call_uuid = ? LIMIT 1",
        (call_uuid,),
    ).fetchone()
    if not row:
        return {}
    return {k: row[k] for k in row.keys()}


def _get_account_settings(conn: sqlite3.Connection, user_id: Optional[int]) -> Dict[str, Any]:
    if user_id is None:
        return {}
    if not _table_exists(conn, "account_settings"):
        return {}
    cols = set(_columns(conn, "account_settings"))
    wanted = [
        "voice_provider",
        "calendar_booking_enabled",
        "tasks_enabled",
        "advanced_voice_enabled",
        "sales_detector_enabled",
        "use_elevenlabs",
    ]
    select_cols = [c for c in wanted if c in cols]
    if not select_cols:
        return {}

    row = conn.execute(
        f"SELECT {', '.join(select_cols)} FROM account_settings WHERE user_id = ? LIMIT 1",
        (user_id,),
    ).fetchone()
    if not row:
        return {}
    return {k: row[k] for k in row.keys()}


def _get_global_keys(conn: sqlite3.Connection) -> Dict[str, Any]:
    # Keys may be in global_settings; be robust.
    for table in ["global_settings", "settings"]:
        if not _table_exists(conn, table):
            continue
        cols = _columns(conn, table)
        if not cols:
            continue
        row = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        if not row:
            continue

        def has(col: str) -> bool:
            try:
                v = row[col]
            except Exception:
                return False
            s = str(v or "").strip()
            return bool(s)

        # Try common column names but also fallback to substring matching.
        def has_col_with_tokens(tokens: List[str]) -> bool:
            toks = [t.lower() for t in (tokens or []) if str(t).strip()]
            if not toks:
                return False
            for c in cols:
                c_low = c.lower()
                if all(t in c_low for t in toks) and has(c):
                    return True
            return False

        return {
            "source_table": table,
            "openrouter_key_present": has_col_with_tokens(["openrouter", "api_key"]),
            "speechmatics_key_present": has_col_with_tokens(["speechmatics", "api_key"]),
            "openai_key_present": has_col_with_tokens(["openai", "api_key"]),
            "raw_columns": cols,
        }

    return {}


def _compute_explanation(call: Dict[str, Any], usage: Dict[str, Any], acct: Dict[str, Any], keys: Dict[str, Any]) -> List[str]:
    selected = str(call.get("selected_brain_provider") or "").strip().lower()
    effective = str(call.get("effective_brain_provider") or "").strip().lower()
    call_mode = str(call.get("call_mode") or "").strip().lower()

    openai_turns = int(usage.get("openai_turns") or 0)
    openrouter_turns = int(usage.get("openrouter_turns") or 0)

    reasons: List[str] = []

    stored_gating = _safe_json_list(call.get("brain_gating_reasons"))
    if stored_gating:
        reasons.append(f"Stored gating reasons: {', '.join(stored_gating)}")

    fb_turns = int(call.get("openai_fallback_turns") or 0)
    fb_reasons = _safe_json_list(call.get("openai_fallback_reasons"))
    if fb_turns:
        reasons.append(f"OpenAI fallback turns recorded: {fb_turns}")
    if fb_reasons:
        reasons.append(f"OpenAI fallback reasons: {', '.join(fb_reasons)}")

    voice_provider = str(acct.get("voice_provider") or "").strip().lower()
    cal_enabled = acct.get("calendar_booking_enabled")

    has_openrouter = bool(keys.get("openrouter_key_present"))
    has_speechmatics = bool(keys.get("speechmatics_key_present"))

    if selected == "openrouter" and effective and effective != "openrouter":
        reasons.append(f"Selected OpenRouter but effective brain was '{effective}'.")
        if not has_openrouter:
            reasons.append("OpenRouter API key appears missing/empty in DB.")
        if voice_provider == "openai" and not has_speechmatics:
            reasons.append("No non-OpenAI TTS path: voice_provider=openai and Speechmatics key missing.")
        if cal_enabled in (1, True):
            reasons.append("Calendar booking enabled in account settings (non-OpenAI brains disable booking per-call).")

    # If the call was supposed to be OpenRouter but usage shows none.
    if effective == "openrouter" and openrouter_turns == 0 and openai_turns > 0:
        reasons.append(
            "Effective brain was OpenRouter but OpenRouter turns are 0 while OpenAI turns > 0. "
            "This usually means OpenRouter never started producing responses (timeouts/empty/errors) and the system fell back to OpenAI. "
            "If fallback reasons are empty, we need server logs from that call or make another call after restarting server to capture fallback reasons."
        )

    if call_mode and selected == "openrouter" and call_mode != "realtime":
        reasons.append(f"Call mode was '{call_mode}' (OpenRouter selection normally forces realtime for ASR-only mode).")

    if not reasons:
        reasons.append("No obvious gating/fallback reason found from DB fields.")

    return reasons


def explain(db_path: str, call_uuid: Optional[str]) -> Dict[str, Any]:
    with _connect(db_path) as conn:
        if call_uuid is None:
            call_uuid = _pick_last_ended_call(conn)
        if not call_uuid:
            return {"success": False, "error": "No ended call found in calls table."}

        call = _get_call_row(conn, call_uuid)
        usage = _get_usage_row(conn, call_uuid)
        acct = _get_account_settings(conn, call.get("user_id"))
        keys = _get_global_keys(conn)

        explanation = _compute_explanation(call, usage, acct, keys)

        return {
            "success": True,
            "call_uuid": call_uuid,
            "call": call,
            "usage": usage,
            "account_settings": acct,
            "key_presence": keys,
            "explanation": explanation,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="Explain why a call used OpenAI vs OpenRouter (and why OpenRouter may be 0).")
    ap.add_argument("--db", default="call_logs.db", help="Path to SQLite DB (default: call_logs.db)")
    ap.add_argument("--call", default=None, help="Call UUID to analyze (default: most recent ended call)")
    ap.add_argument("--json", action="store_true", help="Print JSON output")
    args = ap.parse_args()

    result = explain(args.db, args.call)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("success") else 2

    if not result.get("success"):
        print("ERROR:", result.get("error"))
        return 2

    call = result.get("call", {})
    usage = result.get("usage", {})

    selected = str(call.get("selected_brain_provider") or "?")
    effective = str(call.get("effective_brain_provider") or "?")
    mode = str(call.get("call_mode") or "?")

    print(f"Call UUID: {result.get('call_uuid')}")
    print(f"Selected: {selected} | Effective: {effective} | Call mode: {mode}")
    print(
        "Turns: "
        f"OpenAI={int(usage.get('openai_turns') or 0)} "
        f"OpenRouter={int(usage.get('openrouter_turns') or 0)} "
        f"DeepSeek={int(usage.get('deepseek_turns') or 0)} "
        f"Groq={int(usage.get('groq_turns') or 0)} "
        f"Grok={int(usage.get('grok_turns') or 0)}"
    )

    print("\nExplanation:")
    for line in result.get("explanation", []):
        print("-", line)

    fb_turns = int(call.get("openai_fallback_turns") or 0)
    if fb_turns:
        print(f"\nFallback turns to OpenAI: {fb_turns}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
