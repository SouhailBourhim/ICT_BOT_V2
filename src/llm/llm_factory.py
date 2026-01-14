"""
LLM Factory for creating and managing different LLM providers.
"""
from typing import Dict, Any, Optional, List
from loguru import logger

from .base_llm import BaseLLM
from .providers.ollama_client import OllamaClient
from .providers.gemini_client import GeminiClient


class LLMFactory:
    """Factory for creating LLM clients."""
    
    PROVIDERS = {
        'ollama': OllamaClient,
        'gemini': GeminiClient,
    }
    
    @classmethod
    def create_llm(cls, provider: str, config: Dict[str, Any]) -> BaseLLM:
        """
        Create an LLM client for the specified provider.
        
        Args:
            provider: Provider name ('ollama', 'gemini', etc.)
            config: Provider-specific configuration
            
        Returns:
            Configured LLM client
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls.PROVIDERS:
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider '{provider}'. Available: {available}")
        
        provider_class = cls.PROVIDERS[provider]
        
        try:
            return provider_class(config)
        except Exception as e:
            logger.error(f"Failed to create {provider} client: {e}")
            raise
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers."""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def create_with_fallback(
        cls,
        primary_provider: str,
        primary_config: Dict[str, Any],
        fallback_provider: Optional[str] = None,
        fallback_config: Optional[Dict[str, Any]] = None
    ) -> BaseLLM:
        """
        Create LLM client with fallback support.
        
        Args:
            primary_provider: Primary provider to try
            primary_config: Primary provider config
            fallback_provider: Fallback provider (optional)
            fallback_config: Fallback provider config (optional)
            
        Returns:
            Working LLM client
        """
        # Try primary provider
        try:
            llm = cls.create_llm(primary_provider, primary_config)
            if llm.is_available():
                logger.info(f"Using primary provider: {primary_provider}")
                return llm
            else:
                logger.warning(f"Primary provider {primary_provider} not available")
        except Exception as e:
            logger.error(f"Primary provider {primary_provider} failed: {e}")
        
        # Try fallback if provided
        if fallback_provider and fallback_config:
            try:
                llm = cls.create_llm(fallback_provider, fallback_config)
                if llm.is_available():
                    logger.info(f"Using fallback provider: {fallback_provider}")
                    return llm
                else:
                    logger.warning(f"Fallback provider {fallback_provider} not available")
            except Exception as e:
                logger.error(f"Fallback provider {fallback_provider} failed: {e}")
        
        raise Exception("No working LLM provider available")


class LLMManager:
    """Manager for handling multiple LLM providers with routing."""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLM] = {}
        self.default_provider: Optional[str] = None
    
    def add_provider(self, name: str, provider: BaseLLM):
        """Add a provider to the manager."""
        self.providers[name] = provider
        if self.default_provider is None:
            self.default_provider = name
        logger.info(f"Added provider: {name}")
    
    def set_default_provider(self, name: str):
        """Set the default provider."""
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        self.default_provider = name
        logger.info(f"Default provider set to: {name}")
    
    def get_provider(self, name: Optional[str] = None) -> BaseLLM:
        """Get a provider by name or return default."""
        provider_name = name or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            available = ', '.join(self.providers.keys())
            raise ValueError(f"Provider '{provider_name}' not found. Available: {available}")
        
        return self.providers[provider_name]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())
    
    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all providers."""
        info = {}
        for name, provider in self.providers.items():
            try:
                info[name] = {
                    'available': provider.is_available(),
                    'info': provider.get_model_info()
                }
            except Exception as e:
                info[name] = {
                    'available': False,
                    'error': str(e)
                }
        return info
    
    async def generate_with_fallback(
        self,
        prompt: str,
        context: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ):
        """Generate response with automatic fallback."""
        providers_to_try = []
        
        # Add preferred provider first
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        # Add default provider if different
        if self.default_provider and self.default_provider not in providers_to_try:
            providers_to_try.append(self.default_provider)
        
        # Add all other providers
        for name in self.providers:
            if name not in providers_to_try:
                providers_to_try.append(name)
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                if provider.is_available():
                    logger.info(f"Trying provider: {provider_name}")
                    response = await provider.generate_response(
                        prompt=prompt,
                        context=context,
                        **kwargs
                    )
                    logger.success(f"Response generated with: {provider_name}")
                    return response
                else:
                    logger.warning(f"Provider {provider_name} not available")
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                last_error = e
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")