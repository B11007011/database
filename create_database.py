#!/usr/bin/env python3
"""
Create the initial database schema for the Chinese-Vietnamese Dictionary
"""

import sqlite3
from pathlib import Path

def create_database(db_path="cedict.db"):
    """Create the database with all necessary tables"""
    # Remove existing database if it exists
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
    
    # Connect to the database (this will create it)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create main dictionary table
    cursor.execute('''
    CREATE TABLE dictionary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        traditional TEXT,
        simplified TEXT,
        pinyin TEXT,
        zhuyin TEXT,
        vi_meaning TEXT NOT NULL,
        en_meaning TEXT,
        part_of_speech TEXT,
        hsk_level INTEGER,
        tocfl_level INTEGER,
        frequency_rank INTEGER,
        hanviet_reading TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create examples table
    cursor.execute('''
    CREATE TABLE examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        chinese TEXT NOT NULL,
        pinyin TEXT,
        vietnamese TEXT,
        english TEXT,
        source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES dictionary (id) ON DELETE CASCADE
    )
    ''')
    
    # Create synonyms table
    cursor.execute('''
    CREATE TABLE synonyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        synonym TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES dictionary (id) ON DELETE CASCADE
    )
    ''')
    
    # Create antonyms table
    cursor.execute('''
    CREATE TABLE antonyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        antonym TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES dictionary (id) ON DELETE CASCADE
    )
    ''')
    
    # Create measure words table
    cursor.execute('''
    CREATE TABLE measure_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        measure_word TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES dictionary (id) ON DELETE CASCADE
    )
    ''')
    
    # Create tags table
    cursor.execute('''
    CREATE TABLE tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES dictionary (id) ON DELETE CASCADE
    )
    ''')
    
    # Create full-text search virtual table
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS dictionary_fts 
    USING fts5(
        word,
        pinyin,
        vi_meaning,
        en_meaning,
        hanviet_reading,
        tokenize = 'unicode61 remove_diacritics 2'
    )
    ''')
    
    # Create triggers to keep the FTS index up to date
    cursor.execute('''
    CREATE TRIGGER dictionary_ai AFTER INSERT ON dictionary
    BEGIN
        INSERT INTO dictionary_fts (
            rowid, word, pinyin, vi_meaning, en_meaning, hanviet_reading
        ) VALUES (
            new.id, new.word, new.pinyin, new.vi_meaning, new.en_meaning, new.hanviet_reading
        );
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER dictionary_ad AFTER DELETE ON dictionary
    BEGIN
        DELETE FROM dictionary_fts WHERE rowid = old.id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER dictionary_au AFTER UPDATE ON dictionary
    BEGIN
        UPDATE dictionary_fts SET
            word = new.word,
            pinyin = new.pinyin,
            vi_meaning = new.vi_meaning,
            en_meaning = new.en_meaning,
            hanviet_reading = new.hanviet_reading
        WHERE rowid = old.id;
    END;
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX idx_dictionary_word ON dictionary(word)')
    cursor.execute('CREATE INDEX idx_dictionary_pinyin ON dictionary(pinyin)')
    cursor.execute('CREATE INDEX idx_dictionary_hsk ON dictionary(hsk_level)')
    cursor.execute('CREATE INDEX idx_tags_tag ON tags(tag)')
    cursor.execute('CREATE INDEX idx_tags_category ON tags(category)')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"✅ Database schema created successfully at {db_path}")
    return True

if __name__ == "__main__":
    create_database()
