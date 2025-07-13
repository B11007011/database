#!/usr/bin/env python3
"""
DeepSeek API Enhancer for Chinese-Vietnamese Dictionary
Uses DeepSeek API to fill in missing information in dictionary entries
"""

import os
import sqlite3
import json
import requests
import time
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepSeekEnhancer:
    def __init__(self, api_key: str = None):
        """Initialize DeepSeek API enhancer"""
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        
        # Connect to database
        self.conn = sqlite3.connect("chinese_vietnamese_dict.db", check_same_thread=False)
        self.conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _call_deepseek_api(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Call DeepSeek API with the given prompt"""
        self._rate_limit()
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Chinese language expert specializing in Chinese-Vietnamese dictionaries. Provide accurate, helpful information about Chinese words including pronunciations, meanings, examples, and cultural context."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Unexpected API response format: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling API: {e}")
            return None
    
    def enhance_missing_pronunciation(self, chinese_text: str) -> Dict[str, str]:
        """Generate missing pronunciation data using DeepSeek API"""
        prompt = f"""
For the Chinese word/phrase "{chinese_text}", please provide:

1. Pinyin pronunciation with tone marks (e.g., nǐ hǎo)
2. Pinyin with numbers (e.g., ni3 hao3)  
3. Zhuyin/Bopomofo notation (e.g., ㄋㄧˇ ㄏㄠˇ)
4. Sino-Vietnamese reading (Han-Viet) if applicable

Please format your response as JSON:
{{
    "pinyin_tones": "pinyin with tone marks",
    "pinyin_numbers": "pinyin with numbers", 
    "zhuyin": "zhuyin notation",
    "hanviet": "sino-vietnamese reading"
}}

Only include fields where you are confident about the pronunciation. If unsure about any field, omit it from the JSON response.
"""
        
        response = self._call_deepseek_api(prompt)
        if not response:
            return {}
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse pronunciation JSON for '{chinese_text}': {e}")
        
        return {}
    
    def enhance_missing_vietnamese(self, chinese_text: str, english_meaning: str = "") -> str:
        """Generate Vietnamese translation using DeepSeek API"""
        context = f" (English meaning: {english_meaning})" if english_meaning else ""
        
        prompt = f"""
Please provide an accurate Vietnamese translation for the Chinese word/phrase "{chinese_text}"{context}.

Consider:
1. The most common and appropriate Vietnamese equivalent
2. Cultural context and usage
3. Multiple meanings if the word has them

Provide only the Vietnamese translation(s), separated by semicolons if multiple meanings exist.
Do not include explanations or additional text.

Example format: "xin chào; chào hỏi"
"""
        
        response = self._call_deepseek_api(prompt, max_tokens=200)
        return response.strip() if response else ""
    
    def enhance_missing_examples(self, chinese_text: str, vietnamese_meaning: str = "") -> List[Dict[str, str]]:
        """Generate example sentences using DeepSeek API"""
        context = f" (Vietnamese meaning: {vietnamese_meaning})" if vietnamese_meaning else ""
        
        prompt = f"""
Please provide 2-3 example sentences using the Chinese word/phrase "{chinese_text}"{context}.

For each example, provide:
1. Chinese sentence
2. Pinyin with tone marks
3. Vietnamese translation
4. English translation

Format as JSON array:
[
    {{
        "chinese": "Chinese sentence",
        "pinyin": "pinyin with tones",
        "vietnamese": "Vietnamese translation", 
        "english": "English translation"
    }}
]

Keep sentences practical and commonly used. Ensure translations are accurate.
"""
        
        response = self._call_deepseek_api(prompt, max_tokens=800)
        if not response:
            return []
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                examples = json.loads(json_str)
                return examples if isinstance(examples, list) else []
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse examples JSON for '{chinese_text}': {e}")
        
        return []
    
    def enhance_missing_grammar_info(self, chinese_text: str) -> Dict[str, str]:
        """Generate grammar and usage information using DeepSeek API"""
        prompt = f"""
For the Chinese word/phrase "{chinese_text}", please provide grammatical and usage information:

1. Part of speech (noun, verb, adjective, etc.)
2. Usage notes or grammar patterns
3. Common collocations or phrases it appears in
4. Formality level (formal, informal, neutral)

Format as JSON:
{{
    "part_of_speech": "grammatical category",
    "usage_notes": "how it's typically used",
    "collocations": "common word combinations",
    "formality": "formal/informal/neutral"
}}

Only include fields where you have reliable information.
"""
        
        response = self._call_deepseek_api(prompt)
        if not response:
            return {}
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse grammar JSON for '{chinese_text}': {e}")
        
        return {}
    
    def find_entries_needing_enhancement(self, limit: int = 100) -> List[Dict]:
        """Find dictionary entries that need enhancement"""
        cursor = self.conn.cursor()
        
        # Find entries missing key information
        query = """
        SELECT * FROM dictionary 
        WHERE (zhuyin IS NULL OR zhuyin = '') 
           OR (vi_meaning IS NULL OR vi_meaning = '')
           OR (hanviet_reading IS NULL OR hanviet_reading = '')
        ORDER BY frequency_rank DESC, id ASC
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    
    def enhance_entry(self, entry: Dict) -> bool:
        """Enhance a single dictionary entry"""
        chinese_text = entry['word']
        logger.info(f"Enhancing entry: {chinese_text}")
        
        updates = {}
        
        # Enhance pronunciation if missing
        if not entry['zhuyin'] or not entry['hanviet_reading']:
            pronunciation_data = self.enhance_missing_pronunciation(chinese_text)
            if pronunciation_data.get('zhuyin'):
                updates['zhuyin'] = pronunciation_data['zhuyin']
            if pronunciation_data.get('hanviet'):
                updates['hanviet_reading'] = pronunciation_data['hanviet']
            if pronunciation_data.get('pinyin_tones') and not entry['pinyin']:
                updates['pinyin'] = pronunciation_data['pinyin_tones']
        
        # Enhance Vietnamese meaning if missing
        if not entry['vi_meaning']:
            vietnamese_meaning = self.enhance_missing_vietnamese(
                chinese_text, 
                entry.get('en_meaning', '')
            )
            if vietnamese_meaning:
                updates['vi_meaning'] = vietnamese_meaning
        
        # Add example sentences if none exist
        if not entry.get('examples'):
            examples = self.enhance_missing_examples(
                chinese_text,
                updates.get('vi_meaning', entry.get('vi_meaning', ''))
            )
            if examples:
                updates['examples'] = json.dumps(examples, ensure_ascii=False)
        
        # Add grammar information if missing
        if not entry.get('grammar_info'):
            grammar_info = self.enhance_missing_grammar_info(chinese_text)
            if grammar_info:
                updates['grammar_info'] = json.dumps(grammar_info, ensure_ascii=False)
        
        # Update database if we have enhancements
        if updates:
            return self._update_database_entry(entry['id'], updates)
        
        return False
    
    def _update_database_entry(self, entry_id: int, updates: Dict[str, str]) -> bool:
        """Update database entry with enhanced information"""
        try:
            cursor = self.conn.cursor()
            
            # Build UPDATE query
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                set_clauses.append(f"{field} = ?")
                values.append(value)
            
            # Add updated timestamp
            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            
            values.append(entry_id)  # For WHERE clause
            
            query = f"""
            UPDATE dictionary 
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            cursor.execute(query, values)
            self.conn.commit()
            
            logger.info(f"Updated entry {entry_id} with fields: {list(updates.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update entry {entry_id}: {e}")
            return False
    
    def enhance_batch(self, batch_size: int = 50, max_entries: int = 500):
        """Enhance multiple entries in batches"""
        logger.info(f"Starting batch enhancement (batch_size={batch_size}, max_entries={max_entries})")
        
        enhanced_count = 0
        total_processed = 0
        
        while total_processed < max_entries:
            # Get next batch of entries
            entries = self.find_entries_needing_enhancement(batch_size)
            
            if not entries:
                logger.info("No more entries need enhancement")
                break
            
            logger.info(f"Processing batch of {len(entries)} entries...")
            
            for entry in entries:
                if total_processed >= max_entries:
                    break
                
                try:
                    if self.enhance_entry(entry):
                        enhanced_count += 1
                    
                    total_processed += 1
                    
                    # Progress update
                    if total_processed % 10 == 0:
                        logger.info(f"Processed {total_processed}/{max_entries} entries, enhanced {enhanced_count}")
                
                except Exception as e:
                    logger.error(f"Error enhancing entry {entry.get('word', 'unknown')}: {e}")
                    total_processed += 1
                    continue
        
        logger.info(f"Batch enhancement complete. Processed: {total_processed}, Enhanced: {enhanced_count}")
        return enhanced_count
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main function for testing the enhancer"""
    import sys
    
    # Check for API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set")
        print("Please set your DeepSeek API key:")
        print("export DEEPSEEK_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    try:
        enhancer = DeepSeekEnhancer(api_key)
        
        # Get command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "test":
                # Test mode - enhance just a few entries
                print("Testing DeepSeek enhancer...")
                enhanced = enhancer.enhance_batch(batch_size=5, max_entries=5)
                print(f"Test complete. Enhanced {enhanced} entries.")
            
            elif sys.argv[1] == "batch":
                # Batch mode - enhance many entries
                batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
                max_entries = int(sys.argv[3]) if len(sys.argv) > 3 else 100
                
                print(f"Starting batch enhancement (batch_size={batch_size}, max_entries={max_entries})")
                enhanced = enhancer.enhance_batch(batch_size, max_entries)
                print(f"Batch enhancement complete. Enhanced {enhanced} entries.")
            
            else:
                print("Usage:")
                print("  python deepseek_enhancer.py test          # Test with 5 entries")
                print("  python deepseek_enhancer.py batch [size] [max]  # Batch enhancement")
        
        else:
            # Interactive mode
            print("DeepSeek Dictionary Enhancer")
            print("Commands:")
            print("  test - Test with a few entries")
            print("  batch [size] [max] - Batch enhancement")
            
        enhancer.close()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 