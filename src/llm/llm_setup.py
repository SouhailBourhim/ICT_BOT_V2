"""
LLM Setup utility for initializing and configuring LLM providers.
"""
from typing import Dict, Any, Optional
from loguru import logger

from .llm_factory import LLMFactory, LLMManager
from ..config.settings import settings


def create_llm_manager() -> LLMManager:
    """
    Create and configure LLM manager with available providers.
    
    Returns:
        Configured LLMManager instance
    """
    manager = LLMManager()
    
    # Configure primary provider
    primary_provider = settings.LLM_PROVIDER
    primary_config = _get_provider_config(primary_provider)
    
    try:
        primary_llm = LLMFactory.create_llm(primary_provider, primary_config)
        manager.add_provider(primary_provider, primary_llm)
        manager.set_default_provider(primary_provider)
        logger.info(f"✅ Primary LLM provider configured: {primary_provider}")
    except Exception as e:
        logger.error(f"❌ Failed to configure primary provider {primary_provider}: {e}")
    
    # Configure fallback provider if different from primary
    fallback_provider = settings.LLM_FALLBACK_PROVIDER
    if fallback_provider != primary_provider:
        fallback_config = _get_provider_config(fallback_provider)
        
        try:
            fallback_llm = LLMFactory.create_llm(fallback_provider, fallback_config)
            manager.add_provider(fallback_provider, fallback_llm)
            logger.info(f"✅ Fallback LLM provider configured: {fallback_provider}")
        except Exception as e:
            logger.error(f"❌ Failed to configure fallback provider {fallback_provider}: {e}")
    
    # Add other available providers if API keys are present
    _add_optional_providers(manager)
    
    return manager


def _get_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for a specific provider."""
    if provider == 'ollama':
        return {
            'base_url': settings.OLLAMA_BASE_URL,
            'model': settings.OLLAMA_MODEL,
            'timeout': settings.OLLAMA_TIMEOUT
        }
    elif provider == 'gemini':
        return {
            'api_key': settings.GOOGLE_API_KEY,
            'model': settings.GEMINI_MODEL
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _add_optional_providers(manager: LLMManager):
    """Add optional providers if their API keys are available."""
    
    # Add Gemini if API key is available and not already added
    if (settings.GOOGLE_API_KEY and 
        'gemini' not in manager.get_available_providers()):
        try:
            gemini_config = _get_provider_config('gemini')
            gemini_llm = LLMFactory.create_llm('gemini', gemini_config)
            manager.add_provider('gemini', gemini_llm)
            logger.info("✅ Optional Gemini provider added")
        except Exception as e:
            logger.warning(f"⚠️ Could not add optional Gemini provider: {e}")


def get_provider_status() -> Dict[str, Dict[str, Any]]:
    """
    Get status of all configured providers.
    
    Returns:
        Dictionary with provider status information
    """
    try:
        manager = create_llm_manager()
        return manager.get_provider_info()
    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        return {}


def test_providers() -> Dict[str, bool]:
    """
    Test all configured providers with a simple query.
    
    Returns:
        Dictionary mapping provider names to success status
    """
    results = {}
    
    try:
        manager = create_llm_manager()
        test_prompt = "Hello, respond with just 'OK' if you can understand this."
        
        for provider_name in manager.get_available_providers():
            try:
                provider = manager.get_provider(provider_name)
                
                # Simple availability check
                is_available = provider.is_available()
                results[provider_name] = is_available
                
                if is_available:
                    logger.info(f"✅ {provider_name} is available")
                else:
                    logger.warning(f"⚠️ {provider_name} is not available")
                    
            except Exception as e:
                logger.error(f"❌ Error testing {provider_name}: {e}")
                results[provider_name] = False
                
    except Exception as e:
        logger.error(f"Error during provider testing: {e}")
    
    return results


def get_recommended_provider() -> Optional[str]:
    """
    Get the recommended provider based on availability and performance.
    
    Returns:
        Name of recommended provider or None if none available
    """
    provider_status = test_providers()
    
    # Priority order: Gemini (fast API) -> Ollama (local)
    priority_order = ['gemini', 'ollama']
    
    for provider in priority_order:
        if provider_status.get(provider, False):
            logger.info(f"🎯 Recommended provider: {provider}")
            return provider
    
    logger.warning("⚠️ No providers available")
    return None


def print_provider_info():
    """Print detailed information about all providers."""
    print("\n🤖 LLM Provider Information")
    print("=" * 50)
    
    status = get_provider_status()
    
    for provider_name, info in status.items():
        print(f"\n📋 {provider_name.upper()}")
        print(f"   Available: {'✅' if info.get('available', False) else '❌'}")
        
        if 'info' in info:
            provider_info = info['info']
            print(f"   Model: {provider_info.get('model', 'Unknown')}")
            print(f"   Type: {provider_info.get('type', 'Unknown')}")
            
            if 'pricing' in provider_info:
                pricing = provider_info['pricing']
                print(f"   Pricing: {pricing.get('input', 'N/A')} input, {pricing.get('output', 'N/A')} output")
        
        if 'error' in info:
            print(f"   Error: {info['error']}")
    
    # Show recommendation
    recommended = get_recommended_provider()
    if recommended:
        print(f"\n🎯 Recommended: {recommended}")
    else:
        print("\n⚠️ No providers available")


if __name__ == "__main__":
    print("🚀 Testing LLM Provider Setup")
    
    # Test all providers
    results = test_providers()
    
    # Print detailed info
    print_provider_info()
    
    # Show summary
    print(f"\n📊 Summary: {sum(results.values())}/{len(results)} providers available")