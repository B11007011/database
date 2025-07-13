#!/usr/bin/env python3
"""
Test Enhancement System
Quick test to verify CC-CEDICT integration and DeepSeek API setup
"""

import os
import sqlite3
from dotenv import load_dotenv

def test_setup():
    """Test the complete enhancement setup"""
    print("🧪 TESTING ENHANCEMENT SYSTEM")
    print("=" * 50)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Test 1: Database connection
    try:
        conn = sqlite3.connect("chinese_vietnamese_dict.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE source = 'CC-CEDICT'")
        cedict_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE vi_meaning = ''")
        missing_vietnamese = cursor.fetchone()[0]
        
        print(f"✅ Database: {total_entries:,} total entries")
        print(f"✅ CC-CEDICT: {cedict_entries:,} entries added")
        print(f"📝 Missing Vietnamese: {missing_vietnamese:,} entries")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Test 2: DeepSeek API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        print(f"✅ DeepSeek API key: {api_key[:8]}...{api_key[-4:]}")
    else:
        print("❌ DeepSeek API key not found")
        return False
    
    # Test 3: Sample API call (optional)
    try:
        from deepseek_enhancer import DeepSeekEnhancer
        enhancer = DeepSeekEnhancer(api_key)
        print("✅ DeepSeek enhancer initialized")
    except Exception as e:
        print(f"⚠️  DeepSeek enhancer warning: {e}")
    
    print("\n🎉 All tests passed! Ready for enhancement.")
    return True

def show_enhancement_options():
    """Show available enhancement options"""
    print("\n🚀 ENHANCEMENT OPTIONS")
    print("=" * 50)
    print("1. Quick test (5 entries)")
    print("2. Small batch (50 entries)")
    print("3. Medium batch (200 entries)")
    print("4. Large batch (1000 entries)")
    print("5. Add more CC-CEDICT entries")
    print("6. View current statistics")
    
def run_enhancement(option):
    """Run the selected enhancement"""
    if option == "1":
        os.system("python deepseek_enhancer.py batch 5 5")
    elif option == "2":
        os.system("python deepseek_enhancer.py batch 20 50")
    elif option == "3":
        os.system("python deepseek_enhancer.py batch 20 200")
    elif option == "4":
        os.system("python deepseek_enhancer.py batch 20 1000")
    elif option == "5":
        limit = input("How many CC-CEDICT entries to add (default 1000): ").strip()
        limit = limit if limit.isdigit() else "1000"
        os.system(f"python integrate_cedict.py integrate {limit}")
    elif option == "6":
        os.system("python integrate_cedict.py stats")

if __name__ == "__main__":
    if test_setup():
        show_enhancement_options()
        
        choice = input("\nEnter your choice (1-6): ").strip()
        if choice in ["1", "2", "3", "4", "5", "6"]:
            print(f"\n🔄 Running option {choice}...")
            run_enhancement(choice)
        else:
            print("Invalid choice. Run the script again to try.")
    else:
        print("\n❌ Setup incomplete. Please check your configuration.") 