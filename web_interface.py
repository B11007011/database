#!/usr/bin/env python3
"""
Simple Flask web interface for the Chinese-Vietnamese Dictionary
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, g
from dictionary_api import ChineseVietnameseDictionary
import json
from pathlib import Path

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Support Unicode characters

def get_dictionary():
    """Get dictionary instance for current request"""
    if 'dictionary' not in g:
        try:
            g.dictionary = ChineseVietnameseDictionary()
        except FileNotFoundError:
            g.dictionary = None
    return g.dictionary

@app.teardown_appcontext
def close_dictionary(error):
    """Close dictionary connection after request"""
    dictionary = g.pop('dictionary', None)
    if dictionary is not None:
        dictionary.close()

def check_database_exists():
    """Check if database file exists"""
    return Path("cedict.db").exists()

@app.route('/')
def index():
    """Main page"""
    if not check_database_exists():
        return render_template('setup.html')
    
    dictionary = get_dictionary()
    if not dictionary:
        return render_template('setup.html')
    
    stats = dictionary.get_statistics()
    return render_template('index.html', stats=stats)

@app.route('/search')
def search():
    """Search page"""
    if not check_database_exists():
        return redirect(url_for('index'))
    
    dictionary = get_dictionary()
    if not dictionary:
        return redirect(url_for('index'))
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    hsk_level = request.args.get('hsk', '').strip()
    tocfl_level = request.args.get('tocfl', '').strip()
    
    results = []
    
    if query:
        results = dictionary.search_word(query, limit=50)
    elif category:
        results = dictionary.search_by_category(category, limit=50)
    elif hsk_level:
        try:
            results = dictionary.search_by_hsk_level(int(hsk_level), limit=50)
        except ValueError:
            pass
    elif tocfl_level:
        try:
            results = dictionary.search_by_tocfl_level(int(tocfl_level), limit=50)
        except ValueError:
            pass
    
    return render_template('search.html', 
                         results=results, 
                         query=query,
                         category=category,
                         hsk_level=hsk_level,
                         tocfl_level=tocfl_level)

@app.route('/word/<int:word_id>')
def word_detail(word_id):
    """Word detail page"""
    if not check_database_exists():
        return redirect(url_for('index'))
    
    dictionary = get_dictionary()
    if not dictionary:
        return redirect(url_for('index'))
    
    entry = dictionary.get_word_details(word_id)
    if not entry:
        return "Word not found", 404
    
    return render_template('word_detail.html', entry=entry)

@app.route('/random')
def random_words():
    """Random words page"""
    if not check_database_exists():
        return redirect(url_for('index'))
    
    dictionary = get_dictionary()
    if not dictionary:
        return redirect(url_for('index'))
    
    hsk_level = request.args.get('hsk', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if hsk_level:
        try:
            results = dictionary.get_random_words(limit=limit, hsk_level=int(hsk_level))
        except ValueError:
            results = dictionary.get_random_words(limit=limit)
    else:
        results = dictionary.get_random_words(limit=limit)
    
    return render_template('random.html', results=results, hsk_level=hsk_level)

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    if not check_database_exists():
        return jsonify({'error': 'Dictionary database not found'}), 500
    
    dictionary = get_dictionary()
    if not dictionary:
        return jsonify({'error': 'Dictionary not initialized'}), 500
    
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    results = dictionary.search_word(query, limit=limit)
    
    # Convert to JSON-serializable format
    results_data = []
    for entry in results:
        results_data.append({
            'id': entry.id,
            'word': entry.word,
            'pinyin': entry.pinyin,
            'zhuyin': entry.zhuyin,
            'vi_meaning': entry.vi_meaning,
            'en_meaning': entry.en_meaning,
            'hsk_level': entry.hsk_level,
            'tocfl_level': entry.tocfl_level,
            'hanviet_reading': entry.hanviet_reading
        })
    
    return jsonify({
        'query': query,
        'results': results_data,
        'count': len(results_data)
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    if not check_database_exists():
        return jsonify({'error': 'Dictionary database not found'}), 500
    
    dictionary = get_dictionary()
    if not dictionary:
        return jsonify({'error': 'Dictionary not initialized'}), 500
    
    stats = dictionary.get_statistics()
    return jsonify(stats)

if __name__ == '__main__':
    if check_database_exists():
        print("Dictionary initialized successfully!")
        print("Starting web server...")
        print("Open http://localhost:5000 in your browser")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Error: Dictionary database not found!")
        print("Please run 'python import_vietnamese_data.py' first to create the database.") 