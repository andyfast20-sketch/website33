import asyncio
import sqlite3
from vonage_agent import CallLogger

async def main():
    conn = sqlite3.connect('call_logs.db')
    c = conn.cursor()
    c.execute('SELECT call_uuid FROM calls WHERE summary IS NULL')
    uuids = [r[0] for r in c.fetchall()]
    conn.close()
    
    print(f'Found {len(uuids)} calls needing summaries')
    
    for uuid in uuids:
        print(f'Generating summary for {uuid}...')
        await CallLogger.generate_summary(uuid)
    
    print('Done!')

if __name__ == "__main__":
    asyncio.run(main())
