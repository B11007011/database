# Chinese-Vietnamese Dictionary System

A comprehensive Chinese-Vietnamese dictionary system with 44,000+ entries, featuring multiple data sources, AI-powered enhancements, and a modern web interface.

## 🌟 Features

### Core Dictionary
- **44,142 Vietnamese vocabulary entries** from 214 specialized JSON files
- **HSK levels 1-7** (11,581 words) and **TOCFL levels 1-6** (7,363 words)
- **100% Pinyin/English coverage**, 7% Zhuyin/Hanviet coverage
- Specialized vocabularies: business, medical, technology, culture, and more

### Data Sources Integration
- **CC-CEDICT Integration**: 100,000+ Chinese-English entries
- **Existing Zhuyin Database**: 11,586 pronunciation entries
- **Hanviet Database**: 11,776 Sino-Vietnamese readings
- **Vietnamese Vocabulary**: 214 specialized topic files

### AI-Powered Enhancement
- **DeepSeek API Integration**: Automatically fills missing information
- **Smart Pronunciation Generation**: Pinyin, Zhuyin, and Hanviet
- **Vietnamese Translation Enhancement**: AI-generated translations
- **Example Sentences**: Contextual usage examples
- **Grammar Information**: Part of speech and usage patterns

### Web Interface
- **Modern Bootstrap UI**: Responsive design for all devices
- **Advanced Search**: Filter by levels, categories, and pronunciation
- **Random Study Tool**: Vocabulary practice and learning
- **Detailed Word Pages**: Complete information with examples
- **REST API**: Programmatic access to dictionary data

### Search & Browse
- Search by Chinese characters, Vietnamese meaning, or Pinyin
- Filter by HSK/TOCFL levels and specialized categories
- Browse by frequency, alphabetical order, or learning level
- Full-text search across all fields

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite3
- DeepSeek API key (optional, for AI enhancements)

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd chinese-vietnamese-dictionary
pip install -r requirements.txt
```

2. **Create the dictionary database**:
```bash
python create_dictionary_db.py
```

3. **Import Vietnamese vocabulary data**:
```bash
python import_vietnamese_data.py
```

4. **Download and integrate CC-CEDICT** (optional):
```bash
python download_cedict.py
python integrate_cedict.py integrate 10000
```

5. **Set up AI enhancement** (optional):
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
python deepseek_enhancer.py test
```

6. **Run comprehensive data completion**:
```bash
python ai_data_completion.py --cedict-limit 10000 --ai-limit 1000
```

7. **Start the web server**:
```bash
python start_dictionary.py
```

Visit `http://localhost:5000` to access the dictionary.

## 📚 Data Sources

### Vietnamese Vocabulary (214 files)
- **HSK Levels**: Complete vocabulary for HSK 1-7
- **TOCFL Levels**: Traditional Chinese proficiency levels 1-6
- **Specialized Topics**: 
  - Business & Economics (accounting, trading, marketing)
  - Medical & Health (traditional medicine, modern healthcare)
  - Technology & IT (computers, software, internet)
  - Culture & Arts (music, movies, literature)
  - Daily Life (food, clothing, transportation)
  - And 180+ more specialized categories

### CC-CEDICT Integration
- **100,000+ entries** from the community-maintained CC-CEDICT
- **Traditional and Simplified** Chinese characters
- **Pinyin pronunciations** with tone marks
- **English definitions** with multiple meanings
- **Automatic matching** with existing Vietnamese entries

### Pronunciation Databases
- **Zhuyin Database**: 11,586 Bopomofo pronunciation entries
- **Hanviet Database**: 11,776 Sino-Vietnamese readings
- **Integrated seamlessly** with Vietnamese vocabulary

## 🤖 AI Enhancement

The system uses DeepSeek API to intelligently fill missing information:

### Pronunciation Enhancement
```python
# Automatically generates missing pronunciations
python deepseek_enhancer.py batch 50 500
```

### Translation Enhancement
- Vietnamese translations for Chinese entries
- Context-aware meaning generation
- Cultural and usage considerations

### Example Generation
- Practical usage examples in Chinese
- Vietnamese and English translations
- Contextual sentences for learning

### Grammar Information
- Part of speech identification
- Usage patterns and collocations
- Formality levels and contexts

## 🔧 Advanced Usage

### Complete Data Enhancement Workflow
```bash
# Run comprehensive enhancement with custom limits
python ai_data_completion.py --cedict-limit 15000 --ai-limit 2000

# Quick mode for testing
python ai_data_completion.py --quick

# Without AI enhancement
python ai_data_completion.py --ai-limit 0
```

### Individual Components
```bash
# Download CC-CEDICT only
python download_cedict.py

# Check integration statistics
python integrate_cedict.py stats

# Test AI enhancement
python deepseek_enhancer.py test

# Batch AI enhancement
python deepseek_enhancer.py batch 20 100
```

### API Usage
```python
import requests

# Search for words
response = requests.get('http://localhost:5000/api/search', 
                       params={'q': '你好', 'limit': 10})

# Get word details
response = requests.get('http://localhost:5000/api/word/123')

# Random words for study
response = requests.get('http://localhost:5000/api/random', 
                       params={'count': 5, 'level': 'HSK1'})
```

## 📊 Database Schema

### Main Dictionary Table
- **chinese**: Chinese characters (primary key)
- **pinyin**: Romanized pronunciation
- **vietnamese_meaning**: Vietnamese translation
- **english_meaning**: English translation
- **zhuyin**: Bopomofo notation
- **hanviet**: Sino-Vietnamese reading
- **traditional**: Traditional character form
- **simplified**: Simplified character form
- **hsk_level**: HSK difficulty level
- **tocfl_level**: TOCFL difficulty level
- **frequency**: Usage frequency ranking
- **examples**: JSON array of example sentences
- **grammar_info**: Part of speech and usage
- **source**: Data source identifier

### Supporting Tables
- **examples**: Example sentences with translations
- **synonyms**: Related words and synonyms
- **measure_words**: Chinese measure word usage
- **tags**: Categorical tags and topics

## 🌐 Web Interface

### Search Features
- **Multi-field search**: Chinese, Vietnamese, Pinyin, English
- **Advanced filters**: Level, category, source, completion status
- **Smart suggestions**: Auto-complete and related terms
- **Export options**: CSV, JSON data export

### Study Tools
- **Random vocabulary**: Spaced repetition learning
- **Level-based practice**: HSK/TOCFL focused study
- **Category exploration**: Topic-based vocabulary
- **Progress tracking**: Learning statistics

### Admin Features
- **Data completion status**: Real-time completion rates
- **Source statistics**: Entries by data source
- **Quality metrics**: Missing information tracking
- **Enhancement logs**: AI improvement history

## 📈 Statistics

### Current Database Status
- **Total Entries**: 44,142+ words and phrases
- **Vietnamese Coverage**: 100% (44,142 entries)
- **English Coverage**: 100% (44,142 entries)  
- **Pinyin Coverage**: 100% (44,142 entries)
- **Zhuyin Coverage**: 7% (3,200+ entries)
- **Hanviet Coverage**: 7% (3,200+ entries)

### Learning Levels
- **HSK 1-7**: 11,581 entries (26.2%)
- **TOCFL 1-6**: 7,363 entries (16.7%)
- **Specialized Topics**: 25,198 entries (57.1%)

### Data Sources
- **Vietnamese JSON Files**: 44,142 entries
- **CC-CEDICT**: 100,000+ additional entries (optional)
- **Zhuyin Database**: 11,586 pronunciations
- **Hanviet Database**: 11,776 readings
- **AI Enhancement**: Variable based on usage

## 🔧 Configuration

### Environment Variables
```bash
# Required for AI enhancement
export DEEPSEEK_API_KEY="your_api_key_here"

# Optional database configuration
export DATABASE_PATH="custom_dict.db"
export WEB_PORT="8080"
export DEBUG_MODE="true"
```

### API Rate Limiting
- **DeepSeek API**: 1 request per second (configurable)
- **Batch processing**: 20 entries per batch
- **Error handling**: Automatic retry with exponential backoff

## 🤝 Contributing

### Data Contributions
- Add new Vietnamese vocabulary files to `notebooks/note/`
- Follow the JSON format of existing files
- Include metadata: HSK/TOCFL levels, categories, sources

### Code Contributions
- Follow Python PEP 8 style guidelines
- Add unit tests for new features
- Update documentation for API changes
- Test with sample data before submitting

### Enhancement Suggestions
- Report missing pronunciations or translations
- Suggest new specialized vocabulary categories
- Propose UI/UX improvements
- Share AI prompt optimizations

## 📄 License

This project is open source and available under the MIT License.

### Data Sources Licenses
- **CC-CEDICT**: Creative Commons Attribution-Share Alike 3.0
- **Vietnamese Vocabulary**: Various educational and reference sources
- **Zhuyin/Hanviet Databases**: Academic and reference materials

## 🙏 Acknowledgments

- **CC-CEDICT Project**: Community-maintained Chinese-English dictionary
- **MDBG**: CC-CEDICT hosting and maintenance
- **DeepSeek**: AI-powered language enhancement
- **Vietnamese Language Community**: Vocabulary compilation and verification
- **HSK/TOCFL Organizations**: Standardized learning levels

## 📞 Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the API documentation at `/api/docs`
- Join the community discussions

---

**Built with ❤️ for Chinese language learners and Vietnamese speakers** 