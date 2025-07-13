#!/usr/bin/env python3
"""
Import Vietnamese vocabulary data from JSON files into the dictionary database
"""

import sqlite3
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class VietnameseDataImporter:
    def __init__(self, db_path="chinese_vietnamese_dictionary.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def clean_vietnamese_text(self, text: str) -> str:
        """Clean Vietnamese text by removing extra spaces and formatting"""
        if not text:
            return ""
        # Remove extra spaces and clean up
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove unwanted characters
        text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)]', '', text)
        return text
    
    def parse_hsk_level(self, filename: str) -> Optional[int]:
        """Extract HSK level from filename"""
        hsk_match = re.search(r'hsk_(\d+)', filename)
        if hsk_match:
            return int(hsk_match.group(1))
        return None
    
    def parse_tocfl_level(self, filename: str) -> Optional[int]:
        """Extract TOCFL level from filename"""
        tocfl_match = re.search(r'tocfl_(\d+)', filename)
        if tocfl_match:
            return int(tocfl_match.group(1))
        return None
    
    def get_category_from_filename(self, filename: str) -> str:
        """Extract category from filename"""
        # Remove extension and path
        name = Path(filename).stem
        # Convert underscores to spaces and clean up
        category = name.replace('_', ' ').replace('tu vung', '').strip()
        return category
    
    def import_json_file(self, file_path: str) -> int:
        """Import a single JSON file and return number of imported records"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"Warning: {file_path} does not contain a list")
                return 0
            
            filename = os.path.basename(file_path)
            hsk_level = self.parse_hsk_level(filename)
            tocfl_level = self.parse_tocfl_level(filename)
            category = self.get_category_from_filename(filename)
            
            imported_count = 0
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                # Extract basic fields
                word = item.get('w', '').strip()
                pinyin = item.get('p', '').strip()
                vi_meaning = self.clean_vietnamese_text(item.get('m', ''))
                en_meaning = item.get('m_en', '').strip()
                unit = item.get('unit', 0)
                
                if not word or not vi_meaning:
                    continue
                
                # Check if word already exists
                self.cursor.execute(
                    "SELECT id FROM dictionary WHERE word = ? AND vi_meaning = ?",
                    (word, vi_meaning)
                )
                existing = self.cursor.fetchone()
                
                if existing:
                    # Update existing record
                    word_id = existing[0]
                    self.cursor.execute('''
                        UPDATE dictionary 
                        SET pinyin = COALESCE(?, pinyin),
                            en_meaning = COALESCE(?, en_meaning),
                            hsk_level = COALESCE(?, hsk_level),
                            tocfl_level = COALESCE(?, tocfl_level),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (pinyin or None, en_meaning or None, hsk_level, tocfl_level, word_id))
                else:
                    # Insert new record
                    self.cursor.execute('''
                        INSERT INTO dictionary (
                            word, pinyin, vi_meaning, en_meaning, 
                            hsk_level, tocfl_level, frequency_rank
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (word, pinyin, vi_meaning, en_meaning, hsk_level, tocfl_level, unit))
                    
                    word_id = self.cursor.lastrowid
                    imported_count += 1
                
                # Add category tag
                if category:
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO tags (word_id, tag, category)
                        VALUES (?, ?, ?)
                    ''', (word_id, category, 'topic'))
            
            self.conn.commit()
            print(f"Imported {imported_count} new records from {filename}")
            return imported_count
            
        except Exception as e:
            print(f"Error importing {file_path}: {e}")
            return 0
    
    def import_all_vietnamese_files(self, directory="notebooks/note/"):
        """Import all Vietnamese JSON files from the specified directory"""
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist")
            return
        
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print(f"No JSON files found in {directory}")
            return
        
        total_imported = 0
        print(f"Found {len(json_files)} JSON files to import...")
        
        for file_path in sorted(json_files):
            imported = self.import_json_file(file_path)
            total_imported += imported
        
        print(f"\nTotal imported: {total_imported} records")
        
        # Update FTS index
        print("Updating full-text search index...")
        self.cursor.execute('''
            INSERT INTO dictionary_fts(dictionary_fts) VALUES('rebuild')
        ''')
        self.conn.commit()
        
        print("Import completed successfully!")
    
    def import_existing_databases(self):
        """Import data from existing zhuyin.db and mini_kanji.db"""
        
        # Import Zhuyin data
        if os.path.exists('zhuyin.db'):
            print("Importing Zhuyin data...")
            zhuyin_conn = sqlite3.connect('zhuyin.db')
            zhuyin_cursor = zhuyin_conn.cursor()
            
            zhuyin_cursor.execute("SELECT word, zhuyin FROM zhuyin")
            zhuyin_data = zhuyin_cursor.fetchall()
            
            for word, zhuyin in zhuyin_data:
                self.cursor.execute('''
                    UPDATE dictionary 
                    SET zhuyin = ?
                    WHERE word = ? AND zhuyin IS NULL
                ''', (zhuyin, word))
            
            zhuyin_conn.close()
            print(f"Updated {len(zhuyin_data)} records with Zhuyin data")
        
        # Import Hanviet data
        if os.path.exists('mini_kanji.db'):
            print("Importing Hanviet data...")
            hanviet_conn = sqlite3.connect('mini_kanji.db')
            hanviet_cursor = hanviet_conn.cursor()
            
            hanviet_cursor.execute("SELECT word, cn_vi FROM hanviet")
            hanviet_data = hanviet_cursor.fetchall()
            
            for word, hanviet in hanviet_data:
                self.cursor.execute('''
                    UPDATE dictionary 
                    SET hanviet_reading = ?
                    WHERE word = ? AND hanviet_reading IS NULL
                ''', (hanviet, word))
            
            hanviet_conn.close()
            print(f"Updated {len(hanviet_data)} records with Hanviet data")
        
        self.conn.commit()
    
    def get_import_statistics(self):
        """Get statistics about imported data"""
        stats = {}
        
        # Total records
        self.cursor.execute("SELECT COUNT(*) FROM dictionary")
        stats['total_records'] = self.cursor.fetchone()[0]
        
        # Records with different data types
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE pinyin IS NOT NULL")
        stats['with_pinyin'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE zhuyin IS NOT NULL")
        stats['with_zhuyin'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE hanviet_reading IS NOT NULL")
        stats['with_hanviet'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE en_meaning IS NOT NULL")
        stats['with_english'] = self.cursor.fetchone()[0]
        
        # HSK levels
        self.cursor.execute("SELECT hsk_level, COUNT(*) FROM dictionary WHERE hsk_level IS NOT NULL GROUP BY hsk_level")
        stats['hsk_levels'] = dict(self.cursor.fetchall())
        
        # TOCFL levels
        self.cursor.execute("SELECT tocfl_level, COUNT(*) FROM dictionary WHERE tocfl_level IS NOT NULL GROUP BY tocfl_level")
        stats['tocfl_levels'] = dict(self.cursor.fetchall())
        
        # Categories
        self.cursor.execute("SELECT category, COUNT(*) FROM tags GROUP BY category")
        stats['categories'] = dict(self.cursor.fetchall())
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main function to run the import process"""
    from create_dictionary_db import create_database_schema
    
    # Create database schema first
    create_database_schema()
    
    # Import data
    importer = VietnameseDataImporter()
    
    # Import Vietnamese vocabulary files
    importer.import_all_vietnamese_files()
    
    # Import existing database data
    importer.import_existing_databases()
    
    # Show statistics
    stats = importer.get_import_statistics()
    print("\n" + "="*50)
    print("IMPORT STATISTICS")
    print("="*50)
    print(f"Total records: {stats['total_records']}")
    print(f"With Pinyin: {stats['with_pinyin']}")
    print(f"With Zhuyin: {stats['with_zhuyin']}")
    print(f"With Hanviet: {stats['with_hanviet']}")
    print(f"With English: {stats['with_english']}")
    
    if stats['hsk_levels']:
        print(f"HSK Levels: {stats['hsk_levels']}")
    
    if stats['tocfl_levels']:
        print(f"TOCFL Levels: {stats['tocfl_levels']}")
    
    print(f"Categories: {len(stats['categories'])}")
    
    importer.close()

if __name__ == "__main__":
    main() 