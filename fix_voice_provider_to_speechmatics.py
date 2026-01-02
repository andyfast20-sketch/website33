import argparse
import sqlite3


def counts(cur: sqlite3.Cursor) -> None:
    def fetchall(sql: str):
        return cur.execute(sql).fetchall()

    cols = [r[1] for r in fetchall("pragma table_info(account_settings)")]
    print("account_settings columns:", cols)

    if "voice_provider" in cols:
        print("voice_provider counts:", fetchall("select coalesce(voice_provider,'(null)'), count(*) from account_settings group by voice_provider order by count(*) desc"))
    else:
        print("voice_provider column not found")

    if "voice" in cols:
        print("voice counts:", fetchall("select coalesce(voice,'(null)'), count(*) from account_settings group by voice order by count(*) desc"))
    else:
        print("voice column not found")


def apply(cur: sqlite3.Cursor) -> None:
    cols = [r[1] for r in cur.execute("pragma table_info(account_settings)").fetchall()]
    if "voice_provider" not in cols:
        raise SystemExit("account_settings.voice_provider column not present; cannot apply fix")

    # Only flip accounts that are effectively on the OpenAI default.
    # Leave explicitly configured non-openai providers alone.
    cur.execute(
        """
        update account_settings
        set voice_provider = 'speechmatics'
        where voice_provider is null
           or trim(voice_provider) = ''
           or lower(voice_provider) = 'openai'
        """
    )

    if "voice" in cols:
        cur.execute(
            """
            update account_settings
            set voice = 'sarah'
            where voice is null
               or trim(voice) = ''
               or lower(voice) = 'shimmer'
            """
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="call_logs.db")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    cur = con.cursor()

    print("db:", args.db)
    print("--- before ---")
    counts(cur)

    if args.apply:
        print("\nApplying fix...")
        apply(cur)
        con.commit()
        print("Applied.")

        print("\n--- after ---")
        counts(cur)

    con.close()


if __name__ == "__main__":
    main()
