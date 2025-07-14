#!/usr/bin/env python3
"""
Simple launcher for the Chinese-Vietnamese Dictionary
"""

import os
import sys
from pathlib import Path

def check_database():
    """Check if the dictionary database exists"""
    return Path("cedict.db").exists()

def main():
    print("=" * 60)
    print("Chinese-Vietnamese Dictionary")
    print("=" * 60)
    
    if not check_database():
        print("❌ Dictionary database not found!")
        print("\n🔧 Setting up the database...")
        
        # Run the import script
        import subprocess
        try:
            result = subprocess.run([sys.executable, "import_vietnamese_data.py"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Database setup completed successfully!")
            else:
                print(f"❌ Database setup failed: {result.stderr}")
                return
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            return
    
    print("✅ Dictionary database found!")
    
    # Get statistics
    try:
        from dictionary_api import ChineseVietnameseDictionary
        dictionary = ChineseVietnameseDictionary()
        stats = dictionary.get_statistics()
        
        print(f"\n📊 Dictionary Statistics:")
        print(f"   • Total words: {stats['total_words']:,}")
        print(f"   • With Pinyin: {stats['with_pinyin']:,}")
        print(f"   • With Zhuyin: {stats['with_zhuyin']:,}")
        print(f"   • With Hanviet: {stats['with_hanviet']:,}")
        print(f"   • HSK levels: {len(stats['hsk_distribution'])}")
        print(f"   • TOCFL levels: {len(stats['tocfl_distribution'])}")
        
        dictionary.close()
    except Exception as e:
        print(f"⚠️  Could not load statistics: {e}")
    
    print("\n🚀 Starting web interface...")
    print("📱 Open http://localhost:5000 in your browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Start the web interface
    try:
        from web_interface import app, check_database_exists
        if check_database_exists():
            app.run(debug=False, host='0.0.0.0', port=5000)
        else:
            print("❌ Failed to initialize dictionary!")
    except KeyboardInterrupt:
        print("\n\n👋 Dictionary server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")

if __name__ == "__main__":
    main() 