#!/usr/bin/env python3
"""
CC-CEDICT Integration Script
Integrates CC-CEDICT entries with existing Chinese-Vietnamese dictionary
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CEDICTIntegrator:
    def __init__(self):
        """Initialize the CEDICT integrator"""
        self.main_db = "chinese_vietnamese_dict.db"
        self.cedict_db = "cedict.db"
        
        # Check if databases exist
        self._verify_databases()
        
        # Connect to databases
        self.main_conn = sqlite3.connect(self.main_db, check_same_thread=False)
        self.main_conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
        
        self.cedict_conn = sqlite3.connect(self.cedict_db, check_same_thread=False)
        self.cedict_conn.row_factory = sqlite3.Row
    
    def _verify_databases(self):
        """Verify that required databases exist"""
        import os
        
        if not os.path.exists(self.main_db):
            raise FileNotFoundError(f"Main dictionary database not found: {self.main_db}")
        
        if not os.path.exists(self.cedict_db):
            raise FileNotFoundError(f"CC-CEDICT database not found: {self.cedict_db}")
    
    def get_cedict_stats(self) -> Dict[str, int]:
        """Get statistics about CC-CEDICT database"""
        # Use a temporary connection without custom row factory for COUNT queries
        temp_conn = sqlite3.connect(self.cedict_db, check_same_thread=False)
        cursor = temp_conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cedict_entries")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT simplified) FROM cedict_entries")
        unique_simplified = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT traditional) FROM cedict_entries")
        unique_traditional = cursor.fetchone()[0]
        
        temp_conn.close()
        
        return {
            'total_entries': total_entries,
            'unique_simplified': unique_simplified,
            'unique_traditional': unique_traditional
        }
    
    def get_main_dict_stats(self) -> Dict[str, int]:
        """Get statistics about main dictionary"""
        # Use a temporary connection without custom row factory for COUNT queries
        temp_conn = sqlite3.connect(self.main_db, check_same_thread=False)
        cursor = temp_conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE en_meaning IS NOT NULL AND en_meaning != ''")
        with_english = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE vi_meaning IS NOT NULL AND vi_meaning != ''")
        with_vietnamese = cursor.fetchone()[0]
        
        temp_conn.close()
        
        return {
            'total_entries': total_entries,
            'with_english': with_english,
            'with_vietnamese': with_vietnamese
        }
    
    def find_matching_entries(self) -> List[Tuple[sqlite3.Row, sqlite3.Row]]:
        """Find entries that match between main dictionary and CC-CEDICT"""
        logger.info("Finding matching entries between dictionaries...")
        
        matches = []
        
        # Get all entries from main dictionary
        main_cursor = self.main_conn.cursor()
        main_cursor.execute("SELECT * FROM dictionary")
        main_entries = main_cursor.fetchall()
        
        logger.info(f"Processing {len(main_entries)} main dictionary entries...")
        
        for i, main_entry in enumerate(main_entries):
            if i % 1000 == 0:
                logger.info(f"Processed {i}/{len(main_entries)} entries...")
            
            chinese_text = main_entry['word']
            
            # Try to find matching CC-CEDICT entry
            cedict_cursor = self.cedict_conn.cursor()
            
            # First try simplified match
            cedict_cursor.execute(
                "SELECT * FROM cedict_entries WHERE simplified = ? LIMIT 1",
                (chinese_text,)
            )
            cedict_entry = cedict_cursor.fetchone()
            
            # If no simplified match, try traditional
            if not cedict_entry:
                cedict_cursor.execute(
                    "SELECT * FROM cedict_entries WHERE traditional = ? LIMIT 1",
                    (chinese_text,)
                )
                cedict_entry = cedict_cursor.fetchone()
            
            if cedict_entry:
                matches.append((main_entry, cedict_entry))
        
        logger.info(f"Found {len(matches)} matching entries")
        return matches
    
    def enhance_entry_with_cedict(self, main_entry: sqlite3.Row, cedict_entry: sqlite3.Row) -> Dict[str, str]:
        """Enhance main dictionary entry with CC-CEDICT data"""
        updates = {}
        
        # Add English meaning if missing
        if not main_entry.get('en_meaning') or main_entry.get('en_meaning', '').strip() == '':
            if cedict_entry['english']:
                updates['en_meaning'] = cedict_entry['english']
        
        # Add or improve Pinyin if missing or different
        if not main_entry['pinyin'] or main_entry['pinyin'].strip() == '':
            if cedict_entry['pinyin']:
                updates['pinyin'] = cedict_entry['pinyin']
        
        # Add traditional form if missing
        if not main_entry.get('traditional') or main_entry.get('traditional', '').strip() == '':
            if cedict_entry['traditional'] != cedict_entry['simplified']:
                updates['traditional'] = cedict_entry['traditional']
        
        # Add simplified form if missing
        if not main_entry.get('simplified') or main_entry.get('simplified', '').strip() == '':
            if cedict_entry['simplified'] != cedict_entry['traditional']:
                updates['simplified'] = cedict_entry['simplified']
        
        # Store CC-CEDICT definitions as additional information
        if cedict_entry['definitions']:
            try:
                definitions = json.loads(cedict_entry['definitions'])
                if definitions:
                    updates['cedict_definitions'] = cedict_entry['definitions']
            except (json.JSONDecodeError, TypeError):
                # If definitions is already a string, store it directly
                updates['cedict_definitions'] = cedict_entry['definitions']
        
        return updates
    
    def add_new_cedict_entries(self, limit: int = 1000) -> int:
        """Add new entries from CC-CEDICT that don't exist in main dictionary"""
        logger.info(f"Adding new entries from CC-CEDICT (limit: {limit})...")
        
        # Use a temporary connection without custom row factory for this complex query
        temp_cedict_conn = sqlite3.connect(self.cedict_db, check_same_thread=False)
        temp_main_conn = sqlite3.connect(self.main_db, check_same_thread=False)
        
        # Get existing words from main dictionary
        main_cursor = temp_main_conn.cursor()
        main_cursor.execute("SELECT DISTINCT word FROM dictionary")
        existing_words = {row[0] for row in main_cursor.fetchall()}
        
        # Get CC-CEDICT entries
        cedict_cursor = temp_cedict_conn.cursor()
        cedict_cursor.execute("""
        SELECT * FROM cedict_entries 
        ORDER BY LENGTH(simplified), simplified
        LIMIT ?
        """, (limit * 3,))  # Get more to filter out existing ones
        
        all_cedict_entries = cedict_cursor.fetchall()
        temp_cedict_conn.close()
        temp_main_conn.close()
        
        # Filter out entries that already exist
        new_entries = []
        for entry in all_cedict_entries:
            if entry[1] not in existing_words and entry[2] not in existing_words:  # simplified and traditional
                new_entries.append(entry)
                if len(new_entries) >= limit:
                    break
        
        logger.info(f"Found {len(new_entries)} new entries to add")
        
        added_count = 0
        main_cursor = self.main_conn.cursor()
        
        for entry in new_entries:
            try:
                # Prepare data for insertion (entry is a tuple from raw query)
                chinese_text = entry[1]  # simplified column
                pinyin = entry[3]  # pinyin column
                english_meaning = entry[4]  # english column
                
                # Parse definitions
                definitions = []
                try:
                    definitions = json.loads(entry[5])  # definitions column
                except (json.JSONDecodeError, TypeError):
                    definitions = [entry[4]] if entry[4] else []  # english column
                
                # Insert into main dictionary
                main_cursor.execute("""
                INSERT INTO dictionary 
                (word, pinyin, en_meaning, vi_meaning, traditional, simplified, 
                 cedict_definitions, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chinese_text,
                    pinyin,
                    english_meaning,
                    '',  # Empty Vietnamese meaning for now - can be filled by AI later
                    entry[2] if entry[2] != entry[1] else None,  # traditional if different from simplified
                    entry[1],  # simplified
                    entry[5],  # definitions
                    'CC-CEDICT',
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                added_count += 1
                
                if added_count % 100 == 0:
                    logger.info(f"Added {added_count} new entries...")
                    self.main_conn.commit()
                
            except Exception as e:
                logger.error(f"Error adding entry {entry[1]}: {e}")
                continue
        
        self.main_conn.commit()
        logger.info(f"Successfully added {added_count} new entries from CC-CEDICT")
        return added_count
    
    def update_existing_entries(self, matches: List[Tuple[sqlite3.Row, sqlite3.Row]]) -> int:
        """Update existing entries with CC-CEDICT data"""
        logger.info(f"Updating {len(matches)} existing entries with CC-CEDICT data...")
        
        updated_count = 0
        main_cursor = self.main_conn.cursor()
        
        for i, (main_entry, cedict_entry) in enumerate(matches):
            if i % 100 == 0:
                logger.info(f"Updated {i}/{len(matches)} entries...")
            
            try:
                updates = self.enhance_entry_with_cedict(main_entry, cedict_entry)
                
                if updates:
                    # Build UPDATE query
                    set_clauses = []
                    values = []
                    
                    for field, value in updates.items():
                        set_clauses.append(f"{field} = ?")
                        values.append(value)
                    
                    # Add updated timestamp
                    set_clauses.append("updated_at = ?")
                    values.append(datetime.now().isoformat())
                    
                    values.append(main_entry['id'])  # For WHERE clause
                    
                    query = f"""
                    UPDATE dictionary 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                    """
                    
                    main_cursor.execute(query, values)
                    updated_count += 1
            
            except Exception as e:
                logger.error(f"Error updating entry {main_entry.get('word', 'unknown')}: {e}")
                continue
        
        self.main_conn.commit()
        logger.info(f"Successfully updated {updated_count} entries")
        return updated_count
    
    def add_missing_database_columns(self):
        """Add missing columns to support CC-CEDICT integration"""
        logger.info("Adding missing database columns...")
        
        # Temporarily create a new connection without custom row factory for PRAGMA commands
        temp_conn = sqlite3.connect(self.main_db, check_same_thread=False)
        temp_cursor = temp_conn.cursor()
        
        # Get existing columns
        temp_cursor.execute("PRAGMA table_info(dictionary)")
        existing_columns = {row[1] for row in temp_cursor.fetchall()}
        temp_conn.close()
        
        main_cursor = self.main_conn.cursor()
        
        # Columns we need
        required_columns = {
            'traditional': 'TEXT',
            'simplified': 'TEXT', 
            'cedict_definitions': 'TEXT',
            'source': 'TEXT'
        }
        
        # Add missing columns
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                try:
                    main_cursor.execute(f"ALTER TABLE dictionary ADD COLUMN {column} {column_type}")
                    logger.info(f"Added column: {column}")
                except Exception as e:
                    logger.warning(f"Could not add column {column}: {e}")
        
        # Add indexes for new columns
        try:
            main_cursor.execute("CREATE INDEX IF NOT EXISTS idx_traditional ON dictionary(traditional)")
            main_cursor.execute("CREATE INDEX IF NOT EXISTS idx_simplified ON dictionary(simplified)")
            main_cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON dictionary(source)")
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
        
        self.main_conn.commit()
    
    def integrate_full(self, add_new_limit: int = 5000) -> Dict[str, int]:
        """Perform full integration of CC-CEDICT with main dictionary"""
        logger.info("Starting full CC-CEDICT integration...")
        
        # Add missing columns
        self.add_missing_database_columns()
        
        # Get statistics before integration
        logger.info("Statistics before integration:")
        main_stats = self.get_main_dict_stats()
        cedict_stats = self.get_cedict_stats()
        
        logger.info(f"Main dictionary: {main_stats['total_entries']:,} entries")
        logger.info(f"CC-CEDICT: {cedict_stats['total_entries']:,} entries")
        
        # Find matching entries
        matches = self.find_matching_entries()
        
        # Update existing entries
        updated_count = self.update_existing_entries(matches)
        
        # Add new entries
        added_count = self.add_new_cedict_entries(add_new_limit)
        
        # Get statistics after integration
        logger.info("Statistics after integration:")
        final_stats = self.get_main_dict_stats()
        logger.info(f"Main dictionary: {final_stats['total_entries']:,} entries")
        
        results = {
            'matched_entries': len(matches),
            'updated_entries': updated_count,
            'added_entries': added_count,
            'total_before': main_stats['total_entries'],
            'total_after': final_stats['total_entries']
        }
        
        logger.info("Integration complete!")
        logger.info(f"Results: {results}")
        
        return results
    
    def close(self):
        """Close database connections"""
        if self.main_conn:
            self.main_conn.close()
        if self.cedict_conn:
            self.cedict_conn.close()

def main():
    """Main function for CC-CEDICT integration"""
    import sys
    
    try:
        integrator = CEDICTIntegrator()
        
        if len(sys.argv) > 1:
            if sys.argv[1] == "stats":
                # Show statistics only
                print("Dictionary Statistics:")
                print("=" * 40)
                
                main_stats = integrator.get_main_dict_stats()
                print(f"Main Dictionary:")
                print(f"  Total entries: {main_stats['total_entries']:,}")
                print(f"  With English: {main_stats['with_english']:,}")
                print(f"  With Vietnamese: {main_stats['with_vietnamese']:,}")
                
                cedict_stats = integrator.get_cedict_stats()
                print(f"\nCC-CEDICT:")
                print(f"  Total entries: {cedict_stats['total_entries']:,}")
                print(f"  Unique simplified: {cedict_stats['unique_simplified']:,}")
                print(f"  Unique traditional: {cedict_stats['unique_traditional']:,}")
            
            elif sys.argv[1] == "integrate":
                # Perform full integration
                add_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
                results = integrator.integrate_full(add_limit)
                
                print("Integration Results:")
                print("=" * 40)
                for key, value in results.items():
                    print(f"{key.replace('_', ' ').title()}: {value:,}")
            
            else:
                print("Usage:")
                print("  python integrate_cedict.py stats                # Show statistics")
                print("  python integrate_cedict.py integrate [limit]    # Integrate with CC-CEDICT")
        
        else:
            print("CC-CEDICT Integration Tool")
            print("Commands:")
            print("  stats - Show database statistics")
            print("  integrate [limit] - Integrate CC-CEDICT data")
        
        integrator.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 