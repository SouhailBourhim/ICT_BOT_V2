#!/usr/bin/env python3
"""
End-to-end test for professor queries including contact information
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.storage.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.llm.response_generator import ResponseGenerator
from src.llm.prompt_templates import PromptBuilder
from src.llm.providers.ollama_client import OllamaClient
from src.config.settings import settings

def test_professor_conversation_flow():
    """Test the complete professor conversation flow"""
    print("🎓 Testing Complete Professor Conversation Flow")
    print("=" * 60)
    
    try:
        # Initialize components
        print("1. Initializing components...")
        
        vector_store = VectorStore(
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        hybrid_search = HybridSearchEngine(
            vector_store=vector_store,
            semantic_weight=0.7,
            bm25_weight=0.3
        )
        
        ollama_client = OllamaClient(config={
            'base_url': settings.OLLAMA_BASE_URL,
            'model': settings.OLLAMA_MODEL
        })
        
        prompt_builder = PromptBuilder()
        
        response_generator = ResponseGenerator(
            hybrid_search=hybrid_search,
            ollama_client=ollama_client,
            prompt_builder=prompt_builder,
            min_confidence=0.3,
            max_sources=3,
            top_k_retrieval=5
        )
        
        print("✅ Components initialized")
        
        # Test conversation flow
        conversation_history = []
        
        # First query: Professor name
        print("\n2. Testing professor name query...")
        query1 = "What is the name of this course's professor?"
        
        response1 = response_generator.generate_response(
            question=query1,
            conversation_history=conversation_history,
            temperature=0.3
        )
        
        print(f"Query: '{query1}'")
        print(f"Answer: {response1.answer[:200]}...")
        print(f"Confidence: {response1.confidence:.3f}")
        print(f"Sources: {len(response1.sources)}")
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": query1})
        conversation_history.append({"role": "assistant", "content": response1.answer})
        
        # Second query: Professor email (follow-up)
        print("\n3. Testing professor contact follow-up query...")
        query2 = "What is his email?"
        
        response2 = response_generator.generate_response(
            question=query2,
            conversation_history=conversation_history,
            temperature=0.3
        )
        
        print(f"Query: '{query2}'")
        print(f"Answer: {response2.answer[:200]}...")
        print(f"Confidence: {response2.confidence:.3f}")
        print(f"Sources: {len(response2.sources)}")
        
        # Check if email is found
        email_found = "INPTlahsencherif@inpt.ac.ma" in response2.answer or "lahsencherif@inpt.ac.ma" in response2.answer
        
        print(f"\n4. Results Analysis:")
        print(f"✅ Professor name query handled: {response1.confidence > 0.5}")
        print(f"✅ Contact query detected and handled: {response2.confidence > 0.3}")
        print(f"✅ Email information found: {email_found}")
        
        if email_found:
            print(f"\n🎯 SUCCESS: Complete professor conversation flow working!")
            print(f"   - Professor name query: ✅")
            print(f"   - Follow-up contact query: ✅")
            print(f"   - Email extraction: ✅")
        else:
            print(f"\n❌ Issue: Email not found in response")
            
        return email_found and response1.confidence > 0.5 and response2.confidence > 0.3
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_user_interaction():
    """Simulate the expected user interaction"""
    print("\n" + "="*60)
    print("🗣️ SIMULATED USER INTERACTION")
    print("="*60)
    
    print("User: What is the name of this course's professor?")
    print("Assistant: Le professeur de ce cours de Machine Learning est Iyad LAHSEN CHERIF, PhDPA.")
    print("          Cette information se trouve sur la première page du document.")
    print("          [Source: Algo_ML1_v2.pdf, page 1]")
    print()
    print("User: What is his email?")
    print("Assistant: L'adresse email du professeur Iyad LAHSEN CHERIF est INPTlahsencherif@inpt.ac.ma.")
    print("          [Source: Algo_ML1_v2.pdf, page 1]")
    print()
    print("✅ This conversation flow should now work in the Streamlit app!")

if __name__ == "__main__":
    success = test_professor_conversation_flow()
    simulate_user_interaction()
    
    if success:
        print(f"\n🚀 READY FOR DEMO!")
        print(f"   The Streamlit app is running at: http://localhost:8501")
        print(f"   Test these queries in sequence:")
        print(f"   1. 'What is the name of this course's professor?'")
        print(f"   2. 'What is his email?'")
    else:
        print(f"\n❌ Some issues detected. Please check the implementation.")