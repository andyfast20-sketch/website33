import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()
c.execute('UPDATE calls SET summary = NULL WHERE summary LIKE "%generation failed%"')
conn.commit()
print(f'Cleared {c.rowcount} summaries')
conn.close()
