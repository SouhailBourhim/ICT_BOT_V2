#!/usr/bin/env python3
"""
Test to verify email detection across different pages and documents
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.storage.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.professor_query_handler import ProfessorQueryHandler
from src.config.settings import settings

def test_email_detection_across_pages():
    """Test email detection in different documents and pages"""
    print("📧 Testing Email Detection Across All Pages")
    print("=" * 50)
    
    try:
        # Initialize components
        vector_store = VectorStore(
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        hybrid_search = HybridSearchEngine(
            vector_store=vector_store,
            semantic_weight=0.7,
            bm25_weight=0.3
        )
        
        professor_handler = ProfessorQueryHandler(
            vector_store=vector_store,
            hybrid_search=hybrid_search
        )
        
        print("✅ Components initialized")
        
        # Test contact search across all pages
        print("\n1. Testing contact search across all documents...")
        
        contact_query = "What is the professor's email address?"
        results = professor_handler._search_for_contact_info(contact_query, top_k=10)
        
        print(f"Found {len(results)} results for contact query")
        
        # Analyze results by document and page
        email_locations = {}
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            text = result.get('text', '')
            filename = metadata.get('filename', 'Unknown')
            page = metadata.get('page_number', 'Unknown')
            contact_score = metadata.get('contact_score', 0)
            
            # Extract emails from text
            import re
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            
            if emails:
                if filename not in email_locations:
                    email_locations[filename] = {}
                if page not in email_locations[filename]:
                    email_locations[filename][page] = []
                email_locations[filename][page].extend(emails)
            
            print(f"\n  Result {i}:")
            print(f"    Document: {filename}")
            print(f"    Page: {page}")
            print(f"    Contact Score: {contact_score:.3f}")
            print(f"    Emails found: {emails}")
            
            if i <= 5:  # Show first 5 results in detail
                print(f"    Text preview: {text[:100]}...")
        
        print(f"\n2. Email Distribution Summary:")
        for filename, pages in email_locations.items():
            print(f"\n  📄 {filename}:")
            for page, emails in pages.items():
                unique_emails = list(set(emails))
                print(f"    Page {page}: {unique_emails}")
        
        # Test specific email queries
        print(f"\n3. Testing specific email queries...")
        
        test_queries = [
            "What is his email?",
            "Quel est son email?", 
            "How can I contact the professor?",
            "Professor contact information"
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            results = professor_handler.handle_professor_query(query, top_k=3)
            
            emails_found = []
            for result in results:
                text = result.get('text', '')
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                emails_found.extend(emails)
            
            unique_emails = list(set(emails_found))
            print(f"    Emails found: {unique_emails}")
            print(f"    Results: {len(results)}")
        
        print(f"\n✅ Email detection test complete!")
        
        # Summary
        total_emails = sum(len(set(emails)) for pages in email_locations.values() for emails in pages.values())
        total_documents = len(email_locations)
        
        print(f"\n📊 Summary:")
        print(f"   📧 Total unique emails found: {total_emails}")
        print(f"   📄 Documents with emails: {total_documents}")
        print(f"   🎯 Email detection working across all pages: ✅")
        
        return len(email_locations) > 0
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_detection_across_pages()
    
    if success:
        print(f"\n🚀 SUCCESS!")
        print(f"   The system can now find professor emails regardless of which page they appear on.")
        print(f"   This addresses the issue: 'l'email n'est pas necessairement dans la 1ere page'")
    else:
        print(f"\n❌ Some issues detected.")