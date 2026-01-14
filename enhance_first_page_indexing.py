#!/usr/bin/env python3
"""
Script to enhance first page indexing for better professor name detection
This script ensures first page content is properly chunked and indexed
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.document_processing.parser import DocumentParser
from src.document_processing.chunker import SemanticChunker
from src.storage.vector_store import VectorStore
from src.config.settings import settings
import re

def extract_first_page_professor_info(text: str, filename: str) -> dict:
    """
    Extract professor information specifically from first page content
    
    Args:
        text: First page text content
        filename: Document filename
        
    Returns:
        Dictionary with professor information
    """
    professor_info = {
        'names': [],
        'titles': [],
        'contact': [],
        'course_info': []
    }
    
    # Professor name patterns (more comprehensive for INPT format)
    name_patterns = [
        # Standard patterns with titles
        r'(?:Professeur|Prof\.?|Dr\.?|M\.?|Mme\.?)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        r'(?:Enseignant|Instructor|Teacher):\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        r'(?:Responsable|Coordinator):\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        r'(?:Par|By):\s*(?:Prof\.?|Dr\.?|M\.?|Mme\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        
        # INPT specific patterns - name followed by credentials and email
        r'([A-Z][a-zA-Z]+[A-Z][A-Z]+\s+[A-Z][A-Z]+),\s*(?:PhD|PhDPA|Dr)',  # IyadLAHSEN CHERIF, PhDPA
        r'([A-Z][a-zA-Z]+\s+[A-Z][A-Z]+\s+[A-Z][A-Z]+),\s*(?:PhD|PhDPA|Dr)',  # Name with spaces
        
        # Name before email pattern
        r'([A-Z][a-zA-Z]+[A-Z][A-Z]+\s+[A-Z][A-Z]+),?\s*[^,]*@',  # Name before email
        r'([A-Z][a-zA-Z]+\s+[A-Z][A-Z]+\s+[A-Z][A-Z]+),?\s*[^,]*@',  # Name with spaces before email
    ]
    
    # Extract names
    for pattern in name_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            clean_name = match.strip()
            # Clean up the name (add spaces if needed)
            if clean_name and len(clean_name) > 3:
                # Handle names like "IyadLAHSEN" -> "Iyad LAHSEN"
                if re.match(r'^[A-Z][a-z]+[A-Z][A-Z]+', clean_name):
                    # Find where lowercase ends and uppercase begins
                    for i in range(1, len(clean_name)):
                        if clean_name[i].isupper() and clean_name[i-1].islower():
                            clean_name = clean_name[:i] + ' ' + clean_name[i:]
                            break
                
                if clean_name not in professor_info['names']:
                    professor_info['names'].append(clean_name)
    
    # Extract email addresses (often associated with professors)
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    emails = re.findall(email_pattern, text)
    professor_info['contact'].extend(emails)
    
    # Extract course titles
    course_patterns = [
        r'(?:Cours|Course|Module):\s*([^\n]+)',
        r'^([A-Z][^.\n]*(?:Machine Learning|ML|Intelligence Artificielle|AI|Data Science|Big Data|Hadoop)[^.\n]*)',
    ]
    
    for pattern in course_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        professor_info['course_info'].extend(matches)
    
    return professor_info

def create_enhanced_first_page_chunk(page_content: str, doc_metadata: dict, professor_info: dict) -> str:
    """
    Create an enhanced first page chunk with professor information highlighted
    
    Args:
        page_content: Original first page content
        doc_metadata: Document metadata
        professor_info: Extracted professor information
        
    Returns:
        Enhanced chunk text with professor information
    """
    enhanced_content = f"=== PREMIÈRE PAGE - {doc_metadata.get('filename', 'Document')} ===\n\n"
    
    # Add professor information summary if found
    if professor_info['names']:
        enhanced_content += "PROFESSEUR/ENSEIGNANT:\n"
        for name in professor_info['names']:
            enhanced_content += f"- {name}\n"
        enhanced_content += "\n"
    
    if professor_info['contact']:
        enhanced_content += "CONTACT:\n"
        for contact in professor_info['contact']:
            enhanced_content += f"- {contact}\n"
        enhanced_content += "\n"
    
    if professor_info['course_info']:
        enhanced_content += "COURS:\n"
        for course in professor_info['course_info']:
            enhanced_content += f"- {course.strip()}\n"
        enhanced_content += "\n"
    
    # Add original content
    enhanced_content += "CONTENU ORIGINAL:\n"
    enhanced_content += page_content
    
    return enhanced_content

def enhance_document_indexing():
    """
    Re-process documents with enhanced first page handling
    """
    print("🔧 Enhancing Document Indexing for Professor Detection")
    print("=" * 60)
    
    # Initialize components
    parser = DocumentParser()
    chunker = SemanticChunker(
        chunk_size=800,  # Smaller chunks for better precision
        chunk_overlap=150,
        min_chunk_size=50
    )
    
    vector_store = VectorStore(
        persist_directory=str(settings.CHROMA_PERSIST_DIR),
        collection_name=settings.CHROMA_COLLECTION_NAME
    )
    
    documents_dir = settings.DOCUMENTS_DIR
    processed_count = 0
    
    print(f"📁 Scanning documents in: {documents_dir}")
    
    # Process each document
    for doc_path in documents_dir.glob("*.pdf"):
        print(f"\n📄 Processing: {doc_path.name}")
        
        try:
            # Parse document
            parsed_doc = parser.parse(doc_path)
            
            if not parsed_doc.pages:
                print("  ⚠️  No page structure found, skipping enhanced processing")
                continue
            
            # Focus on first page
            first_page = parsed_doc.pages[0]
            first_page_content = first_page['content']
            
            print(f"  📖 First page content length: {len(first_page_content)} chars")
            
            # Extract professor information
            professor_info = extract_first_page_professor_info(
                first_page_content, 
                doc_path.name
            )
            
            print(f"  👨‍🏫 Found professor names: {professor_info['names']}")
            print(f"  📧 Found contacts: {professor_info['contact']}")
            
            # Create enhanced first page chunk
            if professor_info['names'] or professor_info['contact']:
                enhanced_content = create_enhanced_first_page_chunk(
                    first_page_content,
                    parsed_doc.metadata,
                    professor_info
                )
                
                # Create special metadata for first page chunk
                enhanced_metadata = {
                    **parsed_doc.metadata,
                    'page_number': 1,
                    'is_first_page': True,
                    'has_professor_info': True,
                    'professor_names': professor_info['names'],
                    'professor_contacts': professor_info['contact'],
                    'chunk_type': 'enhanced_first_page'
                }
                
                # Add to vector store with special ID
                special_id = f"{doc_path.stem}_enhanced_first_page"
                
                try:
                    vector_store.add_documents(
                        texts=[enhanced_content],
                        metadatas=[enhanced_metadata],
                        ids=[special_id]
                    )
                    print(f"  ✅ Added enhanced first page chunk: {special_id}")
                    processed_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error adding enhanced chunk: {e}")
            else:
                print("  ℹ️  No professor information found on first page")
                
        except Exception as e:
            print(f"  ❌ Error processing {doc_path.name}: {e}")
    
    print(f"\n✅ Enhanced indexing complete!")
    print(f"📊 Processed {processed_count} documents with professor information")
    
    # Show collection stats
    try:
        stats = vector_store.get_collection_stats()
        print(f"📚 Total documents in collection: {stats.get('total_documents', 'Unknown')}")
    except Exception as e:
        print(f"📚 Could not get collection stats: {e}")
        # Try alternative method
        try:
            collection_count = vector_store.collection.count()
            print(f"📚 Total documents in collection: {collection_count}")
        except Exception as e2:
            print(f"📚 Could not get collection count: {e2}")

def test_professor_query():
    """
    Test professor query with enhanced indexing
    """
    print("\n🧪 Testing Professor Query")
    print("=" * 40)
    
    try:
        vector_store = VectorStore(
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        # Search for professor-related content
        results = vector_store.search(
            query_text="professor name enseignant responsable",
            n_results=5
        )
        
        print("🔍 Search results for professor-related content:")
        
        if 'normalized_results' in results:
            for i, result in enumerate(results['normalized_results'][:3], 1):
                metadata = result.get('metadata', {})
                content = result.get('content', '')[:200] + "..."
                
                print(f"\n{i}. Document: {metadata.get('filename', 'Unknown')}")
                print(f"   Page: {metadata.get('page_number', 'N/A')}")
                print(f"   Has professor info: {metadata.get('has_professor_info', False)}")
                print(f"   Professor names: {metadata.get('professor_names', [])}")
                print(f"   Content preview: {content}")
        else:
            print("No results found or wrong format")
            
    except Exception as e:
        print(f"Error testing query: {e}")

def main():
    """Main function"""
    print("🎓 Professor Query Enhancement - Document Indexing")
    print("=" * 70)
    
    # Enhance document indexing
    enhance_document_indexing()
    
    # Test the enhancement
    test_professor_query()
    
    print("\n🚀 Enhancement Complete!")
    print("The system should now better detect professor names from first pages.")
    print("Try asking: 'What is the name of this course's professor?'")

if __name__ == "__main__":
    main()