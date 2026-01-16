import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Count fillers
c.execute('SELECT COUNT(*) FROM global_filler_phrases')
count = c.fetchone()[0]
print(f'Total Fillers in Database: {count}')

# Get sample fillers
c.execute('SELECT voice_id, slot, phrase FROM global_filler_phrases LIMIT 10')
fillers = c.fetchall()

print('\nSample Fillers:')
for voice_id, slot, phrase in fillers:
    phrase_preview = phrase[:60] if phrase else "NO PHRASE"
    print(f'  [{voice_id}] Slot {slot}: {phrase_preview}')

# Group by voice_id
c.execute('SELECT voice_id, COUNT(*) FROM global_filler_phrases GROUP BY voice_id')
by_voice = c.fetchall()
print('\nFillers by voice:')
for voice, cnt in by_voice:
    print(f'  {voice}: {cnt}')

# Check if filler audio files exist in fillers_sarah directory
import os
sarah_dir = 'fillers_sarah'
if os.path.exists(sarah_dir):
    wav_files = [f for f in os.listdir(sarah_dir) if f.endswith('.wav')]
    print(f'\nFiller audio files in {sarah_dir}: {len(wav_files)}')
    for f in wav_files[:5]:
        print(f'  {f}')
else:
    print(f'\n⚠️ Directory {sarah_dir} does not exist!')

conn.close()
