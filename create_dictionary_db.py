#!/usr/bin/env python3
"""
Chinese-Vietnamese Dictionary Database Setup
Creates the main database schema for the Chinese-Vietnamese dictionary
"""

import sqlite3
import json
import os
from pathlib import Path

def create_database_schema(db_path="chinese_vietnamese_dictionary.db"):
    """Create the database schema for Chinese-Vietnamese dictionary"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Main dictionary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary (
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
    
    # Example sentences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            chinese TEXT NOT NULL,
            pinyin TEXT,
            vietnamese TEXT NOT NULL,
            english TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES dictionary (id)
        )
    ''')
    
    # Synonyms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            synonym TEXT NOT NULL,
            FOREIGN KEY (word_id) REFERENCES dictionary (id)
        )
    ''')
    
    # Antonyms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS antonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            antonym TEXT NOT NULL,
            FOREIGN KEY (word_id) REFERENCES dictionary (id)
        )
    ''')
    
    # Measure words table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measure_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            measure_word TEXT NOT NULL,
            FOREIGN KEY (word_id) REFERENCES dictionary (id)
        )
    ''')
    
    # Tags/Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            tag TEXT NOT NULL,
            category TEXT,
            FOREIGN KEY (word_id) REFERENCES dictionary (id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON dictionary (word)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_simplified ON dictionary (simplified)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_traditional ON dictionary (traditional)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pinyin ON dictionary (pinyin)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vi_meaning ON dictionary (vi_meaning)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hsk_level ON dictionary (hsk_level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tocfl_level ON dictionary (tocfl_level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hanviet ON dictionary (hanviet_reading)')
    
    # Full-text search indexes
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS dictionary_fts USING fts5(
            word, traditional, simplified, pinyin, vi_meaning, en_meaning,
            content='dictionary',
            content_rowid='id'
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database schema created successfully at: {db_path}")

def get_database_info(db_path="chinese_vietnamese_dictionary.db"):
    """Get information about the database"""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist yet.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"Database: {db_path}")
    print("Tables:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} records")
    
    conn.close()

if __name__ == "__main__":
    create_database_schema()
    get_database_info() 