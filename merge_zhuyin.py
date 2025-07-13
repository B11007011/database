import sqlite3

# Paths to the databases
MAIN_DB = 'chinese_vietnamese_dict.db'
ZHUYIN_DB = 'zhuyin.db'

# Connect to both databases
main_conn = sqlite3.connect(MAIN_DB)
main_conn.row_factory = sqlite3.Row
main_cur = main_conn.cursor()

zhuyin_conn = sqlite3.connect(ZHUYIN_DB)
zhuyin_conn.row_factory = sqlite3.Row
zhuyin_cur = zhuyin_conn.cursor()

# Build a dictionary: word -> zhuyin
zhuyin_cur.execute('SELECT word, zhuyin FROM zhuyin')
zhuyin_map = {row['word']: row['zhuyin'] for row in zhuyin_cur.fetchall() if row['zhuyin']}

# Fetch all words from the main dictionary
main_cur.execute('SELECT id, word FROM dictionary')
rows = main_cur.fetchall()

update_count = 0
for row in rows:
    word = row['word']
    entry_id = row['id']
    zhuyin = zhuyin_map.get(word)
    if zhuyin:
        main_cur.execute('UPDATE dictionary SET zhuyin = ? WHERE id = ?', (zhuyin, entry_id))
        update_count += 1

main_conn.commit()

print(f"Updated zhuyin for {update_count} entries in the main dictionary.")

main_conn.close()
zhuyin_conn.close() 