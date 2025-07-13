#!/usr/bin/env python3
"""
AI-Powered Data Completion Workflow
Combines CC-CEDICT integration with DeepSeek API enhancement for comprehensive dictionary completion
"""

import os
import sys
import sqlite3
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our custom modules
from download_cedict import main as download_cedict_main
from integrate_cedict import CEDICTIntegrator
from deepseek_enhancer import DeepSeekEnhancer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataCompletion:
    def __init__(self, deepseek_api_key: str = None):
        """Initialize the comprehensive data completion system"""
        self.deepseek_api_key = deepseek_api_key or os.getenv('DEEPSEEK_API_KEY')
        
        # Initialize database connection
        self.conn = sqlite3.connect("chinese_vietnamese_dict.db", check_same_thread=False)
        self.conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
        
        # Initialize components
        self.cedict_integrator = None
        self.deepseek_enhancer = None
        
        # Statistics tracking
        self.stats = {
            'initial_entries': 0,
            'cedict_matches': 0,
            'cedict_new_entries': 0,
            'ai_enhancements': 0,
            'final_entries': 0,
            'completion_percentage': 0
        }
    
    def get_initial_statistics(self) -> Dict[str, int]:
        """Get initial database statistics"""
        cursor = self.conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        total = cursor.fetchone()[0]
        
        # Entries with various fields
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE en_meaning IS NOT NULL AND en_meaning != ''")
        with_english = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE vi_meaning IS NOT NULL AND vi_meaning != ''")
        with_vietnamese = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE pinyin IS NOT NULL AND pinyin != ''")
        with_pinyin = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE zhuyin IS NOT NULL AND zhuyin != ''")
        with_zhuyin = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary WHERE hanviet_reading IS NOT NULL AND hanviet_reading != ''")
        with_hanviet = cursor.fetchone()[0]
        
        # Calculate completion rates
        english_rate = (with_english / total * 100) if total > 0 else 0
        vietnamese_rate = (with_vietnamese / total * 100) if total > 0 else 0
        pinyin_rate = (with_pinyin / total * 100) if total > 0 else 0
        zhuyin_rate = (with_zhuyin / total * 100) if total > 0 else 0
        hanviet_rate = (with_hanviet / total * 100) if total > 0 else 0
        
        return {
            'total_entries': total,
            'with_english': with_english,
            'with_vietnamese': with_vietnamese,
            'with_pinyin': with_pinyin,
            'with_zhuyin': with_zhuyin,
            'with_hanviet': with_hanviet,
            'english_rate': english_rate,
            'vietnamese_rate': vietnamese_rate,
            'pinyin_rate': pinyin_rate,
            'zhuyin_rate': zhuyin_rate,
            'hanviet_rate': hanviet_rate
        }
    
    def step1_download_cedict(self) -> bool:
        """Step 1: Download CC-CEDICT if not already present"""
        logger.info("Step 1: Downloading CC-CEDICT...")
        
        if os.path.exists("cedict.db"):
            logger.info("CC-CEDICT database already exists, skipping download")
            return True
        
        try:
            # Download and process CC-CEDICT
            download_cedict_main()
            return os.path.exists("cedict.db")
        except Exception as e:
            logger.error(f"Failed to download CC-CEDICT: {e}")
            return False
    
    def step2_integrate_cedict(self, add_new_limit: int = 10000) -> Dict[str, int]:
        """Step 2: Integrate CC-CEDICT with existing dictionary"""
        logger.info("Step 2: Integrating CC-CEDICT...")
        
        try:
            self.cedict_integrator = CEDICTIntegrator()
            results = self.cedict_integrator.integrate_full(add_new_limit)
            
            self.stats['cedict_matches'] = results['matched_entries']
            self.stats['cedict_new_entries'] = results['added_entries']
            
            logger.info(f"CC-CEDICT integration complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to integrate CC-CEDICT: {e}")
            return {}
    
    def step3_ai_enhancement(self, max_entries: int = 1000) -> int:
        """Step 3: Use DeepSeek AI to enhance missing information"""
        logger.info("Step 3: AI-powered enhancement...")
        
        if not self.deepseek_api_key:
            logger.warning("No DeepSeek API key provided, skipping AI enhancement")
            return 0
        
        try:
            self.deepseek_enhancer = DeepSeekEnhancer(self.deepseek_api_key)
            enhanced_count = self.deepseek_enhancer.enhance_batch(
                batch_size=20,  # Smaller batches for API rate limiting
                max_entries=max_entries
            )
            
            self.stats['ai_enhancements'] = enhanced_count
            logger.info(f"AI enhancement complete: {enhanced_count} entries enhanced")
            return enhanced_count
            
        except Exception as e:
            logger.error(f"Failed to perform AI enhancement: {e}")
            return 0
    
    def step4_quality_check(self) -> Dict[str, int]:
        """Step 4: Perform quality checks and generate report"""
        logger.info("Step 4: Quality check and reporting...")
        
        cursor = self.conn.cursor()
        
        # Check for entries with missing critical information
        cursor.execute("""
        SELECT COUNT(*) FROM dictionary 
        WHERE (pinyin IS NULL OR pinyin = '') 
           OR (en_meaning IS NULL OR en_meaning = '')
        """)
        missing_critical = cursor.fetchone()[0]
        
        # Check for entries with no pronunciation at all
        cursor.execute("""
        SELECT COUNT(*) FROM dictionary 
        WHERE (pinyin IS NULL OR pinyin = '') 
          AND (zhuyin IS NULL OR zhuyin = '')
        """)
        no_pronunciation = cursor.fetchone()[0]
        
        # Check for entries with no translation
        cursor.execute("""
        SELECT COUNT(*) FROM dictionary 
        WHERE (en_meaning IS NULL OR en_meaning = '') 
          AND (vi_meaning IS NULL OR vi_meaning = '')
        """)
        no_translation = cursor.fetchone()[0]
        
        # Count entries by source
        cursor.execute("SELECT source, COUNT(*) FROM dictionary WHERE source IS NOT NULL GROUP BY source")
        source_counts = dict(cursor.fetchall())
        
        return {
            'missing_critical': missing_critical,
            'no_pronunciation': no_pronunciation,
            'no_translation': no_translation,
            'source_counts': source_counts
        }
    
    def generate_completion_report(self, initial_stats: Dict, final_stats: Dict, quality_check: Dict) -> str:
        """Generate a comprehensive completion report"""
        report = []
        report.append("=" * 60)
        report.append("CHINESE-VIETNAMESE DICTIONARY COMPLETION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Overview
        report.append("OVERVIEW:")
        report.append(f"Initial entries: {initial_stats['total_entries']:,}")
        report.append(f"Final entries: {final_stats['total_entries']:,}")
        report.append(f"New entries added: {final_stats['total_entries'] - initial_stats['total_entries']:,}")
        report.append("")
        
        # CC-CEDICT Integration
        report.append("CC-CEDICT INTEGRATION:")
        report.append(f"Matched entries updated: {self.stats['cedict_matches']:,}")
        report.append(f"New entries from CC-CEDICT: {self.stats['cedict_new_entries']:,}")
        report.append("")
        
        # AI Enhancement
        report.append("AI ENHANCEMENT:")
        report.append(f"Entries enhanced by AI: {self.stats['ai_enhancements']:,}")
        report.append("")
        
        # Completion Rates
        report.append("COMPLETION RATES:")
        report.append("                    Before    After    Improvement")
        report.append(f"English Meaning:    {initial_stats['english_rate']:5.1f}%   {final_stats['english_rate']:5.1f}%   {final_stats['english_rate'] - initial_stats['english_rate']:+5.1f}%")
        report.append(f"Vietnamese Meaning: {initial_stats['vietnamese_rate']:5.1f}%   {final_stats['vietnamese_rate']:5.1f}%   {final_stats['vietnamese_rate'] - initial_stats['vietnamese_rate']:+5.1f}%")
        report.append(f"Pinyin:             {initial_stats['pinyin_rate']:5.1f}%   {final_stats['pinyin_rate']:5.1f}%   {final_stats['pinyin_rate'] - initial_stats['pinyin_rate']:+5.1f}%")
        report.append(f"Zhuyin:             {initial_stats['zhuyin_rate']:5.1f}%   {final_stats['zhuyin_rate']:5.1f}%   {final_stats['zhuyin_rate'] - initial_stats['zhuyin_rate']:+5.1f}%")
        report.append(f"Hanviet:            {initial_stats['hanviet_rate']:5.1f}%   {final_stats['hanviet_rate']:5.1f}%   {final_stats['hanviet_rate'] - initial_stats['hanviet_rate']:+5.1f}%")
        report.append("")
        
        # Quality Check
        report.append("QUALITY CHECK:")
        report.append(f"Entries missing critical info: {quality_check['missing_critical']:,}")
        report.append(f"Entries with no pronunciation: {quality_check['no_pronunciation']:,}")
        report.append(f"Entries with no translation: {quality_check['no_translation']:,}")
        report.append("")
        
        # Sources
        if quality_check['source_counts']:
            report.append("ENTRIES BY SOURCE:")
            for source, count in quality_check['source_counts'].items():
                report.append(f"  {source}: {count:,}")
        report.append("")
        
        # Overall completion score
        avg_completion = (
            final_stats['english_rate'] + 
            final_stats['vietnamese_rate'] + 
            final_stats['pinyin_rate'] + 
            final_stats['zhuyin_rate'] + 
            final_stats['hanviet_rate']
        ) / 5
        
        report.append(f"OVERALL COMPLETION SCORE: {avg_completion:.1f}%")
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run_complete_workflow(self, 
                             cedict_limit: int = 10000, 
                             ai_limit: int = 1000,
                             save_report: bool = True) -> Dict:
        """Run the complete data completion workflow"""
        logger.info("Starting comprehensive data completion workflow...")
        start_time = time.time()
        
        # Get initial statistics
        initial_stats = self.get_initial_statistics()
        self.stats['initial_entries'] = initial_stats['total_entries']
        
        logger.info(f"Initial state: {initial_stats['total_entries']:,} entries")
        logger.info(f"Initial completion rates - English: {initial_stats['english_rate']:.1f}%, Vietnamese: {initial_stats['vietnamese_rate']:.1f}%")
        
        # Step 1: Download CC-CEDICT
        if not self.step1_download_cedict():
            logger.error("Failed to download CC-CEDICT, continuing without it")
        
        # Step 2: Integrate CC-CEDICT
        cedict_results = self.step2_integrate_cedict(cedict_limit)
        
        # Step 3: AI Enhancement
        ai_enhanced = self.step3_ai_enhancement(ai_limit)
        
        # Step 4: Quality check
        quality_check = self.step4_quality_check()
        
        # Get final statistics
        final_stats = self.get_initial_statistics()
        self.stats['final_entries'] = final_stats['total_entries']
        
        # Calculate overall improvement
        avg_initial = (initial_stats['english_rate'] + initial_stats['vietnamese_rate'] + 
                      initial_stats['pinyin_rate'] + initial_stats['zhuyin_rate'] + 
                      initial_stats['hanviet_rate']) / 5
        avg_final = (final_stats['english_rate'] + final_stats['vietnamese_rate'] + 
                    final_stats['pinyin_rate'] + final_stats['zhuyin_rate'] + 
                    final_stats['hanviet_rate']) / 5
        
        self.stats['completion_percentage'] = avg_final
        
        # Generate report
        report = self.generate_completion_report(initial_stats, final_stats, quality_check)
        
        # Save report
        if save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"completion_report_{timestamp}.txt"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {report_filename}")
        
        # Print report
        print(report)
        
        # Calculate total time
        total_time = time.time() - start_time
        logger.info(f"Workflow completed in {total_time:.1f} seconds")
        
        return {
            'initial_stats': initial_stats,
            'final_stats': final_stats,
            'quality_check': quality_check,
            'cedict_results': cedict_results,
            'ai_enhanced': ai_enhanced,
            'improvement': avg_final - avg_initial,
            'total_time': total_time
        }
    
    def close(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()
        if self.cedict_integrator:
            self.cedict_integrator.close()
        if self.deepseek_enhancer:
            self.deepseek_enhancer.close()

def main():
    """Main function for comprehensive data completion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Chinese-Vietnamese Dictionary Data Completion")
    parser.add_argument("--cedict-limit", type=int, default=10000, 
                       help="Maximum new entries to add from CC-CEDICT (default: 10000)")
    parser.add_argument("--ai-limit", type=int, default=1000,
                       help="Maximum entries to enhance with AI (default: 1000)")
    parser.add_argument("--api-key", type=str,
                       help="DeepSeek API key (or set DEEPSEEK_API_KEY env var)")
    parser.add_argument("--no-report", action="store_true",
                       help="Don't save completion report to file")
    parser.add_argument("--quick", action="store_true",
                       help="Quick mode with reduced limits")
    
    args = parser.parse_args()
    
    # Quick mode adjustments
    if args.quick:
        args.cedict_limit = 1000
        args.ai_limit = 100
        print("Quick mode enabled - reduced limits for faster completion")
    
    # Check for API key
    api_key = args.api_key or os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("Warning: No DeepSeek API key provided. AI enhancement will be skipped.")
        print("To enable AI enhancement, set DEEPSEEK_API_KEY environment variable or use --api-key")
        print()
    
    try:
        # Initialize and run workflow
        completion_system = ComprehensiveDataCompletion(api_key)
        
        print("Starting comprehensive dictionary data completion...")
        print(f"CC-CEDICT limit: {args.cedict_limit:,}")
        print(f"AI enhancement limit: {args.ai_limit:,}")
        print()
        
        results = completion_system.run_complete_workflow(
            cedict_limit=args.cedict_limit,
            ai_limit=args.ai_limit,
            save_report=not args.no_report
        )
        
        print(f"\nWorkflow completed successfully!")
        print(f"Overall improvement: {results['improvement']:.1f} percentage points")
        print(f"Total time: {results['total_time']:.1f} seconds")
        
        completion_system.close()
        
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 