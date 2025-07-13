#!/usr/bin/env python3
"""
Dictionary Enhancement Setup Script
Guides users through CC-CEDICT integration and DeepSeek AI enhancement setup
"""

import os
import sys
import subprocess
import sqlite3
from typing import Optional

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_database_exists():
    """Check if the main dictionary database exists"""
    if os.path.exists("chinese_vietnamese_dict.db"):
        print("✅ Main dictionary database found")
        return True
    print("❌ Main dictionary database not found")
    print("   Please run: python create_dictionary_db.py")
    print("   Then run: python import_vietnamese_data.py")
    return False

def get_database_stats():
    """Get current database statistics"""
    try:
        conn = sqlite3.connect("chinese_vietnamese_dict.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE en_meaning IS NOT NULL AND en_meaning != ''")
        with_english = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE vi_meaning IS NOT NULL AND vi_meaning != ''")
        with_vietnamese = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE zhuyin IS NOT NULL AND zhuyin != ''")
        with_zhuyin = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'english': with_english,
            'vietnamese': with_vietnamese,
            'zhuyin': with_zhuyin
        }
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return None

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['requests', 'flask', 'sqlite3']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} missing")
    
    if missing:
        print(f"\n📦 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def check_cedict_status():
    """Check CC-CEDICT download and integration status"""
    has_raw = os.path.exists("cedict_raw.txt")
    has_db = os.path.exists("cedict.db")
    
    if has_db:
        try:
            conn = sqlite3.connect("cedict.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cedict_entries")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ CC-CEDICT database: {count:,} entries")
            return True
        except:
            print("❌ CC-CEDICT database corrupted")
            return False
    elif has_raw:
        print("⚠️  CC-CEDICT downloaded but not processed")
        return False
    else:
        print("❌ CC-CEDICT not downloaded")
        return False

def check_deepseek_api():
    """Check DeepSeek API key configuration"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        print("✅ DeepSeek API key configured")
        return True
    else:
        print("❌ DeepSeek API key not set")
        print("   Set environment variable: export DEEPSEEK_API_KEY='your_key'")
        return False

def prompt_user_choice(question: str, options: list) -> str:
    """Prompt user for choice from options"""
    print(f"\n{question}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    while True:
        try:
            choice = input("\nEnter your choice (number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔄 {description}...")
    print(f"   Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def setup_cedict():
    """Setup CC-CEDICT integration"""
    print("\n" + "="*50)
    print("CC-CEDICT INTEGRATION SETUP")
    print("="*50)
    
    if check_cedict_status():
        choice = prompt_user_choice(
            "CC-CEDICT is already available. What would you like to do?",
            ["Skip CC-CEDICT setup", "Re-download CC-CEDICT", "Integrate with existing database"]
        )
        
        if choice == "Skip CC-CEDICT setup":
            return True
        elif choice == "Re-download CC-CEDICT":
            return run_command("python download_cedict.py", "Downloading CC-CEDICT")
        else:  # Integrate
            limit = input("Enter max new entries to add (default 10000): ").strip()
            limit = limit if limit.isdigit() else "10000"
            return run_command(f"python integrate_cedict.py integrate {limit}", "Integrating CC-CEDICT")
    
    else:
        print("CC-CEDICT provides 100,000+ Chinese-English dictionary entries")
        print("This will significantly enhance your dictionary with English definitions")
        
        choice = prompt_user_choice(
            "Would you like to download and integrate CC-CEDICT?",
            ["Yes, download and integrate", "Skip CC-CEDICT"]
        )
        
        if choice == "Yes, download and integrate":
            # Download
            if not run_command("python download_cedict.py", "Downloading CC-CEDICT"):
                return False
            
            # Integrate
            limit = input("Enter max new entries to add (default 10000): ").strip()
            limit = limit if limit.isdigit() else "10000"
            return run_command(f"python integrate_cedict.py integrate {limit}", "Integrating CC-CEDICT")
        
        return True

def setup_deepseek():
    """Setup DeepSeek AI enhancement"""
    print("\n" + "="*50)
    print("DEEPSEEK AI ENHANCEMENT SETUP")
    print("="*50)
    
    if check_deepseek_api():
        choice = prompt_user_choice(
            "DeepSeek API is configured. What would you like to do?",
            ["Test AI enhancement", "Run batch enhancement", "Skip AI setup"]
        )
        
        if choice == "Test AI enhancement":
            return run_command("python deepseek_enhancer.py test", "Testing AI enhancement")
        elif choice == "Run batch enhancement":
            limit = input("Enter max entries to enhance (default 100): ").strip()
            limit = limit if limit.isdigit() else "100"
            return run_command(f"python deepseek_enhancer.py batch 20 {limit}", "Running AI enhancement")
        else:
            return True
    
    else:
        print("DeepSeek AI can automatically fill missing information:")
        print("- Generate missing pronunciations (Pinyin, Zhuyin, Hanviet)")
        print("- Create Vietnamese translations")
        print("- Add example sentences")
        print("- Provide grammar information")
        print()
        print("To use this feature, you need a DeepSeek API key from: https://platform.deepseek.com/")
        
        choice = prompt_user_choice(
            "Do you have a DeepSeek API key?",
            ["Yes, I have an API key", "No, skip AI enhancement"]
        )
        
        if choice == "Yes, I have an API key":
            api_key = input("Enter your DeepSeek API key: ").strip()
            if api_key:
                print(f"export DEEPSEEK_API_KEY='{api_key}'")
                print("Please run the above command to set your API key, then restart this script.")
                return False
            else:
                print("No API key provided, skipping AI enhancement")
                return True
        
        return True

def run_comprehensive_enhancement():
    """Run the comprehensive enhancement workflow"""
    print("\n" + "="*50)
    print("COMPREHENSIVE ENHANCEMENT WORKFLOW")
    print("="*50)
    
    print("This will run the complete enhancement process:")
    print("1. CC-CEDICT integration (if available)")
    print("2. DeepSeek AI enhancement (if configured)")
    print("3. Generate completion report")
    
    choice = prompt_user_choice(
        "Select enhancement mode:",
        ["Quick mode (1000 CC-CEDICT + 100 AI)", "Standard mode (10000 CC-CEDICT + 1000 AI)", "Custom limits", "Skip comprehensive enhancement"]
    )
    
    if choice == "Skip comprehensive enhancement":
        return True
    elif choice == "Quick mode (1000 CC-CEDICT + 100 AI)":
        return run_command("python ai_data_completion.py --quick", "Running quick enhancement")
    elif choice == "Standard mode (10000 CC-CEDICT + 1000 AI)":
        return run_command("python ai_data_completion.py", "Running standard enhancement")
    else:  # Custom
        cedict_limit = input("CC-CEDICT limit (default 10000): ").strip()
        ai_limit = input("AI enhancement limit (default 1000): ").strip()
        
        cedict_limit = cedict_limit if cedict_limit.isdigit() else "10000"
        ai_limit = ai_limit if ai_limit.isdigit() else "1000"
        
        return run_command(
            f"python ai_data_completion.py --cedict-limit {cedict_limit} --ai-limit {ai_limit}",
            "Running custom enhancement"
        )

def main():
    """Main setup function"""
    print("🚀 CHINESE-VIETNAMESE DICTIONARY ENHANCEMENT SETUP")
    print("="*60)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and run this script again")
        sys.exit(1)
    
    if not check_database_exists():
        print("\n❌ Please create the dictionary database first")
        sys.exit(1)
    
    # Show current status
    stats = get_database_stats()
    if stats:
        print(f"\n📊 Current database status:")
        print(f"   Total entries: {stats['total']:,}")
        print(f"   With English: {stats['english']:,} ({stats['english']/stats['total']*100:.1f}%)")
        print(f"   With Vietnamese: {stats['vietnamese']:,} ({stats['vietnamese']/stats['total']*100:.1f}%)")
        print(f"   With Zhuyin: {stats['zhuyin']:,} ({stats['zhuyin']/stats['total']*100:.1f}%)")
    
    # Main setup workflow
    try:
        # Setup CC-CEDICT
        if not setup_cedict():
            print("❌ CC-CEDICT setup failed")
            return
        
        # Setup DeepSeek AI
        if not setup_deepseek():
            print("❌ DeepSeek setup failed")
            return
        
        # Run comprehensive enhancement
        if not run_comprehensive_enhancement():
            print("❌ Comprehensive enhancement failed")
            return
        
        # Final status
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        final_stats = get_database_stats()
        if final_stats and stats:
            print(f"\n📈 Enhancement results:")
            print(f"   Total entries: {stats['total']:,} → {final_stats['total']:,}")
            print(f"   English coverage: {stats['english']/stats['total']*100:.1f}% → {final_stats['english']/final_stats['total']*100:.1f}%")
            print(f"   Zhuyin coverage: {stats['zhuyin']/stats['total']*100:.1f}% → {final_stats['zhuyin']/final_stats['total']*100:.1f}%")
        
        print(f"\n🌐 Start the web interface:")
        print(f"   python start_dictionary.py")
        print(f"   Then visit: http://localhost:5000")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 