#!/usr/bin/env python3
"""
Test script for professor query functionality
This script demonstrates the enhanced professor name detection capability
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.retrieval.professor_query_handler import ProfessorQueryHandler
from src.storage.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.llm.response_generator import ResponseGenerator
from src.llm.prompt_templates import PromptBuilder
from src.config.settings import settings

def test_professor_query_detection():
    """Test professor query detection patterns"""
    print("🧪 Testing Professor Query Detection")
    print("=" * 50)
    
    # Create handler (without actual vector store for pattern testing)
    handler = ProfessorQueryHandler(None, None)
    
    test_queries = [
        "What is the name of this course's professor?",
        "Quel est le nom du professeur de ce cours?",
        "Who teaches this course?",
        "Qui enseigne ce module?",
        "Who is the course instructor?",
        "Nom du responsable du cours",
        "Prof de machine learning",
        "What is machine learning?",  # Non-professor query
        "Explain neural networks",    # Non-professor query
        "How does gradient descent work?"  # Non-professor query
    ]
    
    for query in test_queries:
        is_prof_query = handler.is_professor_query(query)
        status = "✅ PROFESSOR" if is_prof_query else "❌ REGULAR"
        print(f"{status}: '{query}'")
    
    print()

def test_professor_name_extraction():
    """Test professor name extraction from sample text"""
    print("🔍 Testing Professor Name Extraction")
    print("=" * 50)
    
    handler = ProfessorQueryHandler(None, None)
    
    sample_texts = [
        """
        Cours de Machine Learning
        Professeur: Dr. Ahmed Benali
        INPT - Smart ICT
        Année 2024-2025
        """,
        """
        Machine Learning Algorithms
        Course Instructor: Prof. Sarah Martin
        Email: s.martin@inpt.ac.ma
        """,
        """
        Introduction aux Algorithmes ML
        Enseignant responsable: M. Youssef Alami
        Bureau: B204
        """,
        """
        This course covers various machine learning techniques
        including supervised and unsupervised learning.
        No professor name mentioned here.
        """
    ]
    
    for i, text in enumerate(sample_texts, 1):
        print(f"Sample Text {i}:")
        names = handler.extract_professor_names(text)
        if names:
            print(f"  Found names: {names}")
        else:
            print("  No professor names found")
        
        relevance = handler._calculate_professor_relevance(text, "professor name")
        print(f"  Relevance score: {relevance:.2f}")
        print()

def simulate_professor_query_flow():
    """Simulate the complete professor query flow"""
    print("🎯 Simulating Professor Query Flow")
    print("=" * 50)
    
    print("1. Query: 'What is the name of this course's professor?'")
    print("2. ✅ Detected as professor query")
    print("3. 🔍 Searching first page chunks...")
    print("4. 📄 Found first page content from 'Algo_ML1_v2.pdf'")
    print("5. 🎯 Boosting score for professor-relevant content")
    print("6. 💬 Using specialized professor prompt template")
    print("7. 🤖 LLM focuses on extracting professor names")
    print("8. ✅ Returns: 'Le professeur de ce cours est Dr. Ahmed Benali'")
    print()

def check_document_structure():
    """Check if documents are properly indexed with page information"""
    print("📚 Checking Document Structure")
    print("=" * 50)
    
    try:
        # Initialize vector store
        vector_store = VectorStore(
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        # Get collection stats
        stats = vector_store.get_collection_stats()
        print(f"Total documents in collection: {stats['total_documents']}")
        
        # Try to get some sample documents to check page metadata
        try:
            all_docs = vector_store.get_all_with_metadata()
            
            if 'normalized_results' in all_docs:
                sample_docs = all_docs['normalized_results'][:5]
                print("\nSample documents with metadata:")
                for i, doc in enumerate(sample_docs, 1):
                    metadata = doc.get('metadata', {})
                    filename = metadata.get('filename', 'Unknown')
                    page_num = metadata.get('page_number', 'N/A')
                    print(f"  {i}. {filename} - Page: {page_num}")
            else:
                print("No normalized results available")
                
        except Exception as e:
            print(f"Could not retrieve documents: {e}")
            
    except Exception as e:
        print(f"Could not connect to vector store: {e}")
        print("Make sure documents are indexed first!")
    
    print()

def main():
    """Main test function"""
    print("🎓 Professor Query Enhancement Test")
    print("=" * 60)
    print()
    
    # Test 1: Query detection
    test_professor_query_detection()
    
    # Test 2: Name extraction
    test_professor_name_extraction()
    
    # Test 3: Simulate flow
    simulate_professor_query_flow()
    
    # Test 4: Check document structure
    check_document_structure()
    
    print("📋 Summary of Enhancements:")
    print("=" * 50)
    print("✅ 1. Professor query detection with regex patterns")
    print("✅ 2. Specialized retrieval prioritizing first page content")
    print("✅ 3. Professor name extraction with title patterns")
    print("✅ 4. Specialized prompt template for professor queries")
    print("✅ 5. Score boosting for professor-relevant content")
    print()
    print("🚀 The system should now correctly identify professor names!")
    print("   Try asking: 'What is the name of this course's professor?'")

if __name__ == "__main__":
    main()