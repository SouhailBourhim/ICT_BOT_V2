#!/usr/bin/env python3
"""
Test the enhanced name extraction patterns
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.retrieval.professor_query_handler import ProfessorQueryHandler
import re

def test_name_extraction():
    """Test name extraction with INPT format"""
    print("🧪 Testing Enhanced Name Extraction")
    print("=" * 50)
    
    handler = ProfessorQueryHandler(None, None)
    
    # Test with actual INPT content
    test_texts = [
        "www.inpt.ac.ma\nMachine Learning IyadLAHSEN CHERIF, PhDPA, INPTlahsencherif@inpt.ac.ma",
        "www.inpt.ac.ma\nCours 2.1 : Hadoop IyadLAHSEN CHERIF, PhDPA, INPTlahsencherif@inpt.ac.ma",
        "www.inpt.ac.ma\nBig Data IyadLAHSEN CHERIF, PhDPA, INPTlahsencherif@inpt.ac.ma",
        "Professeur: Dr. Ahmed Benali",
        "Enseignant: M. Youssef Alami",
        "Course by Prof. Sarah Martin"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text[:50]}...")
        names = handler.extract_professor_names(text)
        relevance = handler._calculate_professor_relevance(text, "professor name")
        
        print(f"  Extracted names: {names}")
        print(f"  Relevance score: {relevance:.2f}")

def test_manual_patterns():
    """Test the patterns manually"""
    print("\n🔍 Testing Patterns Manually")
    print("=" * 40)
    
    text = "Machine Learning IyadLAHSEN CHERIF, PhDPA, INPTlahsencherif@inpt.ac.ma"
    
    patterns = [
        r'([A-Z][a-zA-Z]+[A-Z][A-Z]+\s+[A-Z][A-Z]+),\s*(?:PhD|PhDPA|Dr)',
        r'([A-Z][a-zA-Z]+\s+[A-Z][A-Z]+\s+[A-Z][A-Z]+),\s*(?:PhD|PhDPA|Dr)',
        r'([A-Z][a-zA-Z]+[A-Z][A-Z]+\s+[A-Z][A-Z]+),?\s*[^,]*@',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        matches = re.findall(pattern, text)
        print(f"Pattern {i}: {pattern}")
        print(f"  Matches: {matches}")
        
        if matches:
            for match in matches:
                # Test name formatting
                clean_name = match.strip()
                if re.match(r'^[A-Z][a-z]+[A-Z][A-Z]+', clean_name):
                    for j in range(1, len(clean_name)):
                        if clean_name[j].isupper() and clean_name[j-1].islower():
                            formatted_name = clean_name[:j] + ' ' + clean_name[j:]
                            print(f"  Formatted: {formatted_name}")
                            break

if __name__ == "__main__":
    test_name_extraction()
    test_manual_patterns()