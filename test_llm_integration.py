#!/usr/bin/env python3
"""
Test script for LLM integration with multiple providers.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.llm.llm_setup import create_llm_manager, test_providers, print_provider_info
from src.config.settings import settings
from loguru import logger


async def test_basic_generation():
    """Test basic text generation with available providers."""
    print("\n🧪 Testing Basic Text Generation")
    print("=" * 50)
    
    try:
        # Create LLM manager
        manager = create_llm_manager()
        
        # Test prompt
        test_prompt = "Explain what IoT (Internet of Things) is in one sentence."
        
        # Test with fallback
        print(f"\n📝 Prompt: {test_prompt}")
        print("\n🔄 Generating response with automatic fallback...")
        
        response = await manager.generate_with_fallback(
            prompt=test_prompt,
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"\n✅ Response from {response.provider}:")
        print(f"📄 {response.content}")
        
        if response.usage:
            print(f"\n📊 Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during generation test: {e}")
        return False


async def test_rag_simulation():
    """Simulate a RAG query with context."""
    print("\n🧪 Testing RAG Simulation")
    print("=" * 50)
    
    try:
        manager = create_llm_manager()
        
        # Simulate context from documents
        context = """
        L'Internet des Objets (IoT) est un réseau d'objets physiques connectés qui collectent et échangent des données. 
        Ces objets incluent des capteurs, des actionneurs et des dispositifs intelligents.
        Les applications IoT incluent la domotique, l'industrie 4.0, et les villes intelligentes.
        """
        
        question = "Quelles sont les principales applications de l'IoT ?"
        
        print(f"\n📝 Question: {question}")
        print(f"\n📚 Context: {context[:100]}...")
        
        # Create RAG-style prompt
        rag_prompt = f"""Context: {context}

Question: {question}

Répondez en français en vous basant sur le contexte fourni."""
        
        response = await manager.generate_with_fallback(
            prompt=rag_prompt,
            temperature=0.3,
            max_tokens=200
        )
        
        print(f"\n✅ RAG Response from {response.provider}:")
        print(f"📄 {response.content}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during RAG test: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 LLM Integration Test Suite")
    print("=" * 60)
    
    # Show current configuration
    print(f"\n⚙️ Configuration:")
    print(f"   Primary Provider: {settings.LLM_PROVIDER}")
    print(f"   Fallback Provider: {settings.LLM_FALLBACK_PROVIDER}")
    print(f"   Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"   Ollama Model: {settings.OLLAMA_MODEL}")
    print(f"   Gemini Model: {settings.GEMINI_MODEL}")
    print(f"   Google API Key: {'✅ Set' if settings.GOOGLE_API_KEY else '❌ Not set'}")
    
    # Test provider availability
    print("\n🔍 Testing Provider Availability")
    print("-" * 40)
    provider_results = test_providers()
    
    available_count = sum(provider_results.values())
    total_count = len(provider_results)
    
    print(f"\n📊 Summary: {available_count}/{total_count} providers available")
    
    if available_count == 0:
        print("\n❌ No providers available. Please check your configuration:")
        print("   - For Ollama: Make sure it's running (ollama serve)")
        print("   - For Gemini: Set GOOGLE_API_KEY in .env file")
        return False
    
    # Show detailed provider info
    print_provider_info()
    
    # Run async tests
    print("\n🧪 Running Async Tests")
    print("-" * 40)
    
    # Test basic generation
    basic_success = asyncio.run(test_basic_generation())
    
    # Test RAG simulation
    rag_success = asyncio.run(test_rag_simulation())
    
    # Final summary
    print("\n📋 Test Results Summary")
    print("=" * 50)
    print(f"Provider Availability: {available_count}/{total_count} ✅")
    print(f"Basic Generation: {'✅' if basic_success else '❌'}")
    print(f"RAG Simulation: {'✅' if rag_success else '❌'}")
    
    if basic_success and rag_success:
        print("\n🎉 All tests passed! Your LLM integration is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Add your Google API key to .env for Gemini support")
        print("   2. Run the Streamlit app: streamlit run app/chat.py")
        print("   3. Test the provider selection in the sidebar")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)