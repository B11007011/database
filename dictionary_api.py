#!/usr/bin/env python3
"""
Chinese-Vietnamese Dictionary API
Provides search and query functionality for the dictionary
"""

import sqlite3
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DictionaryEntry:
    """Data class for dictionary entries"""
    id: int
    word: str
    traditional: Optional[str]
    simplified: Optional[str]
    pinyin: Optional[str]
    zhuyin: Optional[str]
    vi_meaning: str
    en_meaning: Optional[str]
    part_of_speech: Optional[str]
    hsk_level: Optional[int]
    tocfl_level: Optional[int]
    frequency_rank: Optional[int]
    hanviet_reading: Optional[str]
    examples: List[Dict] = None
    synonyms: List[str] = None
    antonyms: List[str] = None
    measure_words: List[str] = None
    tags: List[str] = None

class ChineseVietnameseDictionary:
    def __init__(self, db_path="chinese_vietnamese_dictionary.db"):
        self.db_path = db_path
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Dictionary database not found: {db_path}")
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.cursor = self.conn.cursor()
    
    def search_word(self, query: str, limit: int = 20) -> List[DictionaryEntry]:
        """Search for words by Chinese characters or Vietnamese meaning"""
        # Clean the query
        query = query.strip()
        
        # First try exact match
        results = self._search_exact(query, limit)
        if results:
            return results
        
        # Then try fuzzy search
        return self._search_fuzzy(query, limit)
    
    def _search_exact(self, query: str, limit: int) -> List[DictionaryEntry]:
        """Search for exact matches"""
        sql = '''
            SELECT * FROM dictionary 
            WHERE word = ? OR vi_meaning = ? OR pinyin = ?
            ORDER BY frequency_rank ASC, hsk_level ASC, id ASC
            LIMIT ?
        '''
        self.cursor.execute(sql, (query, query, query, limit))
        return self._build_entries(self.cursor.fetchall())
    
    def _search_fuzzy(self, query: str, limit: int) -> List[DictionaryEntry]:
        """Search using fuzzy matching and full-text search"""
        results = []
        
        # Try full-text search first
        if len(query) > 1:
            fts_sql = '''
                SELECT d.* FROM dictionary d
                JOIN dictionary_fts fts ON d.id = fts.rowid
                WHERE dictionary_fts MATCH ?
                ORDER BY rank, d.frequency_rank ASC, d.hsk_level ASC
                LIMIT ?
            '''
            self.cursor.execute(fts_sql, (query, limit))
            results.extend(self.cursor.fetchall())
        
        # If still no results, try LIKE search
        if not results:
            like_sql = '''
                SELECT * FROM dictionary 
                WHERE word LIKE ? OR vi_meaning LIKE ? OR pinyin LIKE ?
                ORDER BY 
                    CASE 
                        WHEN word LIKE ? THEN 1
                        WHEN vi_meaning LIKE ? THEN 2
                        WHEN pinyin LIKE ? THEN 3
                        ELSE 4
                    END,
                    frequency_rank ASC, hsk_level ASC
                LIMIT ?
            '''
            like_query = f"%{query}%"
            start_query = f"{query}%"
            self.cursor.execute(like_sql, (
                like_query, like_query, like_query,
                start_query, start_query, start_query,
                limit
            ))
            results.extend(self.cursor.fetchall())
        
        return self._build_entries(results)
    
    def search_by_hsk_level(self, level: int, limit: int = 50) -> List[DictionaryEntry]:
        """Search words by HSK level"""
        sql = '''
            SELECT * FROM dictionary 
            WHERE hsk_level = ?
            ORDER BY frequency_rank ASC, id ASC
            LIMIT ?
        '''
        self.cursor.execute(sql, (level, limit))
        return self._build_entries(self.cursor.fetchall())
    
    def search_by_tocfl_level(self, level: int, limit: int = 50) -> List[DictionaryEntry]:
        """Search words by TOCFL level"""
        sql = '''
            SELECT * FROM dictionary 
            WHERE tocfl_level = ?
            ORDER BY frequency_rank ASC, id ASC
            LIMIT ?
        '''
        self.cursor.execute(sql, (level, limit))
        return self._build_entries(self.cursor.fetchall())
    
    def search_by_category(self, category: str, limit: int = 50) -> List[DictionaryEntry]:
        """Search words by category/tag"""
        sql = '''
            SELECT d.* FROM dictionary d
            JOIN tags t ON d.id = t.word_id
            WHERE t.tag LIKE ? OR t.category LIKE ?
            ORDER BY d.frequency_rank ASC, d.hsk_level ASC
            LIMIT ?
        '''
        like_query = f"%{category}%"
        self.cursor.execute(sql, (like_query, like_query, limit))
        return self._build_entries(self.cursor.fetchall())
    
    def get_word_details(self, word_id: int) -> Optional[DictionaryEntry]:
        """Get detailed information for a specific word"""
        sql = "SELECT * FROM dictionary WHERE id = ?"
        self.cursor.execute(sql, (word_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return None
        
        entries = self._build_entries([result], include_details=True)
        return entries[0] if entries else None
    
    def _build_entries(self, rows: List[sqlite3.Row], include_details: bool = False) -> List[DictionaryEntry]:
        """Build DictionaryEntry objects from database rows"""
        entries = []
        
        for row in rows:
            entry = DictionaryEntry(
                id=row['id'],
                word=row['word'],
                traditional=row['traditional'],
                simplified=row['simplified'],
                pinyin=row['pinyin'],
                zhuyin=row['zhuyin'],
                vi_meaning=row['vi_meaning'],
                en_meaning=row['en_meaning'],
                part_of_speech=row['part_of_speech'],
                hsk_level=row['hsk_level'],
                tocfl_level=row['tocfl_level'],
                frequency_rank=row['frequency_rank'],
                hanviet_reading=row['hanviet_reading']
            )
            
            if include_details:
                entry.examples = self._get_examples(row['id'])
                entry.synonyms = self._get_synonyms(row['id'])
                entry.antonyms = self._get_antonyms(row['id'])
                entry.measure_words = self._get_measure_words(row['id'])
                entry.tags = self._get_tags(row['id'])
            
            entries.append(entry)
        
        return entries
    
    def _get_examples(self, word_id: int) -> List[Dict]:
        """Get example sentences for a word"""
        sql = '''
            SELECT chinese, pinyin, vietnamese, english, source
            FROM examples WHERE word_id = ?
            ORDER BY id
        '''
        self.cursor.execute(sql, (word_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def _get_synonyms(self, word_id: int) -> List[str]:
        """Get synonyms for a word"""
        sql = "SELECT synonym FROM synonyms WHERE word_id = ?"
        self.cursor.execute(sql, (word_id,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def _get_antonyms(self, word_id: int) -> List[str]:
        """Get antonyms for a word"""
        sql = "SELECT antonym FROM antonyms WHERE word_id = ?"
        self.cursor.execute(sql, (word_id,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def _get_measure_words(self, word_id: int) -> List[str]:
        """Get measure words for a word"""
        sql = "SELECT measure_word FROM measure_words WHERE word_id = ?"
        self.cursor.execute(sql, (word_id,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def _get_tags(self, word_id: int) -> List[str]:
        """Get tags for a word"""
        sql = "SELECT tag FROM tags WHERE word_id = ?"
        self.cursor.execute(sql, (word_id,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_random_words(self, limit: int = 10, hsk_level: Optional[int] = None) -> List[DictionaryEntry]:
        """Get random words for study"""
        sql = '''
            SELECT * FROM dictionary 
            WHERE 1=1
        '''
        params = []
        
        if hsk_level:
            sql += " AND hsk_level = ?"
            params.append(hsk_level)
        
        sql += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(sql, params)
        return self._build_entries(self.cursor.fetchall())
    
    def get_statistics(self) -> Dict:
        """Get dictionary statistics"""
        stats = {}
        
        # Total words
        self.cursor.execute("SELECT COUNT(*) FROM dictionary")
        stats['total_words'] = self.cursor.fetchone()[0]
        
        # HSK distribution
        self.cursor.execute('''
            SELECT hsk_level, COUNT(*) FROM dictionary 
            WHERE hsk_level IS NOT NULL 
            GROUP BY hsk_level 
            ORDER BY hsk_level
        ''')
        stats['hsk_distribution'] = dict(self.cursor.fetchall())
        
        # TOCFL distribution
        self.cursor.execute('''
            SELECT tocfl_level, COUNT(*) FROM dictionary 
            WHERE tocfl_level IS NOT NULL 
            GROUP BY tocfl_level 
            ORDER BY tocfl_level
        ''')
        stats['tocfl_distribution'] = dict(self.cursor.fetchall())
        
        # Categories
        self.cursor.execute('''
            SELECT category, COUNT(DISTINCT word_id) FROM tags 
            WHERE category IS NOT NULL 
            GROUP BY category 
            ORDER BY COUNT(DISTINCT word_id) DESC
        ''')
        stats['categories'] = dict(self.cursor.fetchall())
        
        # Data completeness
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE pinyin IS NOT NULL")
        stats['with_pinyin'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE zhuyin IS NOT NULL")
        stats['with_zhuyin'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE hanviet_reading IS NOT NULL")
        stats['with_hanviet'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dictionary WHERE en_meaning IS NOT NULL")
        stats['with_english'] = self.cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Demo function to test the dictionary API"""
    try:
        dictionary = ChineseVietnameseDictionary()
        
        print("Chinese-Vietnamese Dictionary API Demo")
        print("="*40)
        
        # Show statistics
        stats = dictionary.get_statistics()
        print(f"Total words: {stats['total_words']}")
        print(f"HSK distribution: {stats['hsk_distribution']}")
        print(f"With Pinyin: {stats['with_pinyin']}")
        print(f"With Zhuyin: {stats['with_zhuyin']}")
        print(f"With Hanviet: {stats['with_hanviet']}")
        print()
        
        # Search examples
        test_queries = ["你好", "bạn", "水", "chào"]
        
        for query in test_queries:
            print(f"Searching for: '{query}'")
            results = dictionary.search_word(query, limit=3)
            for entry in results:
                print(f"  {entry.word} ({entry.pinyin}) - {entry.vi_meaning}")
            print()
        
        # Random words
        print("Random HSK 1 words:")
        random_words = dictionary.get_random_words(limit=5, hsk_level=1)
        for entry in random_words:
            print(f"  {entry.word} ({entry.pinyin}) - {entry.vi_meaning}")
        
        dictionary.close()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run 'python import_vietnamese_data.py' first to create the database.")

if __name__ == "__main__":
    main() 