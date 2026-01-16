import sqlite3
from collections import defaultdict

def _fetchone(cursor, q, p=()):
    cursor.execute(q, p)
    return cursor.fetchone()

def _fetchall(cursor, q, p=()):
    cursor.execute(q, p)
    return cursor.fetchall()


def main():
    conn = sqlite3.connect("call_logs.db")
    cur = conn.cursor()

    last_call = _fetchone(
        cur,
        "SELECT call_uuid, caller_number, start_time, end_time FROM calls ORDER BY start_time DESC LIMIT 1",
    )
    if not last_call:
        print("No calls found.")
        return

    call_uuid, caller_number, start_time, end_time = last_call
    print("=== Latest call ===")
    print(f"call_uuid: {call_uuid}")
    print(f"caller_number: {caller_number}")
    print(f"start_time: {start_time}")
    print(f"end_time: {end_time}")

    events = _fetchall(
        cur,
        """
        SELECT turn_index, event_name, ms_from_turn_start
        FROM call_latency_events
        WHERE call_uuid = ?
        ORDER BY turn_index ASC, ms_from_turn_start ASC
        """,
        (call_uuid,),
    )

    if not events:
        print("\nNo latency events found for this call in call_latency_events.")
        return

    # Group events by turn
    by_turn = defaultdict(list)
    event_names = set()
    for turn_index, event_name, ms in events:
        by_turn[int(turn_index)].append((str(event_name), float(ms)))
        event_names.add(str(event_name))

    print("\n=== Event types seen ===")
    for name in sorted(event_names):
        print(f"- {name}")

    def first_ms(turn_events, name):
        for ename, ms in turn_events:
            if ename == name:
                return ms
        return None

    # Compute per-turn summary
    print("\n=== Per-turn latency summary ===")
    for turn in sorted(by_turn.keys()):
        turn_events = by_turn[turn]
        caller_stopped = first_ms(turn_events, "caller_stopped")
        brain_trig = first_ms(turn_events, "brain_triggered_openrouter")
        first_token = first_ms(turn_events, "first_token_openrouter")
        first_audio = (
            first_ms(turn_events, "first_audio_speechmatics")
            or first_ms(turn_events, "first_audio")
            or first_ms(turn_events, "assistant_first_audio")
        )

        print(f"\nTurn {turn}:")
        for ename, ms in turn_events:
            print(f"  +{ms:>6.0f}ms  {ename}")

        # Derived metrics
        if caller_stopped is not None:
            if brain_trig is not None:
                print(f"  caller_stopped -> brain_triggered_openrouter: {brain_trig - caller_stopped:.0f}ms")
            if first_token is not None:
                print(f"  caller_stopped -> first_token_openrouter: {first_token - caller_stopped:.0f}ms")
            if first_audio is not None:
                print(f"  caller_stopped -> first_audio: {first_audio - caller_stopped:.0f}ms")

            # Brain-only vs TTS-only breakdown if we have both
            if first_token is not None and first_audio is not None:
                print(f"  first_token -> first_audio (TTS start gap): {first_audio - first_token:.0f}ms")

    # Brain usage table (if present)
    try:
        brain_usage = _fetchone(
            cur,
            "SELECT brain_provider, openrouter_turns FROM call_brain_usage WHERE call_uuid = ?",
            (call_uuid,),
        )
        if brain_usage:
            print("\n=== Brain usage ===")
            print(f"brain_provider: {brain_usage[0]}")
            print(f"openrouter_turns: {brain_usage[1]}")
    except Exception as e:
        print(f"\n(Brain usage lookup failed: {e})")

    conn.close()


if __name__ == "__main__":
    main()
