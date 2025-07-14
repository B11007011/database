#!/usr/bin/env python3
"""
Test script for pinyin conversion
"""

from pinyin_utils import convert_pinyin_tone_numbers

def test_conversion():
    """Test pinyin conversion with various examples"""
    test_cases = [
        ("ni3 hao3", "nǐ hǎo"),
        ("zhong1guo2", "zhōngguó"),
        ("ma5", "ma"),
        ("nv3", "nǚ"),
        ("lü4", "lǜ"),
        ("shui3", "shuǐ"),
        ("xiang4", "xiàng"),
        ("qing3 wen4", "qǐng wèn"),
        ("wo3 ai4 ni3", "wǒ ài nǐ"),
        ("zhe4 shi4 yi2 ge5 ce4 shi4", "zhè shì yí gè cè shì")
    ]
    
    print("Testing pinyin conversion...\n")
    all_passed = True
    
    for input_py, expected in test_cases:
        result = convert_pinyin_tone_numbers(input_py)
        if result != expected:
            print(f"❌ FAIL: {input_py} -> {result} (expected: {expected})")
            all_passed = False
        else:
            print(f"✅ PASS: {input_py} -> {result}")
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")

if __name__ == "__main__":
    test_conversion()
