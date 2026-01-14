#!/usr/bin/env python3
"""
Script to examine the actual content of first pages to understand the professor name issue
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.document_processing.parser import DocumentParser
from src.config.settings import settings

def examine_first_pages():
    """Examine the first page content of all PDF documents"""
    print("🔍 Examining First Page Content")
    print("=" * 50)
    
    parser = DocumentParser()
    documents_dir = settings.DOCUMENTS_DIR
    
    for doc_path in documents_dir.glob("*.pdf"):
        print(f"\n📄 Document: {doc_path.name}")
        print("-" * 40)
        
        try:
            # Parse document
            parsed_doc = parser.parse(doc_path)
            
            if parsed_doc.pages:
                first_page = parsed_doc.pages[0]
                content = first_page['content']
                
                print(f"First page length: {len(content)} characters")
                print("First page content:")
                print("=" * 30)
                print(content)
                print("=" * 30)
                
                # Look for professor-related patterns
                import re
                
                # Check for common professor patterns
                patterns = [
                    r'(?i)(prof|professeur|dr|enseignant|instructor)',
                    r'(?i)(responsable|coordinator)',
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
                    r'(?i)(cours|course|module)',
                ]
                
                print("\nPattern matches:")
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f"  {pattern}: {matches}")
                
            else:
                print("No page structure found")
                print("Full document content (first 500 chars):")
                print(parsed_doc.content[:500])
                
        except Exception as e:
            print(f"Error parsing {doc_path.name}: {e}")

def examine_full_document_content():
    """Examine full document content to find professor information"""
    print("\n\n🔍 Examining Full Document Content for Professor Info")
    print("=" * 60)
    
    parser = DocumentParser()
    documents_dir = settings.DOCUMENTS_DIR
    
    # Focus on the ML course document
    ml_doc = documents_dir / "Algo_ML1_v2.pdf"
    
    if ml_doc.exists():
        print(f"📄 Analyzing: {ml_doc.name}")
        
        try:
            parsed_doc = parser.parse(ml_doc)
            
            # Search through all content for professor information
            full_content = parsed_doc.content
            
            print(f"Total document length: {len(full_content)} characters")
            
            # Look for professor patterns in full content
            import re
            
            professor_patterns = [
                r'(?i)(?:prof|professeur|dr)\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
                r'(?i)(?:enseignant|instructor|responsable):\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
                r'(?i)(?:par|by):\s*(?:prof|dr)\.?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            ]
            
            print("\nSearching for professor names in full document:")
            found_names = []
            
            for pattern in professor_patterns:
                matches = re.findall(pattern, full_content)
                if matches:
                    print(f"  Pattern '{pattern}': {matches}")
                    found_names.extend(matches)
            
            # Look for email addresses
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_pattern, full_content)
            if emails:
                print(f"  Email addresses: {emails}")
            
            # Show context around potential professor names
            if found_names:
                print(f"\nFound potential professor names: {found_names}")
                
                for name in found_names[:3]:  # Show context for first 3 names
                    # Find context around the name
                    name_pos = full_content.lower().find(name.lower())
                    if name_pos != -1:
                        start = max(0, name_pos - 100)
                        end = min(len(full_content), name_pos + len(name) + 100)
                        context = full_content[start:end]
                        print(f"\nContext for '{name}':")
                        print(f"...{context}...")
            else:
                print("\nNo professor names found with standard patterns")
                
                # Show first few pages content to manually inspect
                if parsed_doc.pages:
                    print("\nFirst 3 pages content:")
                    for i, page in enumerate(parsed_doc.pages[:3], 1):
                        print(f"\n--- Page {i} ---")
                        print(page['content'][:300] + "..." if len(page['content']) > 300 else page['content'])
                
        except Exception as e:
            print(f"Error analyzing document: {e}")
    else:
        print(f"ML document not found: {ml_doc}")

if __name__ == "__main__":
    examine_first_pages()
    examine_full_document_content()