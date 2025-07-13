#!/usr/bin/env python3
"""
CC-CEDICT Dictionary Downloader and Parser
Downloads and parses the CC-CEDICT Chinese-English dictionary
"""

import os
import requests
import gzip
import sqlite3
import re
from datetime import datetime
import json

def download_cedict():
    """Download CC-CEDICT dictionary from MDBG"""
    print("Downloading CC-CEDICT dictionary...")
    
    # CC-CEDICT download URL
    url = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save compressed file
        with open("cedict_raw.txt.gz", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract the file
        with gzip.open("cedict_raw.txt.gz", "rt", encoding="utf-8") as f:
            content = f.read()
        
        # Save extracted file
        with open("cedict_raw.txt", "w", encoding="utf-8") as f:
            f.write(content)
        
        # Clean up compressed file
        os.remove("cedict_raw.txt.gz")
        
        print(f"Downloaded CC-CEDICT successfully. Size: {len(content)} characters")
        return True
        
    except Exception as e:
        print(f"Error downloading CC-CEDICT: {e}")
        return False

def parse_cedict_line(line):
    """Parse a single CC-CEDICT line"""
    # CC-CEDICT format: 
    # Traditional Simplified [pinyin] /definition1/definition2/
    
    # Skip comment lines
    if line.startswith('#') or not line.strip():
        return None
    
    # Regular expression to parse CC-CEDICT format
    pattern = r'^(.+?)\s+(.+?)\s+\[(.+?)\]\s+/(.+)/$'
    match = re.match(pattern, line.strip())
    
    if not match:
        return None
    
    traditional, simplified, pinyin, definitions = match.groups()
    
    # Split definitions by '/'
    definition_list = [d.strip() for d in definitions.split('/') if d.strip()]
    
    return {
        'traditional': traditional.strip(),
        'simplified': simplified.strip(),
        'pinyin': pinyin.strip(),
        'definitions': definition_list,
        'english': '; '.join(definition_list)  # Combined definitions
    }

def parse_cedict_file():
    """Parse the entire CC-CEDICT file"""
    print("Parsing CC-CEDICT file...")
    
    if not os.path.exists("cedict_raw.txt"):
        print("CC-CEDICT file not found. Please download first.")
        return []
    
    entries = []
    total_lines = 0
    parsed_lines = 0
    
    with open("cedict_raw.txt", "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            parsed_entry = parse_cedict_line(line)
            
            if parsed_entry:
                entries.append(parsed_entry)
                parsed_lines += 1
                
                if parsed_lines % 1000 == 0:
                    print(f"Parsed {parsed_lines} entries...")
    
    print(f"Parsing complete. Total lines: {total_lines}, Parsed entries: {parsed_lines}")
    return entries

def create_cedict_database(entries):
    """Create SQLite database with CC-CEDICT entries"""
    print("Creating CC-CEDICT database...")
    
    conn = sqlite3.connect("cedict.db")
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cedict_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        traditional TEXT NOT NULL,
        simplified TEXT NOT NULL,
        pinyin TEXT NOT NULL,
        english TEXT NOT NULL,
        definitions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(traditional, simplified, pinyin)
    )
    """)
    
    # Create indexes for fast searching
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_traditional ON cedict_entries(traditional)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_simplified ON cedict_entries(simplified)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pinyin ON cedict_entries(pinyin)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_english ON cedict_entries(english)")
    
    # Insert entries
    inserted = 0
    skipped = 0
    
    for entry in entries:
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO cedict_entries 
            (traditional, simplified, pinyin, english, definitions)
            VALUES (?, ?, ?, ?, ?)
            """, (
                entry['traditional'],
                entry['simplified'], 
                entry['pinyin'],
                entry['english'],
                json.dumps(entry['definitions'], ensure_ascii=False)
            ))
            
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
                
        except Exception as e:
            print(f"Error inserting entry: {e}")
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"Database created. Inserted: {inserted}, Skipped: {skipped}")
    return inserted

def get_cedict_stats():
    """Get statistics about the CC-CEDICT database"""
    if not os.path.exists("cedict.db"):
        return None
    
    conn = sqlite3.connect("cedict.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM cedict_entries")
    total_entries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT traditional) FROM cedict_entries")
    unique_traditional = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT simplified) FROM cedict_entries")
    unique_simplified = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_entries': total_entries,
        'unique_traditional': unique_traditional,
        'unique_simplified': unique_simplified
    }

def main():
    """Main function to download and process CC-CEDICT"""
    print("CC-CEDICT Dictionary Processor")
    print("=" * 40)
    
    # Download CC-CEDICT
    if not os.path.exists("cedict_raw.txt"):
        if not download_cedict():
            return
    
    # Parse the file
    entries = parse_cedict_file()
    
    if not entries:
        print("No entries parsed. Please check the file format.")
        return
    
    # Create database
    inserted = create_cedict_database(entries)
    
    # Show statistics
    stats = get_cedict_stats()
    if stats:
        print(f"\nCC-CEDICT Database Statistics:")
        print(f"Total entries: {stats['total_entries']:,}")
        print(f"Unique traditional characters: {stats['unique_traditional']:,}")
        print(f"Unique simplified characters: {stats['unique_simplified']:,}")
    
    print("\nCC-CEDICT processing complete!")

if __name__ == "__main__":
    main() 