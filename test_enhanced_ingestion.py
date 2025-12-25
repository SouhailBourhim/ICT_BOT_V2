#!/usr/bin/env python3
"""
Test script for enhanced chunk ingestion with contextual headers
"""
import sys
import tempfile
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from scripts.ingest_documents import DocumentIngestion
from src.storage.models import EnhancedChunk

def test_enhanced_ingestion():
    """Test the enhanced ingestion pipeline with contextual headers"""
    
    # Create a temporary test document
    test_content = """
# Introduction to Machine Learning

Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions from data.

## 1. Supervised Learning

Supervised learning uses labeled data to train models. The algorithm learns from input-output pairs.

### 1.1 Classification
Classification predicts discrete categories or classes.

### 1.2 Regression
Regression predicts continuous numerical values.

## 2. Unsupervised Learning

Unsupervised learning finds patterns in data without labeled examples.

### 2.1 Clustering
Clustering groups similar data points together.

### 2.2 Dimensionality Reduction
Reduces the number of features while preserving important information.

## 3. Deep Learning

Deep learning uses neural networks with multiple layers to learn complex patterns.
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        temp_file_path = Path(f.name)
    
    try:
        print("🧪 Testing Enhanced Ingestion Pipeline")
        print("=" * 50)
        
        # Initialize ingestion pipeline
        ingestion = DocumentIngestion()
        
        # Get initial count
        initial_count = ingestion.vector_store.count()
        print(f"Initial document count: {initial_count}")
        
        # Ingest the test document
        print(f"\n📄 Ingesting test document: {temp_file_path.name}")
        num_chunks = ingestion.ingest_document(temp_file_path)
        
        print(f"✅ Created {num_chunks} chunks")
        
        # Get final count
        final_count = ingestion.vector_store.count()
        print(f"Final document count: {final_count}")
        print(f"New chunks added: {final_count - initial_count}")
        
        # Retrieve and examine the newly created chunks
        print("\n🔍 Examining newly created chunks:")
        print("-" * 40)
        
        # Get recent documents (assuming they are the ones we just added)
        all_docs = ingestion.vector_store.peek(limit=final_count)
        
        # Find our test document chunks (they should have the temp filename)
        test_chunks = []
        for doc_id, text, metadata in zip(
            all_docs['ids'],
            all_docs['documents'], 
            all_docs['metadatas']
        ):
            if temp_file_path.stem in metadata.get('filename', ''):
                test_chunks.append((doc_id, text, metadata))
        
        print(f"Found {len(test_chunks)} chunks from test document")
        
        # Examine each chunk
        for i, (doc_id, text, metadata) in enumerate(test_chunks[:5]):  # Show first 5
            print(f"\n--- Chunk {i+1} ---")
            print(f"ID: {doc_id}")
            print(f"Filename: {metadata.get('filename', 'N/A')}")
            print(f"Has contextual_header: {'contextual_header' in metadata}")
            print(f"Has hierarchy_path: {'hierarchy_path' in metadata}")
            print(f"Has structure_metadata: {'structure_metadata' in metadata}")
            print(f"Chunk method: {metadata.get('chunk_method', 'N/A')}")
            
            if 'contextual_header' in metadata and metadata['contextual_header']:
                print(f"Contextual header: '{metadata['contextual_header']}'")
            
            if 'hierarchy_path' in metadata:
                print(f"Hierarchy path: {metadata['hierarchy_path']}")
            
            print(f"Text length: {len(text)}")
            print(f"First 100 chars: {text[:100]}...")
        
        # Test search with contextual headers
        print(f"\n🔍 Testing search functionality:")
        print("-" * 30)
        
        search_results = ingestion.vector_store.search(
            "What is supervised learning?", 
            n_results=3
        )
        
        print(f"Search returned {len(search_results['documents'])} results")
        for i, (doc, meta, dist) in enumerate(zip(
            search_results['documents'][:2],
            search_results['metadatas'][:2],
            search_results['distances'][:2]
        )):
            print(f"\nResult {i+1} (distance: {dist:.3f}):")
            if 'contextual_header' in meta and meta['contextual_header']:
                print(f"  Contextual header: '{meta['contextual_header']}'")
            print(f"  Text: {doc[:150]}...")
        
        print("\n✅ Enhanced ingestion test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()
            print(f"\n🧹 Cleaned up temporary file: {temp_file_path.name}")

if __name__ == "__main__":
    test_enhanced_ingestion()