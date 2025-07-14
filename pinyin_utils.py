#!/usr/bin/env python3
"""
Pinyin conversion utilities
"""

def convert_pinyin_tone_numbers(pinyin: str) -> str:
    """
    Convert pinyin with tone numbers to pinyin with diacritical marks.
    
    Args:
        pinyin: Pinyin string with tone numbers (e.g., "ni3 hao3")
        
    Returns:
        Pinyin string with diacritical marks (e.g., "nǐ hǎo")
    """
    if not pinyin:
        return pinyin
    
    # Define pinyin tone rules
    tone_marks = {
        'a': ['a', 'ā', 'á', 'ǎ', 'à'],
        'e': ['e', 'ē', 'é', 'ě', 'è'],
        'i': ['i', 'ī', 'í', 'ǐ', 'ì'],
        'o': ['o', 'ō', 'ó', 'ǒ', 'ò'],
        'u': ['u', 'ū', 'ú', 'ǔ', 'ù'],
        'ü': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ'],
        'A': ['A', 'Ā', 'Á', 'Ǎ', 'À'],
        'E': ['E', 'Ē', 'É', 'Ě', 'È'],
        'I': ['I', 'Ī', 'Í', 'Ǐ', 'Ì'],
        'O': ['O', 'Ō', 'Ó', 'Ǒ', 'Ò'],
        'U': ['U', 'Ū', 'Ú', 'Ǔ', 'Ù'],
        'Ü': ['Ü', 'Ǖ', 'Ǘ', 'Ǚ', 'Ǜ']
    }
    
    # Split into words in case of multiple syllables
    words = pinyin.split()
    converted_words = []
    
    for word in words:
        # Extract the tone number if it exists
        tone = 0
        clean_word = word
        
        if word and word[-1].isdigit():
            tone = int(word[-1])
            clean_word = word[:-1]
        
        # If no tone or invalid tone, return as is
        if tone < 1 or tone > 4:
            converted_words.append(word)
            continue
            
        # Find the vowel to mark
        marked = False
        for v in ['a', 'e', 'i', 'o', 'u', 'ü', 'A', 'E', 'I', 'O', 'U', 'Ü']:
            if v in clean_word:
                # Special case for 'iu' and 'ui'
                if v == 'i' and 'u' in clean_word and 'a' not in clean_word and 'o' not in clean_word and 'e' not in clean_word:
                    v = 'u'
                elif v == 'u' and 'i' in clean_word and 'a' not in clean_word and 'o' not in clean_word and 'e' not in clean_word:
                    v = 'i'
                # Replace the vowel with the marked version
                clean_word = clean_word.replace(v, tone_marks[v][tone], 1)
                marked = True
                break
        
        converted_words.append(clean_word)
    
    return ' '.join(converted_words)
